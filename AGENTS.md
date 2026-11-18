# Herdr Setup Workspace

## Purpose and entry points

This repository builds Herdr (core and desktop app) from pinned upstream source instead of using official release binaries, and patches the build so Herdr itself sends nothing outward: no telemetry, feedback, update checks, update or core downloads, or direct mod network access. Traffic from programs the user runs inside Herdr (Claude Code, Codex, SSH and similar) is out of scope. The repository also keeps the Herdr configuration and mods, and records work so the setup can be reproduced on another machine. Upstream source is pinned in the `herdr-core/` and `herdr-app/` submodules; the installed runtime lives elsewhere.

- Read [README.md](README.md) and [docs/README.md](docs/README.md) first.
- Never fall back to official release binaries or the official installer, and keep every change compatible with blocking Herdr's own outbound traffic.
- Follow [docs/setup.md](docs/setup.md) for installation and reproduction, starting with its private build section. [docs/configuration.md](docs/configuration.md) applies only to official binaries.
- Follow [mods/README.md](mods/README.md) for mod management and each `mods/local/<name>/README.md` for its application procedure.
- Keep optional app themes in `themes/`, following [themes/README.md](themes/README.md); the setup procedure does not apply them.
- Before private builds, follow [docs/build-prerequisites.md](docs/build-prerequisites.md) to investigate the component's pinned build definitions and check local requirements. Use `scripts/build-install-core.sh` and `scripts/build-install-app.sh` separately; see [docs/private-build.md](docs/private-build.md) and [docs/source-audit.md](docs/source-audit.md). Never bypass revision/context checks or modify upstream submodules to make a patch pass.

## Working rules

- Keep build tool pins in [mise.toml](mise.toml) and platform-specific installation baselines in [build-profiles/](build-profiles/). A version match establishes reproducibility. Evaluate current security advisories separately and review updates with the component build and policy tests before adopting a new baseline.
- Keep user-facing documentation in Korean. Keep these instructions in English; `CLAUDE.md` imports this file.
- Keep shared documentation focused on reproducing the setup on another machine: version requirements, configuration, commands, rationale, and validation procedures. Keep procedures in their canonical documents and link instead of duplicating them.
- Maintain dated local work records in `docs/local-history/YYYY-MM-DD.md`, including relevant session references, host-specific paths, backup locations, and validation results. This directory is gitignored except for `.gitkeep`; preserve existing records when reorganizing documentation and never force-add them.
- This repository is published publicly. Never commit personal or host-specific data in files or commit messages: user and account names, home or workspace paths, email addresses other than the GitHub noreply author, hostnames, IP addresses, session or transcript IDs, local work timestamps, backup locations, contents of `docs/local-history/` or the live app config, credentials, or tokens. Use placeholders such as `~`, `<사용자명>`, or `<저장소 URL>` instead. Such details belong only in the gitignored local records.
- Before pushing, check the full history, not just the working tree, because a file removed in a later commit stays public in earlier commits. Rewriting published history requires the user's explicit approval.
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

Use `git submodule update --init --recursive` to prepare the pinned upstream source. For mod changes, run `herdr-app check <mod-folder>`, confirm that `herdr-app status` reports no `errors` and that no `keys.error` or `settings.error` file exists in the app home (the app writes these files on a load failure and removes them on success), and test affected shortcuts in the GUI. A successful initial mod load does not validate keyboard behavior. Process or socket visibility may be limited by the execution sandbox; do not infer that the app is stopped from an empty process list.

For installer changes, run `python3 -m unittest discover -s scripts -p 'test_secure_build.py'` and both component scripts with `--prepare-only`. Use `--check` for component prerequisites. Full build requirements and policy tests are in the private-build guide. For documentation changes, check links and consistency with actual files. If running Python, activate the root `.venv` first when it exists.
