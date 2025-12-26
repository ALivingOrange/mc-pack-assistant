import os
import json
import zipfile
import urllib.request
from pathlib import Path
from collections import defaultdict

MCMETA_BASE_URL = "https://raw.githubusercontent.com/misode/mcmeta/registries"
CACHE_DIR = Path("cache")

def download_vanilla_registry(registry_type, version=None):
    """Download vanilla item or block registry from MCMeta repo."""
    CACHE_DIR.mkdir(exist_ok=True)
    
    # Use version-specific URL if provided, otherwise use latest
    if version:
        url = f"https://raw.githubusercontent.com/misode/mcmeta/{version}-registries/{registry_type}/data.min.json"
        cache_file = CACHE_DIR / f"{registry_type}_{version}.json"
    else:
        url = f"{MCMETA_BASE_URL}/{registry_type}/data.min.json"
        cache_file = CACHE_DIR / f"{registry_type}_latest.json"
    
    if cache_file.exists():
        print(f"Using cached {registry_type} registry from {cache_file}")
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    
    print(f"Downloading {registry_type} registry from MCMeta...")
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        
        print(f"Cached {registry_type} registry to {cache_file}")
        return data
    except Exception as e:
        print(f"Error downloading {registry_type} registry: {e}")
        return None

def get_vanilla_ids(version=None):
    """Get vanilla item and block IDs from MCMeta repo."""
    vanilla_ids = set()
    
    item_data = download_vanilla_registry("item", version)
    if item_data:
        items_list = item_data.get("values", item_data) if isinstance(item_data, dict) else item_data
        if isinstance(items_list, list):
            vanilla_ids.update(f"minecraft:{item}" for item in items_list)
            print(f"  Loaded {len(items_list)} vanilla items")
    
    block_data = download_vanilla_registry("block", version)
    if block_data:
        # Handle both dict with "values" key and direct list
        blocks_list = block_data.get("values", block_data) if isinstance(block_data, dict) else block_data
        if isinstance(blocks_list, list):
            blocks_before = len(vanilla_ids)

            vanilla_ids.update(f"minecraft:{block}" for block in blocks_list)
            new_blocks = len(vanilla_ids) - blocks_before
            print(f"  Loaded {len(blocks_list)} vanilla blocks ({new_blocks} unique)")
    
    return vanilla_ids

def extract_ids_from_jar(jar_path):
    """Extract item and block IDs from a single JAR file."""
    items = set()
    blocks = set()
    
    try:
        with zipfile.ZipFile(jar_path, 'r') as jar:
            file_list = jar.namelist()
            
            # Find the mod ID from the assets directory
            mod_ids = set()
            for file in file_list:
                if file.startswith('assets/') and '/' in file[7:]:
                    parts = file.split('/')
                    if len(parts) >= 2:
                        mod_ids.add(parts[1])
            
            # For each mod ID, look for model files
            for mod_id in mod_ids:
                item_path_prefix = f'assets/{mod_id}/models/item/'
                for file in file_list:
                    if file.startswith(item_path_prefix) and file.endswith('.json'):
                        item_name = file[len(item_path_prefix):-5]  # Remove path and .json
                        items.add(f'{mod_id}:{item_name}')
                
                block_path_prefix = f'assets/{mod_id}/models/block/'
                for file in file_list:
                    if file.startswith(block_path_prefix) and file.endswith('.json'):
                        block_name = file[len(block_path_prefix):-5]  # Remove path and .json
                        blocks.add(f'{mod_id}:{block_name}')
    
    except Exception as e:
        print(f"Error processing {jar_path}: {e}")
    
    return items, blocks

def scan_modpack_directory(modpack_path):
    """Scan a modpack directory for all JAR files and extract IDs."""
    modpack_path = Path(modpack_path)
    mods_dir = modpack_path / 'mods'
    
    if not mods_dir.exists():
        print(f"Mods directory not found at {mods_dir}")
        return {}, {}
    
    all_items = defaultdict(set)
    all_blocks = defaultdict(set)
    
    jar_files = list(mods_dir.glob('*.jar'))
    
    print(f"Found {len(jar_files)} JAR files in mods directory. Processing...")
    
    for i, jar_file in enumerate(jar_files, 1):
        print(f"[{i}/{len(jar_files)}] Processing {jar_file.name}...")
        items, blocks = extract_ids_from_jar(jar_file)
        
        if items or blocks:
            all_items[jar_file.name].update(items)
            all_blocks[jar_file.name].update(blocks)
    
    return all_items, all_blocks

def save_results(items, blocks, vanilla_ids, output_file='item_ids.txt'):
    """Save extracted IDs to a text file."""
    with open(output_file, 'w', encoding='utf-8') as f:
        # Collect all unique items and blocks from mods
        all_mod_ids = set()
        
        for jar_name, item_set in items.items():
            all_mod_ids.update(item_set)
        
        for jar_name, block_set in blocks.items():
            all_mod_ids.update(block_set)
        
        all_ids = sorted(all_mod_ids | vanilla_ids)
        
        for item_id in all_ids:
            f.write(f"{item_id}\n")
    
    print(f"\nBreakdown:")
    print(f"  Unique mod items/blocks: {len(all_mod_ids)}")
    print(f"  Unique vanilla items/blocks: {len(vanilla_ids)}")
    print(f"  Total unique IDs (after deduplication): {len(all_ids)}")

def main():
    print("Minecraft Modpack Item ID Extractor")
    print("=" * 60)
    
    """
    # Get Minecraft version from user for vanilla items
    version = input("Enter Minecraft version (e.g., 1.20.1) or press Enter for latest: ").strip()
    if not version:
        version = None
    """
    
    # For now just assume version is 1.20.1
    version = "1.20.1"
    
    print("\nFetching vanilla items and blocks...")
    vanilla_ids = get_vanilla_ids(version)
    print(f"Total unique vanilla items/blocks: {len(vanilla_ids)}")
    
    modpack_path = Path('server')
    
    if not os.path.exists(modpack_path):
        print(f"Error: Directory '{modpack_path}' not found!")
        return
    
    print("\nScanning modpack...")
    items, blocks = scan_modpack_directory(modpack_path)
    
    output_file = CACHE_DIR / 'modpack_item_ids.txt'
    save_results(items, blocks, vanilla_ids, output_file)
    
    print(f"\nDone! Results saved to '{output_file}'")

if __name__ == '__main__':
    main()
