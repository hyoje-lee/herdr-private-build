# Herdr Setup Workspace

## Purpose and entry points

This repository manages Herdr desktop installation, configuration, and mods. Record work so the setup can be reproduced later. Upstream source is pinned in the `herdr-core/` and `herdr-app/` submodules; the installed runtime lives elsewhere.

- Read [README.md](README.md) and [docs/README.md](docs/README.md) first.
- Follow [docs/setup.md](docs/setup.md) for installation and reproduction, and [docs/configuration.md](docs/configuration.md) for telemetry and update settings.
- Follow [mods/README.md](mods/README.md) for mod management and each `mods/local/<name>/README.md` for its application procedure.
- Before private builds, follow [docs/build-prerequisites.md](docs/build-prerequisites.md) to investigate the component's pinned build definitions and check local requirements. Use `scripts/build-install-core.sh` and `scripts/build-install-app.sh` separately; see [docs/private-build.md](docs/private-build.md) and [docs/source-audit.md](docs/source-audit.md). Never bypass revision/context checks or modify upstream submodules to make a patch pass.

## Working rules

- Keep user-facing documentation in Korean. Keep these instructions in English; `CLAUDE.md` imports this file.
- Keep shared documentation focused on reproducing the setup on another machine: version requirements, configuration, commands, rationale, and validation procedures. Keep procedures in their canonical documents and link instead of duplicating them.
- Maintain dated local work records in `docs/local-history/YYYY-MM-DD.md`, including relevant session references, host-specific paths, backup locations, and validation results. This directory is gitignored except for `.gitkeep`; preserve existing records when reorganizing documentation and never force-add them.
- Keep local work details out of shared documentation. Describe compatibility limits and untested behavior without implying universal validation.
- List upstream sources in core, app, then mods order.
- Preserve existing work. Inspect both the parent repository and submodule before changing them. Propose a commit message and scope first; commit only after the user approves that proposal.
- Keep upstream code in `mods/sources/` unchanged. Put local configuration or modified copies in `mods/local/`, and pin upstream revisions through the parent repository's gitlink.
- Before applying configuration, inspect and back up the affected files. Merge JSON by section and key; preserve unrelated settings and resolve conflicting bindings before writing.
- The default live app home is `~/.config/herdr-app/`; `HERDR_APP_HOME` and `XDG_CONFIG_HOME` may override it. Documentation work alone does not call for reinstalling or changing the running app.
- Keep credentials, personal runtime state, raw terminal output, full session transcripts, and host backups out of both shared documents and local work records. Record only the evidence needed for reproduction or local follow-up.

## Useful checks

Run from the repository root:

```sh
git status --short
git submodule status
git -C mods/sources/herdr-layout-examples status --short
herdr-app --version
hc --version
herdr-app status
git diff --check
```

Use `git submodule update --init --recursive` to prepare the pinned upstream source. For mod changes, run `herdr-app check <mod-folder>`, inspect the app's `keys.error` and `settings.error`, and test affected shortcuts in the GUI. A successful initial mod load does not validate keyboard behavior. Process or socket visibility may be limited by the execution sandbox; do not infer that the app is stopped from an empty process list.

For installer changes, run `python3 -m unittest discover -s scripts -p 'test_secure_build.py'` and both component scripts with `--prepare-only`. Use `--check` for component prerequisites. Full build requirements and policy tests are in the private-build guide. For documentation changes, check links and consistency with actual files. If running Python, activate the root `.venv` first when it exists.
