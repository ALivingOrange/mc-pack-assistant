from pathlib import Path

from google.genai import types

MODEL_NAME = "gemini-2.5-flash"

_REPO_ROOT = Path(__file__).parent.parent.parent

ITEM_IDS_PATH = _REPO_ROOT / "cache" / "modpack_item_ids.txt"
RECIPE_LIST_PATH = _REPO_ROOT / "cache" / "dumped_recipes.json"
OUTPUT_PATH: Path = _REPO_ROOT / "server" / "kubejs" / "server_scripts" / "test.js"

retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)
