"""Compare the observed build inputs to the repository's reviewed profile."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent


class ProfileError(RuntimeError):
    def __init__(self, details, summary):
        super().__init__("\n".join([*details, "See docs/build-prerequisites.md"]))
        self.summary = ", ".join(summary)


def tool_versions():
    try:
        import tomllib
    except ImportError:  # Ubuntu with Python 3.10
        try:
            import tomli as tomllib
        except ImportError:
            raise RuntimeError("Python 3.10 needs python3-tomli to read mise.toml") from None
    with (ROOT / "mise.toml").open("rb") as stream:
        return tomllib.load(stream)["tools"]


def checked_tools(zig, problems, names=("rustc", "cargo", "cargo-deny", "zig")):
    pins = tool_versions()
    tools = {}
    for name, args, expected in [
        ("rustc", ["rustc", "--version"], pins["rust"]),
        ("cargo", ["cargo", "--version"], pins["rust"]),
        ("cargo-deny", ["cargo", "deny", "--version"], pins["cargo:cargo-deny"]),
        ("zig", [zig, "version"], pins["zig"]),
    ]:
        if name not in names:
            continue
        try:
            result = subprocess.run(args, capture_output=True, text=True, check=True)
            fields = result.stdout.strip().split()
            version = fields[0] if name == "zig" and len(fields) == 1 else (
                fields[1] if len(fields) >= 2 and fields[0] == name else "(unrecognized output)")
        except (OSError, subprocess.CalledProcessError):
            version = "(missing or failed to execute)"
        tools[name] = version
        if version != expected:
            msg = f"{name}: expected {expected}, found {version}"
            if name == "cargo-deny":
                msg += f"; install with: cargo install --locked cargo-deny --version {expected}"
            problems.append(msg)
    return tools


def differences(label, expected, actual):
    return [f"{label} {key}: expected {expected.get(key, '(absent)')}, found {actual.get(key, '(missing)')}"
            for key in sorted(expected.keys() | actual.keys()) if expected.get(key) != actual.get(key)]


def profile_path(profile, component):
    return ROOT / "build-profiles" / f"{profile['platform']}-{component}.json"


def audit_prerequisites():
    """The advisory check depends only on cargo-deny, not on the Ubuntu build baseline."""
    problems = []
    checked_tools(None, problems, names=("cargo-deny",))
    if problems:
        raise ProfileError(problems, ["advisory tool mismatch"])


def observe(component, zig):
    """Collect the build inputs; return (profile or None, problems)."""
    problems = []
    tools = checked_tools(zig, problems)
    native = ["bash", "git", "tar", "cc", "c++", "ld", "ar", "make"]
    if component == "app":
        native += ["clang", "pkg-config"]
    for name in native:
        selected = shutil.which(name)
        packaged = Path("/usr/bin") / name
        if not selected or not packaged.is_file() or not packaged.samefile(selected):
            problems.append(f"{name}: expected Ubuntu {packaged}, found {selected or '(missing)'}")
    python = Path("/usr/bin/python3")
    if not python.is_file() or not python.samefile(sys._base_executable):
        problems.append("Use /usr/bin/python3 or a .venv created with it for the Ubuntu build profile")
    result = subprocess.run([str(python), "-I", str(ROOT / "scripts/ubuntu_packages.py"), component],
                            capture_output=True, text=True) if python.is_file() else None
    if result is None or result.returncode:
        problems.append(result.stderr.strip() if result else "Missing Ubuntu /usr/bin/python3")
        return None, problems
    report = json.loads(result.stdout)
    problems.extend(report.pop("problems"))
    return {"component": component, "tools": tools, **report}, problems


def review_profile(component, zig, candidate=False):
    """Return the observed profile; raise ProfileError when the build must not proceed.

    A candidate for a new baseline is not compared with the reviewed one; security review of
    package updates happens outside this script before a candidate is adopted.
    """
    profile, problems = observe(component, zig)
    missing_profile = None
    if profile is not None and not candidate:
        path = profile_path(profile, component)
        if path.is_file():
            expected = json.loads(path.read_text())
            if expected["component"] != component or expected["platform"] != profile["platform"]:
                problems.append(f"Incorrect platform or component in {path.name}")
            for key in ("tools", "packages"):
                problems.extend(differences(key, expected[key], profile[key]))
        else:
            missing_profile = path.name
    if problems or missing_profile:
        details = list(problems)
        summary = []
        if missing_profile:
            details.append(f"No reviewed profile {missing_profile}; validate using --review-build before adoption")
            summary.append("reviewed profile missing")
        if problems:
            summary.append(f"prerequisite issues: {len(problems)}")
        raise ProfileError(details, summary)
    return profile


def runtime_packages(binary, packages):
    """Record the resolved ELF dependencies of our freshly built, trusted binary."""
    listing = subprocess.check_output(["/usr/bin/ldd", binary], env=dict(os.environ, LC_ALL="C"), text=True)
    runtime = {}
    for entry in listing.splitlines():
        if "not found" in entry:
            raise RuntimeError(f"Missing runtime library: {entry.strip()}")
        match = re.search(r"(?:^\s*|=> )(/\S+)\s+\(", entry)
        if not match:  # e.g. the virtual kernel DSO
            continue
        library = Path(match[1])
        # On merged-/usr systems dpkg may register either spelling.
        paths = [str(library.resolve()), str(library)]
        if paths[0].startswith("/usr/"):
            paths.append(paths[0][4:])
        for path in dict.fromkeys(paths):
            owner = subprocess.run(["dpkg-query", "-S", path], capture_output=True, text=True)
            if owner.returncode == 0:
                package = owner.stdout.split(": ", 1)[0].split(":")[0]
                if package in packages:
                    runtime[library.name] = package
                    break
        else:
            raise RuntimeError(f"No reviewed Ubuntu package owns runtime library {library}")
    if not runtime:
        raise RuntimeError(f"Could not identify runtime libraries of {binary.name}")
    return runtime
