# Agent notes (weed-spray)

Follow [`GROK.md`](GROK.md) for this repository. That file is the Grok Build instruction set.

Non-negotiables if you have not read it yet:

- Human confirm before every spray. Inject is not confirm.
- Do not invent PX4 params. Do not treat local `z` as AGL (SIH has no lidar).
- After Python edits: `make check` (`ruff check` + `ruff format --check` + pytest). Config: `[tool.ruff]` in `pyproject.toml`.
- Host tools: `mise.toml` (Python 3.11, uv, Node 26). Packages stay in uv/npm.
- New/changed `bot_files/`: follow `.grok/rules/bot-files.md` (`scripts/bot_files_delta.py`).
- Obsidian: follow the vault-root `Grok.md`. Problem/solution inbox is `1 - Rough Notes`.
