import os
import json
import zipfile
from pathlib import Path
from collections import defaultdict

def extract_ids_from_jar(jar_path):
    """Extract item and block IDs from a single JAR file."""
    items = set()
    blocks = set()
    
    try:
        with zipfile.ZipFile(jar_path, 'r') as jar:
            # Get list of all files in the JAR
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
                # Check item models
                item_path_prefix = f'assets/{mod_id}/models/item/'
                for file in file_list:
                    if file.startswith(item_path_prefix) and file.endswith('.json'):
                        item_name = file[len(item_path_prefix):-5]  # Remove path and .json
                        items.add(f'{mod_id}:{item_name}')
                
                # Check block models
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
    
    # Find all JAR files
    jar_files = list(mods_dir.glob('*.jar'))
    
    print(f"Found {len(jar_files)} JAR files. Processing...")
    
    for i, jar_file in enumerate(jar_files, 1):
        print(f"[{i}/{len(jar_files)}] Processing {jar_file.name}...")
        items, blocks = extract_ids_from_jar(jar_file)
        
        if items or blocks:
            all_items[jar_file.name].update(items)
            all_blocks[jar_file.name].update(blocks)
    
    return all_items, all_blocks

def save_results(items, blocks, output_file='item_ids.txt'):
    """Save extracted IDs to a text file."""
    with open(output_file, 'w', encoding='utf-8') as f:
        # Collect all unique items and blocks
        all_items_set = set()
        all_blocks_set = set()
        
        for jar_name, item_set in items.items():
            all_items_set.update(item_set)
        
        for jar_name, block_set in blocks.items():
            all_blocks_set.update(block_set)
        
        # Combine and sort all IDs
        all_ids = sorted(all_items_set | all_blocks_set)
        
        # Write just the IDs, one per line
        for item_id in all_ids:
            f.write(f"{item_id}\n")

def main():
    print("Minecraft Modpack Item ID Extractor")
    print("=" * 60)
    
    # Use server/mods directory from working directory
    modpack_path = Path('server')
    
    if not os.path.exists(modpack_path):
        print(f"Error: Directory '{modpack_path}' not found!")
        return
    
    # Scan the modpack
    items, blocks = scan_modpack_directory(modpack_path)
    
    # Save results
    output_file = 'modpack_item_ids.txt'
    save_results(items, blocks, output_file)
    
    print(f"\nDone! Results saved to '{output_file}'")
    
    # Print summary
    total_items = sum(len(item_set) for item_set in items.values())
    total_blocks = sum(len(block_set) for block_set in blocks.values())
    print(f"Total items found: {total_items}")
    print(f"Total blocks found: {total_blocks}")

if __name__ == '__main__':
    main()