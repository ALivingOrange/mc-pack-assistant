import logging
import os
from pathlib import Path

from google.genai import types

logger = logging.getLogger(__name__)

MODEL_NAME = "gemini-2.5-flash"

_REPO_ROOT = Path(__file__).parent.parent.parent

ITEM_IDS_PATH = _REPO_ROOT / "cache" / "modpack_item_ids.txt"
RECIPE_LIST_PATH = _REPO_ROOT / "cache" / "dumped_recipes.json"
OUTPUT_PATH: Path = _REPO_ROOT / "server" / "kubejs" / "server_scripts" / "test.js"
API_KEY_PATH = _REPO_ROOT / "cache" / ".api_key"


def load_api_key() -> str | None:
    """Resolve the Google API key.

    Precedence: GOOGLE_API_KEY env var > cache/.api_key > None.
    Sets os.environ["GOOGLE_API_KEY"] as a side effect when read from disk
    so downstream google-genai clients pick it up.
    """
    key = os.environ.get("GOOGLE_API_KEY")
    if key:
        return key
    try:
        key = API_KEY_PATH.read_text().strip()
    except OSError:
        logger.warning(
            "GOOGLE_API_KEY not set and %s not readable; agent calls will fail until "
            "one is provided.",
            API_KEY_PATH,
        )
        return None
    if key:
        os.environ["GOOGLE_API_KEY"] = key
    return key or None


retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)
