import json
import logging
from pathlib import Path

LOG_PATH = Path("server/logs/latest.log")
OUTPUT_FILE = Path("cache/dumped_recipes.json")

logger = logging.getLogger(__name__)


def extract_recipes_from_log(log_path: Path = LOG_PATH, output_file: Path = OUTPUT_FILE) -> int:
    """Parse the server log for the recipe dump block and write it to JSON.

    Returns the number of recipes extracted. Raises FileNotFoundError if the
    log file is missing.
    """
    log_path = Path(log_path)
    output_file = Path(output_file)

    logger.info("Reading log file: %s...", log_path)

    recipes: list[dict] = []
    capturing = False

    with open(log_path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            if "AGENTSYS_RECIPE_DUMP_START" in line:
                logger.info("Found dump start marker. Capturing...")
                recipes = []
                capturing = True
                continue

            if "AGENTSYS_RECIPE_DUMP_END" in line:
                logger.info("Found dump end marker.")
                capturing = False
                break

            if capturing and "AGENTSYS_DATA::" in line:
                try:
                    raw_json = line.split("AGENTSYS_DATA::", 1)[1].strip()
                    recipes.append(json.loads(raw_json))
                except Exception as e:
                    logger.warning("Failed to parse line: %s", e)

    if not recipes:
        logger.warning("No recipes found. Check server log and kubejs-scripts/dump_recipes.js")
        return 0

    logger.info("Successfully extracted %d recipes.", len(recipes))
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as out:
        json.dump(recipes, out, indent=2)
    logger.info("Saved to %s", output_file)

    return len(recipes)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    extract_recipes_from_log()
