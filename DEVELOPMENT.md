# Development

End-user setup lives in [README.md](README.md). This file is for working *on*
the project.

## Install dev dependencies

The project has no published `pyproject.toml` extras yet — install `ruff` and
`pytest` into the conda env created by `install.sh` / `install.ps1`:

```
./conda-env/bin/pip install ruff pytest
```

Or use a system install (`pipx install ruff pytest`) — the test suite has no
runtime dependencies on the conda env beyond the modules under test.

## Running things

- **UI:** `python run_ui.py` (auto-relaunches under `./conda-env`'s Python).
  Serves Gradio at http://localhost:7860.
- **Pipeline CLIs:** `python -m modules.pipeline.item_id_extractor` and
  `python -m modules.pipeline.catch_recipe_dump` run the same extraction
  steps the UI buttons trigger, in-process.
- **Customizer CLI smoke test:** `python -m modules.customizer.cli`.

## Tests & lint

```
ruff check
ruff format --check
pytest -q
```

CI (`.github/workflows/ci.yml`) runs the same three commands on push and PR.

## API key

Resolution order, applied by `modules.customizer.config.load_api_key()`:

1. `GOOGLE_API_KEY` environment variable
2. `cache/.api_key` (written by the UI's "Save Key" button)
3. None — agent calls will fail with a logged warning at import time

Set the env var for headless / CI use; the UI flow is for humans.

## Where files live

- `cache/` — generated artifacts: `modpack_item_ids.txt`,
  `dumped_recipes.json`, vanilla registry mirrors, `.api_key`. Safe to delete;
  rebuilt on next run.
- `server/` — the installed Minecraft server. `server/kubejs/server_scripts/`
  is where agent output lands.
- `conda-env/`, `jre/` — installed by the install scripts; ignored by git.
- `server-mods.toml` — single source of truth for the mod list both install
  scripts download.

## Module layout

- `modules/customizer/` — agent definitions, tools, validation, RAG, config.
  `agents.py` exposes `root_agent`; `cli.py` is a small REPL-ish smoke test.
- `modules/pipeline/` — modpack-data extraction steps (item IDs, recipe dump
  parsing). Pure functions, importable from anywhere.
- `kubejs-scripts/` — JS dumped into the server install at setup time.
- `tests/` — pytest suite. `conftest.py` stubs cache files so imports don't
  blow up without a real install.
