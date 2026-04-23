import json
import logging
from pathlib import Path

LOG_PATH = "server/logs/latest.log"
OUTPUT_FILE = "cache/dumped_recipes.json"

logger = logging.getLogger(__name__)


def extract_recipes_from_log():
    logger.info("Reading log file: %s...", LOG_PATH)

    recipes = []
    capturing = False

    try:
        with open(LOG_PATH, encoding="utf-8", errors="ignore") as f:
            for line in f:
                if "AGENTSYS_RECIPE_DUMP_START" in line:
                    logger.info("Found dump start marker. Capturing...")
                    recipes = []  # Reset in case of multiple dumps
                    capturing = True
                    continue

                if "AGENTSYS_RECIPE_DUMP_END" in line:
                    logger.info("Found dump end marker.")
                    capturing = False
                    break

                if capturing and "AGENTSYS_DATA::" in line:
                    try:
                        raw_json = line.split("AGENTSYS_DATA::", 1)[1].strip()
                        recipe_obj = json.loads(raw_json)
                        recipes.append(recipe_obj)
                    except Exception as e:
                        logger.warning("Failed to parse line: %s", e)

        if recipes:
            logger.info("Successfully extracted %d recipes.", len(recipes))

            Path(OUTPUT_FILE).parent.mkdir(parents=True, exist_ok=True)
            with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
                json.dump(recipes, out, indent=2)

            logger.info("Saved to %s", OUTPUT_FILE)
        else:
            logger.warning("No recipes found. Check server log and kubejs-scripts/dump_recipes.js")

    except FileNotFoundError:
        logger.error("Could not find the log file. Is LOG_PATH correct?")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    extract_recipes_from_log()
