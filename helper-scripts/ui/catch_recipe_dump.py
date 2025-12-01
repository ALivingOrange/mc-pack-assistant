import json
import re

# --- CONFIGURATION ---
# UPDATE THIS PATH to your Minecraft instance logs folder
LOG_PATH = "server/logs/latest.log"
OUTPUT_FILE = "cache/dumped_recipes.json"

def extract_recipes_from_log():
    print(f"Reading log file: {LOG_PATH}...")
    
    recipes = []
    capturing = False
    
    try:
        with open(LOG_PATH, "r", encoding="utf-8", errors="ignore") as f:
            # Read lines (reverse order might be faster for huge logs, but this is safer)
            for line in f:
                # Clean up the log prefix (timestamps, thread info, etc)
                # We just look for our substring anywhere in the line
                
                if "AGENTSYS_RECIPE_DUMP_START" in line:
                    print("Found dump start marker. Capturing...")
                    recipes = [] # Reset in case of multiple dumps
                    capturing = True
                    continue
                
                if "AGENTSYS_RECIPE_DUMP_END" in line:
                    print("Found dump end marker.")
                    capturing = False
                    break # We are done
                
                if capturing and "AGENTSYS_DATA::" in line:
                    # Extract the JSON part after the double colon
                    try:
                        # Split on the delimiter, take the second part
                        raw_json = line.split("AGENTSYS_DATA::", 1)[1].strip()
                        recipe_obj = json.loads(raw_json)
                        recipes.append(recipe_obj)
                    except Exception as e:
                        print(f"Failed to parse line: {e}")

        if recipes:
            print(f"Successfully extracted {len(recipes)} recipes.")
            
            # Save to the clean JSON file for RAG use
            with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
                json.dump(recipes, out, indent=2)
            
            print(f"Saved to {OUTPUT_FILE}")
        else:
            print("No recipes found. Check server log and " \
            "kubejs-scripts/dump_recipes.js")

    except FileNotFoundError:
        print("Error: Could not find the log file. Is LOG_PATH correct?")

if __name__ == "__main__":
    extract_recipes_from_log()