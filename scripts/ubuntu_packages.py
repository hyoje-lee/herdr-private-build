"""Inspect the native Ubuntu build packages using the distribution's python3-apt."""
import json
import platform
import sys


COMMON = ("bash", "binutils", "build-essential", "git", "python3", "python3-apt", "tar")
APP = ("clang", "libclang-dev", "pkg-config", "libxcb1-dev", "libxkbcommon-dev",
       "libxkbcommon-x11-dev", "libwayland-dev", "libvulkan-dev", "mesa-vulkan-drivers",
       "libfontconfig-dev", "libfreetype-dev")


def inspect(component):
    import apt
    import apt_pkg

    release = platform.freedesktop_os_release()
    if release.get("ID") != "ubuntu":
        raise ValueError("Ubuntu package review is required for this release")
    cache = apt.Cache()
    arch = apt_pkg.config.find("APT::Architecture")

    roots = COMMON + (APP if component == "app" else ())
    packages = {}
    problems = []
    pending = list(roots)
    while pending:
        name = pending.pop()
        if name in packages:
            continue
        pkg = cache.get(name)
        if pkg is None or not pkg.is_installed:
            problems.append(f"Missing Ubuntu package: {name}")
            continue
        current = pkg.installed
        packages[name] = current.version
        for dependency in current.get_dependencies("PreDepends", "Depends"):
            targets = dependency.installed_target_versions
            if not targets:
                problems.append(f"{name}: unsatisfied {dependency}")
                continue
            # Debian alternatives are ordered by preference. Do not require unrelated
            # installed providers merely because they could also satisfy the dependency.
            pending.append(targets[0].package.name)
    return {"platform": f'ubuntu-{release["VERSION_ID"]}-{arch}', "packages": packages,
            "problems": sorted(set(problems))}


if __name__ == "__main__":
    try:
        print(json.dumps(inspect(sys.argv[1]), sort_keys=True))
    except ImportError:
        sys.exit("Install Ubuntu python3-apt for /usr/bin/python3; see docs/build-prerequisites.md")
    except (ValueError, OSError, KeyError) as error:
        sys.exit(str(error))
