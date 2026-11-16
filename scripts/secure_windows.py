"""Windows-only side effects of the installer, following upstream's Windows installers.

secure_build.py keeps the shared flow (pins, patch, audit, build, policy tests, backup and rollback)
and calls these only when running on Windows. winreg and ctypes.windll are imported inside the
functions that need them, so this module imports cleanly on Linux and tests can replace them.
"""
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

# Microsoft's ConPTY that upstream ships beside herdr-core.exe; fetch-conpty.ps1 pins and checks it.
CONPTY_FILES = ("conpty/conpty.dll", "conpty/x64/OpenConsole.exe")


def run(args, **kwargs):
    return subprocess.run([str(a) for a in args], check=True, **kwargs)


def system_tar():
    # Windows' own tar opens what Git Bash's (often first on PATH there) cannot, as upstream notes.
    return Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "tar.exe"


def program_files_x86():
    return Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))


def prerequisites(component, output):
    """MSVC, LLVM and the Windows SDK live outside PATH on Windows, so look where upstream CI finds them."""
    problems = []
    if not system_tar().is_file():
        problems.append(f"Missing tool: {system_tar()} (Windows 10 1803 or newer)")
    if shutil.which("rustc") and "host: x86_64-pc-windows-msvc" not in output(["rustc", "-vV"]):
        problems.append("Rust host toolchain must be x86_64-pc-windows-msvc")
    vswhere = program_files_x86() / "Microsoft Visual Studio/Installer/vswhere.exe"
    msvc = vswhere.is_file() and subprocess.run(
        [str(vswhere), "-latest", "-products", "*", "-requires", "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
         "-property", "installationPath"], capture_output=True, text=True).stdout.strip()
    if not msvc:
        problems.append("Missing Visual Studio C++ build tools (MSVC x64)")
    if component == "app":
        clang_dirs = [os.environ.get("LIBCLANG_PATH"), r"C:\Program Files\LLVM\bin"]
        if not any((Path(d) / "libclang.dll").is_file() for d in clang_dirs if d):
            problems.append("Missing libclang.dll (install LLVM or set LIBCLANG_PATH)")
        fxc = os.environ.get("GPUI_FXC_PATH")
        found = Path(fxc).is_file() if fxc else (shutil.which("fxc.exe") or
                                                 any((program_files_x86() / "Windows Kits/10/bin").glob("*/x64/fxc.exe")))
        if not found:
            problems.append("Missing fxc.exe (install the Windows SDK or set GPUI_FXC_PATH)")
    return problems


def fetch_conpty(work, offline):
    script = work / "herdr-core/scripts/fetch-conpty.ps1"
    if offline:
        # The script reuses its download from the temp folder (checking its SHA-256 again); without one it would go online.
        version = re.search(r'^\$version = "([^"]+)"', script.read_text(), re.MULTILINE)
        cache = Path(tempfile.gettempdir()) / f"hc-conpty-{version.group(1) if version else '?'}.zip"
        if not cache.is_file():
            raise RuntimeError(f"--offline needs the ConPTY download cached at {cache}")
    run(["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", script,
         "-Dest", work / "target/release"])
    missing = [path for path in CONPTY_FILES if not (work / "target/release" / path).is_file()]
    if missing:
        raise RuntimeError(f"ConPTY fetch left no {', '.join(missing)}")


def start_menu():
    return Path(os.environ["APPDATA"]) / "Microsoft/Windows/Start Menu/Programs"


def create_shortcut(link, target):
    # Paths travel in the environment, so no quoting reaches PowerShell's parser.
    script = ("$s = (New-Object -ComObject WScript.Shell).CreateShortcut($env:HERDR_LINK); $s.TargetPath = $env:HERDR_TARGET; "
              "$s.WorkingDirectory = $env:USERPROFILE; $s.Description = 'Herdr built from pinned sources'; $s.Save()")
    run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
        env=dict(os.environ, HERDR_LINK=str(link), HERDR_TARGET=str(target)))


def notify_environment_change():
    # WM_SETTINGCHANGE "Environment": new terminals and Explorer pick up the PATH change.
    import ctypes
    ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001A, 0, "Environment", 0x0002, 5000, None)


def add_to_user_path(directory):
    """Append directory to the user's PATH as upstream's installer does; return the previous value, or None if unchanged."""
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_READ | winreg.KEY_SET_VALUE) as key:
        try:
            raw, kind = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            raw, kind = None, winreg.REG_EXPAND_SZ
        wanted = str(directory).rstrip("\\").lower()
        if any(entry.strip().rstrip("\\").lower() == wanted for entry in (raw or "").split(";")):
            return None
        winreg.SetValueEx(key, "Path", 0, kind, f"{raw.rstrip(';')};{directory}" if raw else str(directory))
    notify_environment_change()
    return {"value": raw, "type": kind}


def restore_user_path(previous):
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE) as key:
        if previous["value"] is None:
            winreg.DeleteValue(key, "Path")
        else:
            winreg.SetValueEx(key, "Path", 0, previous["type"], previous["value"])
    notify_environment_change()
