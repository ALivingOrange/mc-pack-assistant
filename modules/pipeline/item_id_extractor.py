import json
import logging
import os
import urllib.request
import zipfile
from collections import defaultdict
from pathlib import Path

logger = logging.getLogger(__name__)

MCMETA_BASE_URL = "https://raw.githubusercontent.com/misode/mcmeta/registries"
CACHE_DIR = Path("cache")


def download_vanilla_registry(registry_type, version=None):
    """Download vanilla item or block registry from MCMeta repo."""
    CACHE_DIR.mkdir(exist_ok=True)

    if version:
        url = f"https://raw.githubusercontent.com/misode/mcmeta/{version}-registries/{registry_type}/data.min.json"
        cache_file = CACHE_DIR / f"{registry_type}_{version}.json"
    else:
        url = f"{MCMETA_BASE_URL}/{registry_type}/data.min.json"
        cache_file = CACHE_DIR / f"{registry_type}_latest.json"

    if cache_file.exists():
        logger.info("Using cached %s registry from %s", registry_type, cache_file)
        with open(cache_file, encoding="utf-8") as f:
            return json.load(f)

    logger.info("Downloading %s registry from MCMeta...", registry_type)
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode("utf-8"))

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

        logger.info("Cached %s registry to %s", registry_type, cache_file)
        return data
    except Exception as e:
        logger.error("Error downloading %s registry: %s", registry_type, e)
        return None


def get_vanilla_ids(version=None):
    """Get vanilla item and block IDs from MCMeta repo."""
    vanilla_ids = set()

    item_data = download_vanilla_registry("item", version)
    if item_data:
        items_list = (
            item_data.get("values", item_data) if isinstance(item_data, dict) else item_data
        )
        if isinstance(items_list, list):
            vanilla_ids.update(f"minecraft:{item}" for item in items_list)
            logger.info("Loaded %d vanilla items", len(items_list))

    block_data = download_vanilla_registry("block", version)
    if block_data:
        blocks_list = (
            block_data.get("values", block_data) if isinstance(block_data, dict) else block_data
        )
        if isinstance(blocks_list, list):
            blocks_before = len(vanilla_ids)
            vanilla_ids.update(f"minecraft:{block}" for block in blocks_list)
            new_blocks = len(vanilla_ids) - blocks_before
            logger.info("Loaded %d vanilla blocks (%d unique)", len(blocks_list), new_blocks)

    return vanilla_ids


def extract_ids_from_jar(jar_path):
    """Extract item and block IDs from a single JAR file."""
    items = set()
    blocks = set()

    try:
        with zipfile.ZipFile(jar_path, "r") as jar:
            file_list = jar.namelist()

            mod_ids = set()
            for file in file_list:
                if file.startswith("assets/") and "/" in file[7:]:
                    parts = file.split("/")
                    if len(parts) >= 2:
                        mod_ids.add(parts[1])

            for mod_id in mod_ids:
                item_path_prefix = f"assets/{mod_id}/models/item/"
                for file in file_list:
                    if file.startswith(item_path_prefix) and file.endswith(".json"):
                        item_name = file[len(item_path_prefix) : -5]
                        items.add(f"{mod_id}:{item_name}")

                block_path_prefix = f"assets/{mod_id}/models/block/"
                for file in file_list:
                    if file.startswith(block_path_prefix) and file.endswith(".json"):
                        block_name = file[len(block_path_prefix) : -5]
                        blocks.add(f"{mod_id}:{block_name}")

    except Exception as e:
        logger.error("Error processing %s: %s", jar_path, e)

    return items, blocks


def scan_modpack_directory(modpack_path):
    """Scan a modpack directory for all JAR files and extract IDs."""
    modpack_path = Path(modpack_path)
    mods_dir = modpack_path / "mods"

    if not mods_dir.exists():
        logger.error("Mods directory not found at %s", mods_dir)
        return {}, {}

    all_items = defaultdict(set)
    all_blocks = defaultdict(set)

    jar_files = list(mods_dir.glob("*.jar"))

    logger.info("Found %d JAR files in mods directory. Processing...", len(jar_files))

    for i, jar_file in enumerate(jar_files, 1):
        logger.info("[%d/%d] Processing %s...", i, len(jar_files), jar_file.name)
        items, blocks = extract_ids_from_jar(jar_file)

        if items or blocks:
            all_items[jar_file.name].update(items)
            all_blocks[jar_file.name].update(blocks)

    return all_items, all_blocks


def save_results(items, blocks, vanilla_ids, output_file="item_ids.txt"):
    """Save extracted IDs to a text file."""
    with open(output_file, "w", encoding="utf-8") as f:
        all_mod_ids = set()

        for _jar_name, item_set in items.items():
            all_mod_ids.update(item_set)

        for _jar_name, block_set in blocks.items():
            all_mod_ids.update(block_set)

        all_ids = sorted(all_mod_ids | vanilla_ids)

        for item_id in all_ids:
            f.write(f"{item_id}\n")

    logger.info("Breakdown:")
    logger.info("  Unique mod items/blocks: %d", len(all_mod_ids))
    logger.info("  Unique vanilla items/blocks: %d", len(vanilla_ids))
    logger.info("  Total unique IDs (after deduplication): %d", len(all_ids))
    return len(all_ids)


def extract_item_ids(version: str = "1.20.1", modpack_path: str | os.PathLike = "server") -> Path:
    """Extract vanilla + modpack item/block IDs and write them to cache.

    Returns the path to the written file. Raises FileNotFoundError if the
    modpack directory does not exist.
    """
    logger.info("Minecraft Modpack Item ID Extractor")

    logger.info("Fetching vanilla items and blocks...")
    vanilla_ids = get_vanilla_ids(version)
    logger.info("Total unique vanilla items/blocks: %d", len(vanilla_ids))

    modpack_path = Path(modpack_path)
    if not modpack_path.exists():
        raise FileNotFoundError(f"Directory '{modpack_path}' not found")

    logger.info("Scanning modpack...")
    items, blocks = scan_modpack_directory(modpack_path)

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    output_file = CACHE_DIR / "modpack_item_ids.txt"
    save_results(items, blocks, vanilla_ids, output_file)

    logger.info("Done! Results saved to '%s'", output_file)
    return output_file


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    extract_item_ids()
