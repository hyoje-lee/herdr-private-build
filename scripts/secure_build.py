#!/usr/bin/env python3
"""Build pinned Herdr sources with the private policy patch and install them in the usual places."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile

from build_environment import ProfileError, audit_prerequisites, differences, profile_path, review_profile, runtime_packages
from secure_policy import PINS, POLICY, apply

ROOT = Path(__file__).resolve().parent.parent


def run(args, **kwargs):
    return subprocess.run([str(a) for a in args], check=True, **kwargs)


def output(args, **kwargs):
    return subprocess.check_output([str(a) for a in args], text=True, **kwargs).strip()


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def source_pins(component):
    return {name: rev for name, rev in PINS.items() if name == f"herdr-{component}" or name.startswith(f"herdr-{component}/")}


def check_sources(component):
    # Never reset, fetch, patch, or build inside the original submodules.
    for name, revision in source_pins(component).items():
        source = ROOT / name
        if output(["git", "-C", source, "rev-parse", "HEAD"]) != revision:
            raise RuntimeError(f"Unreviewed revision: {name}; audit and update pins first")
        if output(["git", "-C", source, "status", "--porcelain", "--untracked-files=normal"]):
            raise RuntimeError(f"Source has local changes: {name}")


def prepare(work, component):
    check_sources(component)
    for name, revision in source_pins(component).items():
        target = work / name
        target.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryFile() as archive:
            run(["git", "-C", ROOT / name, "archive", revision], stdout=archive)
            archive.seek(0)
            run(["tar", "-x", "-C", target], stdin=archive)
    patch = apply(work, component)
    (work / "private.patch").write_text(patch)
    manifest = {"policy": POLICY, "component": component, "sources": source_pins(component), "patch_sha256": digest(work / "private.patch"),
                "builder_sha256": digest(__file__)}
    (work / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def zig_command():
    requested = os.environ.get("ZIG") or "zig"
    found = shutil.which(requested)
    return str(Path(found).resolve()) if found else requested


def prerequisites(component, candidate=False):
    profile = review_profile(component, zig_command(), candidate)
    problems = []
    if component == "app" and shutil.which("pkg-config"):
        for package in ("xcb", "xkbcommon", "xkbcommon-x11", "wayland-client", "vulkan", "fontconfig", "freetype2"):
            if subprocess.run(["pkg-config", "--exists", package], capture_output=True).returncode:
                problems.append("Missing app development library: " + package)
        # bindgen needs the shared libclang, not just the clang executable.
        import ctypes
        import ctypes.util
        candidates = [ctypes.util.find_library("clang")]
        candidates += [str(p) for p in Path("/usr/lib").glob("llvm-*/lib/libclang.so*")]
        if os.environ.get("LIBCLANG_PATH"):
            candidates += [str(p) for p in Path(os.environ["LIBCLANG_PATH"]).glob("libclang.so*")]
        for candidate in filter(None, candidates):
            try:
                ctypes.CDLL(candidate)
                break
            except OSError:
                continue
        else:
            problems.append("Missing loadable libclang (install libclang-dev or set LIBCLANG_PATH)")
    if problems:
        raise RuntimeError("\n" + "\n".join(problems) + "\nSee docs/build-prerequisites.md")
    return profile


def is_private(binary):
    # Official binaries do not know this flag; any other answer means "not ours".
    try:
        result = subprocess.run([str(binary), "--private-build"], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.stdout.strip() == POLICY


def require_private_core(prefix):
    # The patched app runs the herdr-core next to it, so that core must be patched too.
    core = prefix / "bin/herdr-core"
    if not core.is_file() or not is_private(core):
        raise RuntimeError("Install the patched core first with scripts/build-install-core.sh using the same --prefix")


def deny_config(component):
    return ROOT / "scripts/deny" / f"{component}.toml"


def audit(work, component, offline):
    """Check the prepared sources against RustSec advisories; return (error count, finding lines)."""
    if not shutil.which("cargo-deny"):
        raise RuntimeError("cargo-deny is not installed; see mise.toml and docs/build-prerequisites.md")
    # The advisory database is fetched from GitHub unless --offline uses the cached copy.
    network = ["--offline"] if offline else []
    result = subprocess.run(["cargo", "deny", "--color", "never", "--format", "json", *network, "--locked", "--workspace",
                             "check", "advisories", "--config", str(deny_config(component)), "--hide-inclusion-graph"],
                            cwd=work / f"herdr-{component}", capture_output=True, text=True)
    summary, findings = None, []
    for line in result.stderr.splitlines():
        try:
            item = json.loads(line)
        except ValueError:
            continue
        fields = item.get("fields", {})
        if item.get("type") == "summary":
            summary = fields.get("advisories", {})
        elif item.get("type") == "diagnostic" and fields.get("severity") in ("error", "warning"):
            advisory = fields.get("advisory") or {}
            label = " ".join(filter(None, (advisory.get("id"), advisory.get("package"))))
            if fields.get("code") == "advisory-not-detected":
                # A reviewed advisory that no longer matches: its ID is in the first label.
                label = (fields.get("labels") or [{}])[0].get("span", "") + " (remove from the reviewed list)"
            findings.append(f"{fields['severity']}[{fields.get('code')}] {label + ': ' if label else ''}{fields.get('message')}")
    errors = summary.get("errors") if isinstance(summary, dict) else None
    if type(errors) is not int or errors < 0 or (result.returncode and not errors):
        detail = result.stderr.strip()[-500:] or f"exit status {result.returncode}"
        raise RuntimeError(f"cargo-deny did not report a result: {detail}")
    return errors, findings


def require_reviewed_advisories(work, component, offline):
    """Stop unless every advisory is recorded as reviewed in scripts/deny/<component>.toml."""
    config = deny_config(component).relative_to(ROOT)
    errors, findings = audit(work, component, offline)
    if findings:
        print(f"Security advisory check for herdr-{component} ({config}):", file=sys.stderr)
        print("\n".join("  " + line for line in findings), file=sys.stderr, flush=True)
    if errors:
        raise RuntimeError(f"{errors} unreviewed security advisories in herdr-{component} (listed above). "
                           f"Review each one and record accepted ones with a reason in {config}")
    print(f"Security advisory check passed: herdr-{component} has no unreviewed advisories", flush=True)


def build(work, manifest, offline, jobs):
    component = manifest["component"]
    project = f"herdr-{component}"
    env = os.environ.copy()
    # Release flags and endpoint overrides must not influence this artifact.
    for key in ("HERDR_APP_RELEASE", "HERDR_RELEASES_URL", "HERDR_TELEMETRY_URL", "HERDR_FEEDBACK_URL",
                "RUSTFLAGS", "CARGO_ENCODED_RUSTFLAGS", "RUSTC_WRAPPER", "RUSTC_WORKSPACE_WRAPPER"):
        env.pop(key, None)
    env["CARGO_TARGET_DIR"] = str(work / "target")
    env["ZIG"] = zig_command()
    if offline:
        env["CARGO_NET_OFFLINE"] = "true"
    flags = ["--frozen" if offline else "--locked", "-j", str(jobs)]
    cwd = work / project
    run(["cargo", "build", "--release", *flags], cwd=cwd, env=env)
    # Run only the policy regressions with real-looking endpoints and a curl that records any call.
    sentinels = work / "test-bin"
    sentinels.mkdir()
    curl_used = work / "unexpected-curl"
    (sentinels / "curl").write_text('#!/bin/sh\nprintf "called\\n" >> "$HERDR_PRIVATE_CURL_SENTINEL"\nexit 99\n')
    (sentinels / "curl").chmod(0o755)
    test_env = dict(env, HERDR_TELEMETRY_URL="http://127.0.0.1:9/telemetry",
                    HERDR_FEEDBACK_URL="http://127.0.0.1:9/feedback",
                    HERDR_RELEASES_URL="http://127.0.0.1:9/releases",
                    HERDR_PRIVATE_CURL_SENTINEL=str(curl_used),
                    PATH=str(sentinels) + os.pathsep + env.get("PATH", ""))
    target = ["--lib"] if project == "herdr-core" else ["--bin", "herdr-app"]
    run(["cargo", "test", "--release", *flags, "-p", project, *target, "private_policy_"], cwd=cwd, env=test_env)
    if curl_used.exists():
        raise RuntimeError("Policy test invoked curl; refusing to install")
    binary = work / "target/release" / project
    if not is_private(binary):
        raise RuntimeError(f"Incorrect build identity: {project}")
    manifest["tools"] = {tool: output([tool, "--version"]) for tool in ("rustc", "cargo")}
    manifest["tools"].update(zig=output([env["ZIG"], "version"]), zig_path=env["ZIG"])
    manifest["binaries"] = {project: digest(binary)}
    (work / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


def desktop_entry(exe):
    if any(c in str(exe) for c in '\n\r%'):
        raise RuntimeError("Installation paths cannot contain newlines or desktop field codes (%)")
    quoted = str(exe).replace("\\", "\\\\").replace('"', '\\"').replace('`', '\\`').replace('$', '\\$')
    return ('[Desktop Entry]\nType=Application\nName=Herdr\nComment=Herdr built from pinned sources\n'
            f'Exec="{quoted}"\nIcon=herdr-app\nTerminal=false\nCategories=Development;\nStartupWMClass=herdr-app\n')


def install(work, prefix, data, component):
    project = f"herdr-{component}"
    binary = work / "target/release" / project
    bin_dir = prefix / "bin"
    # Each entry: (destination, kind, source): kind is "file" (copy), "text" or "link".
    if component == "core":
        items = [(bin_dir / "herdr-core", "file", binary), (bin_dir / "hc", "link", "herdr-core")]
    else:
        require_private_core(prefix)
        items = [(bin_dir / "herdr-app", "file", binary),
                 (data / "icons/hicolor/scalable/apps/herdr-app.svg", "file", work / "herdr-app/assets/icons/herdr-ui-icon-clean.svg"),
                 (data / "applications/herdr-app.desktop", "text", desktop_entry(bin_dir / "herdr-app"))]
    state = data / "herdr-build"
    # Provenance of the installed build; replaced and rolled back together with the binaries.
    items += [(state / component / name, "file", work / name) for name in ("manifest.json", "private.patch")]
    for path, _, _ in items:
        if path.is_dir() and not path.is_symlink():
            raise RuntimeError(f"Refusing to replace directory: {path}")

    # Back up everything first, so a failure can restore the previous state exactly.
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    backup = state / "backups" / f"{component}-{stamp}"
    backup.mkdir(parents=True)
    record = []
    for index, (path, _, _) in enumerate(items):
        saved = None
        if path.exists() or path.is_symlink():
            saved = backup / str(index)
            shutil.copy2(path, saved, follow_symlinks=False)
        record.append({"path": str(path), "backup": str(saved) if saved else None})
    (backup / "restore.json").write_text(json.dumps(record, indent=2) + "\n")

    replaced = []
    try:
        for path, kind, source in items:
            path.parent.mkdir(parents=True, exist_ok=True)
            fd, temporary = tempfile.mkstemp(prefix=".herdr-build-", dir=path.parent)
            os.close(fd)
            try:
                if kind == "link":
                    os.unlink(temporary)
                    os.symlink(source, temporary)
                elif kind == "file":
                    shutil.copyfile(source, temporary)
                    os.chmod(temporary, 0o755 if path.parent == bin_dir else 0o644)
                else:
                    Path(temporary).write_text(source)
                    os.chmod(temporary, 0o644)
                os.replace(temporary, path)
            except BaseException:
                if os.path.lexists(temporary):
                    os.unlink(temporary)
                raise
            replaced.append(path)
    except Exception as failure:
        errors = []
        for path in reversed(replaced):
            saved = next(item["backup"] for item in record if item["path"] == str(path))
            try:
                if saved:
                    restored = path.with_name(".herdr-restore-" + path.name)
                    shutil.copy2(saved, restored, follow_symlinks=False)
                    os.replace(restored, path)
                else:
                    path.unlink(missing_ok=True)
            except OSError as error:
                errors.append(f"{path}: {error}")
        if errors:
            raise RuntimeError(f"Install failed: {failure}; rollback incomplete: {errors}. Backups: {backup}") from failure
        raise

    print(f"Installed {project} into {bin_dir}\nPrevious files backed up: {backup}\n"
          "Running Herdr processes were not stopped; quit them and start Herdr again.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("component", choices=("core", "app"))
    parser.add_argument("--check", action="store_true", help="check source pins and prerequisites without building/installing")
    parser.add_argument("--prepare-only", action="store_true", help="export and patch sources, without building/installing")
    parser.add_argument("--build-only", action="store_true", help="build and test, without installing")
    parser.add_argument("--review-build", action="store_true", help="validate a candidate environment and emit its profile without installing")
    parser.add_argument("--audit", action="store_true", help="check the patched sources against RustSec advisories, without building/installing")
    parser.add_argument("--offline", action="store_true", help="use cached Cargo dependencies; Zig also needs cached packages")
    parser.add_argument("--jobs", type=int, default=min(os.cpu_count() or 1, 4))
    parser.add_argument("--prefix", type=Path, default=Path.home() / ".local")
    parser.add_argument("--data-home", type=Path, default=Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share"))))
    args = parser.parse_args()
    if platform.system() != "Linux" or platform.machine() not in ("x86_64", "aarch64"):
        parser.error("This installer supports Linux x86_64/aarch64 only")
    if args.jobs < 1:
        parser.error("--jobs must be positive")
    if args.review_build and (args.check or args.prepare_only or args.build_only or args.audit):
        parser.error("--review-build must be used on its own")
    if args.audit and (args.check or args.prepare_only or args.build_only):
        parser.error("--audit cannot be combined with --check, --prepare-only or --build-only")
    prefix = args.prefix.expanduser().absolute()
    data = args.data_home.expanduser().absolute()
    profile = None
    if args.check or not args.prepare_only:
        stage = "build prerequisites"
        try:
            if args.audit:
                stage = "advisory tool check"
                audit_prerequisites()
            else:
                profile = prerequisites(args.component, args.review_build)
            stage = "pinned source check"
            check_sources(args.component)
            if args.component == "app" and not (args.build_only or args.audit or args.review_build):
                stage = "installed private core check"
                require_private_core(prefix)
        except (RuntimeError, OSError, subprocess.CalledProcessError) as error:
            if not args.check:
                raise
            summary = error.summary if isinstance(error, ProfileError) else stage
            sys.exit(f"{error}\n\nBuild preflight [{args.component}] BLOCKED ({summary})")
        if args.check:
            print(f"Build preflight [{args.component}] PASSED")
            return
    base = ROOT / ".build/private"
    base.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="build-", dir=base))
    print(f"Build directory: {work}", flush=True)
    manifest = prepare(work, args.component)
    if args.prepare_only:
        print(f"Prepared reviewed sources and patch: {work / 'private.patch'}")
        return
    # Advisories nobody has reviewed stop the build; reviewed ones are listed in scripts/deny/.
    try:
        require_reviewed_advisories(work, args.component, args.offline)
    except RuntimeError as error:
        sys.exit(f"Nothing was built or installed: {error}")
    if args.audit:
        return
    manifest["advisory_check"] = "no unreviewed advisories"
    build(work, manifest, args.offline, args.jobs)
    # Recheck before publication in case apt or the toolchain changed during compilation.
    if prerequisites(args.component, args.review_build) != profile:
        raise RuntimeError("Build inputs changed during compilation; repeat the build")
    project = "herdr-" + args.component
    profile["runtime"] = runtime_packages(work / "target/release" / project, profile["packages"])
    if args.review_build:
        candidate = work / "candidate-profile.json"
        candidate.write_text(json.dumps(profile, sort_keys=True, indent=2) + "\n")
        print(f"Candidate passed build and policy tests. Review {candidate} before updating the repository.")
    else:
        expected = json.loads(profile_path(profile, args.component).read_text())
        changes = differences("runtime", expected["runtime"], profile["runtime"])
        if changes:
            raise RuntimeError("\n".join(changes))
    manifest["build_environment"] = profile
    (work / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    if not (args.build_only or args.review_build):
        install(work, prefix, data, args.component)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, subprocess.CalledProcessError) as error:
        sys.exit(f"Build/install failed; no fallback to upstream binaries: {error}")
