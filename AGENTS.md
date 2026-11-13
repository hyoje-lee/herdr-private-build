# Herdr Setup Workspace

## Purpose and entry points

This repository manages Herdr desktop installation, configuration, and mods. Record work so the setup can be reproduced later; the application source and installed runtime live elsewhere.

- Read [README.md](README.md) and [docs/README.md](docs/README.md) first.
- Follow [docs/setup.md](docs/setup.md) for installation and reproduction, and [docs/configuration.md](docs/configuration.md) for telemetry and update settings.
- Follow [mods/README.md](mods/README.md) for mod management and each `mods/local/<name>/README.md` for its application procedure.

## Working rules

- Keep user-facing documentation in Korean. Keep these instructions in English; `CLAUDE.md` imports this file.
- Keep procedures in their canonical documents and dated evidence in `docs/history/YYYY-MM-DD.md`. Link to existing detail instead of duplicating it.
- Record versions, source revisions, affected paths, reasons, reproduction steps, validation results, and remaining gaps together. Distinguish historical evidence, current checks, and untested behavior.
- Preserve existing work. Inspect both the parent repository and submodule before changing them. Propose a commit message and scope first; commit only after the user approves that proposal.
- Keep upstream code in `mods/sources/` unchanged. Put local configuration or modified copies in `mods/local/`, and pin upstream revisions through the parent repository's gitlink.
- Before applying configuration, inspect and back up the affected files. Merge JSON by section and key; preserve unrelated settings and resolve conflicting bindings before writing.
- The default live app home is `~/.config/herdr-app/`; `HERDR_APP_HOME` and `XDG_CONFIG_HOME` may override it. Documentation work alone does not call for reinstalling or changing the running app.
- Keep credentials, personal runtime state, terminal output, full session transcripts, and host backups out of the repository. Record only the evidence needed to reproduce the setup.

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

There is no repository-wide build or test suite. For documentation changes, check links and consistency with actual files. If running Python, activate the root `.venv` first when it exists.
