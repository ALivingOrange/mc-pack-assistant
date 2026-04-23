import json
import logging

from .config import ITEM_IDS_PATH, RECIPE_LIST_PATH

logger = logging.getLogger(__name__)


def load_valid_item_ids(file_path) -> set:
    """Load item IDs from file into a set for O(1) lookup."""
    try:
        with open(file_path) as file:
            return {line.strip() for line in file if line.strip()}
    except OSError as e:
        logger.warning("Could not load item IDs from %s: %s", file_path, e)
        return set()


def load_recipe_list(file_path) -> list[dict]:
    """Load recipe list into a list."""
    try:
        with open(file_path) as file:
            return json.load(file)
    except OSError as e:
        logger.warning("Could not load recipes from %s: %s", file_path, e)
        return []


VALID_ITEM_IDS: set[str] = load_valid_item_ids(ITEM_IDS_PATH)
ALL_RECIPES: list[dict] = load_recipe_list(RECIPE_LIST_PATH)
