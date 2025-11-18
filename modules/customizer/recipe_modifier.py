from google.genai import types

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search, AgentTool, ToolContext
from google.adk.code_executors import BuiltInCodeExecutor
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Tuple, Union
import re

import asyncio

import os
from pathlib import Path

# Load valid item IDs once at module initialization
def load_valid_item_ids(file_path: str) -> set:
    """Load item IDs from file into a set for O(1) lookup."""
    try:
        with open(file_path, 'r') as file:
            # Assuming one ID per line, strip whitespace
            return {line.strip() for line in file if line.strip()}
    except IOError as e:
        print(f"Warning: Could not load item IDs from {file_path}: {e}")
        return set()

# Load once at module level
ITEM_IDS_PATH = Path(__file__).parent.parent.parent / "modpack_item_ids.txt"
VALID_ITEM_IDS = load_valid_item_ids(ITEM_IDS_PATH)

def validate_item_id(item_id: str) -> bool:
    """Check if an item ID is valid. For now, assumes tags are correct."""
    # Handle tags (they start with #)
    if item_id.startswith('#'):
        return True
    
    # Handle item IDs with multiple options (separated by |)
    if '|' in item_id:
        return all(validate_item_id(id.strip()) for id in item_id.split('|'))
    
    return item_id in VALID_ITEM_IDS

# Load API key from file
api_key_path = Path(__file__).parent.parent.parent / ".api_key"
with open(api_key_path, 'r') as file:
    os.environ["GOOGLE_API_KEY"] = file.read().strip()

retry_config = types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
)

# ====== TOOL DEFINITIONS =====================================================


def search_item_ids(queries: List[str], top_k_per_query: int = 8) -> dict:
    """
    Search for item IDs in the pack relevant to the given queries using semantic search.
    
    Args:
        queries: List of query strings to search for.
                 Examples: 
                 - ["diamond tools"]
                 - ["diamond tools", "iron armor", "redstone components"]
        
        top_k_per_query: Number of results to return per query (default 8, max 15)
    
    Returns:
        A dict with:
        - 'queries': The list of queries searched
        - 'results': Dict mapping each query to its list of results
        - 'total_unique_items': Number of unique items found across all queries
        
    Example usage:
        search_item_ids(["diamond sword"]) 
        -> Returns top 8 items matching "diamond sword"
        
        search_item_ids(["red blocks", "blue blocks"], top_k_per_query=5)
        -> Returns top 5 items for each query
    """
    # Limit top_k to reasonable range
    top_k_per_query = max(1, min(top_k_per_query, 15))
    
    try:
        all_results = {}
        all_items = set()
        
        for query in queries:
            results = ITEM_SEARCHER.search(query, top_k=top_k_per_query)
            
            formatted_results = [
                {
                    "item_id": item_id,
                    "relevance_score": round(score, 3)
                }
                for item_id, score in results
            ]
            
            all_results[query] = formatted_results
            all_items.update(item_id for item_id, _ in results)
        
        return {
            "status": "success",
            "queries": queries,
            "results": all_results,
            "total_unique_items": len(all_items)
        }
            
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Search failed: {str(e)}"
        }


def add_shapeless_recipe(comment: str, ingredients: dict, result: str,count: int, output_path: str) -> dict:
    """Writes to a KubeJS script to create a shapeless recipe with the given items.

    Args:
        comment: A string describing the recipe in natural language. Will be added
        to the script as a comment. Try to describe what mod each item is from.
        Ex: "Mix one each of blaze powder coal/charcoal, and gunpowder (all from vanilla) to make one fire charge from vanilla."

        ingredients: A dict containing the items in the recipe. Keys should be item
        identifiers, while values should be the number to be used (as integers).
        For cases with multiple ingredient options, separate each with '|' characters.
        Note that the count must be less than or equal to nine, as that's the maximum
        amount that the grid can fit.
        Ex: {"minecraft:blaze_powder"=1, "minecraft:coal|minecraft:charcoal"=1, "minecraft:gunpowder"=1}

        result: Item identifier of result as a string
        Ex: "minecraft:fire_charge"

        count: Amount of result produced. Ex: 1

        output_path: The file path for the script to be written in.
    """

    # Validate item IDs
    for item_id in list(ingredients.keys()) + [result]:
        if not validate_item_id(item_id):
            return {"status": "error", "error_message": f"Invalid item ID: {item_id}"}

# Read output file
    try:
        with open(output_path, 'r') as file:
            lines:list[str] = file.readlines()
    except IOError as e:
        return {"status": "error", "error_message": ("Error reading file: " + str(e))}
# Remove last line (should be closing "})")        
    if lines: lines = lines[:-1]



# Add script to lines
    lines.append(f"\n\n# {comment}\n")
    lines.append("event.shapeless(\n")
    lines.append(f"\tItem.of('{result}', {count}),\n")
    lines.append("\t[\n")
    for key in ingredients:
        # Check if there are multiple ingredient options
        if '|' in key:
            ingredient_options = key.split('|')
            formatted_options = ', '.join(f"'{opt}'" for opt in ingredient_options)
            # Only specify count if >1
            if ingredients[key] == 1:
                lines.append(f"\t\t[{formatted_options}],\n")
            else:
                lines.append(f"\t\t'{ingredients[key]}x [{formatted_options}]',\n")
        else:
            # Only specify count if >1
            if ingredients[key] == 1:
                lines.append(f"\t\t'{key}',\n")
            else:
                lines.append(f"\t\t'{ingredients[key]}x {key}',\n")
    # Remove comma from last ingredient
    lines[-1] = lines[-1][:-2] + "\n"
    
    lines.append("\t]\n")
    lines.append(")\n")
    lines.append("})")

# Write back to output file
    try:
        with open(output_path, 'w') as file:
            file.writelines(lines)
    except IOError as e:
        return {"status": "error", "error_message": ("Error writing file: " + str(e))}

    return {"status": "success"}

def add_shaped_recipe(comment: str, shape: list[str], ingredients: dict, result: str, count: int, output_path: str) -> dict:
    """Writes to a KubeJS script to create a shaped recipe with the given items.

    Args:
        comment: A string describing the recipe in natural language. Will be added
        to the script as a comment. Try to describe what mod each item is from.
        Ex: "Craft a chest from vanilla using 8 planks in a square shape."

        shape: A list of strings representing the crafting grid pattern. Must be 1-3
        strings, each 1-3 characters long. Use letters A-I to represent ingredients
        and spaces for empty slots. Letters correspond to ingredients dict order
        (first ingredient = A, second = B, etc.).
        Ex: ["AAA", "A A", "AAA"] for a chest pattern

        ingredients: A dict containing the items in the recipe. Keys should be item
        identifiers, while values should be the letter (A-I) they represent in the
        shape pattern. The order matters: first item is A, second is B, etc.
        For cases with multiple ingredient options, separate each with '|' characters.
        Ex: {"minecraft:oak_planks|minecraft:birch_planks": "A"}

        result: Item identifier of result as a string
        Ex: "minecraft:chest"

        count: Amount of result produced. Ex: 1

        output_path: The file path for the script to be written in.
    """
    
    # Validate item IDs
    for item_id in list(ingredients.keys()) + [result]:
        if not validate_item_id(item_id):
            return {"status": "error", "error_message": f"Invalid item ID: {item_id}"}


    validation = validate_shaped_recipe(shape, ingredients)
    if not validation["valid"]:
        return {"status": "error", "error_message": validation["error_message"]}

    # Read output file
    try:
        with open(output_path, 'r') as file:
            lines: list[str] = file.readlines()
    except IOError as e:
        return {"status": "error", "error_message": ("Error reading file: " + str(e))}
    
    # Remove last line (should be closing "})")        
    if lines: 
        lines = lines[:-1]


    # Add script to lines
    lines.append(f"\n\n# {comment}\n")
    lines.append("event.shaped(\n")
    lines.append(f"\tItem.of('{result}', {count}),\n")
    lines.append("\t[\n")
    
    # Add shape pattern
    for row in shape:
        lines.append(f"\t\t'{row}',\n")
    # Remove comma from last row
    lines[-1] = lines[-1][:-2] + "\n"
    
    lines.append("\t],\n")
    lines.append("\t{\n")
    
    # Add ingredient mappings
    for key, letter in ingredients.items():
        # Check if there are multiple ingredient options
        if '|' in key:
            ingredient_options = key.split('|')
            formatted_options = ', '.join(f"'{opt}'" for opt in ingredient_options)
            lines.append(f"\t\t{letter}: [{formatted_options}],\n")
        else:
            lines.append(f"\t\t{letter}: '{key}',\n")
    
    # Remove comma from last ingredient
    lines[-1] = lines[-1][:-2] + "\n"
    
    lines.append("\t}\n")
    lines.append(")\n")
    lines.append("})")

    # Write back to output file
    try:
        with open(output_path, 'w') as file:
            file.writelines(lines)
    except IOError as e:
        return {"status": "error", "error_message": ("Error writing file: " + str(e))}

    return {"status": "success"}

def add_smithing_recipe(comment: str, template: str, base: str, addition: str, result: str, output_path: str) -> dict:
    """Writes to a KubeJS script to create a smithing recipe with the given items.

    Args:
        comment: A string describing the recipe in natural language. Will be added
        to the script as a comment. Try to describe what mod each item is from.
        Ex: "Upgrade iron ingot with black dye using netherite upgrade template to make netherite ingot."

        template: Item identifier of the smithing template as a string.
        Ex: "minecraft:netherite_upgrade_smithing_template"

        base: Item identifier of the base item to be upgraded as a string.
        Ex: "minecraft:iron_ingot"

        addition: Item identifier of the addition/upgrade item as a string.
        Ex: "minecraft:black_dye"

        result: Item identifier of result as a string.
        Ex: "minecraft:netherite_ingot"

        output_path: The file path for the script to be written in.
    """

    # Validate item IDs
    for item_id in [template, base, addition, result]:
        if not validate_item_id(item_id):
            return {"status": "error", "error_message": f"Invalid item ID: {item_id}"}    

    # Read output file
    try:
        with open(output_path, 'r') as file:
            lines: list[str] = file.readlines()
    except IOError as e:
        return {"status": "error", "error_message": ("Error reading file: " + str(e))}
    
    # Remove last line (should be closing "})")        
    if lines: 
        lines = lines[:-1]



    # Add script to lines
    lines.append(f"\n\n# {comment}\n")
    lines.append("event.smithing(\n")
    lines.append(f"\t'{result}',\n")
    lines.append(f"\t'{template}',\n")
    lines.append(f"\t'{base}',\n")
    lines.append(f"\t'{addition}'\n")
    lines.append(")\n")
    lines.append("})")

    # Write back to output file
    try:
        with open(output_path, 'w') as file:
            file.writelines(lines)
    except IOError as e:
        return {"status": "error", "error_message": ("Error writing file: " + str(e))}

    return {"status": "success"}


def add_cooking_recipe(comment: str, ingredient: str, result: str, methods: list[str], output_path: str, xp: float, cooking_time: int) -> dict:
    """Writes to a KubeJS script to create cooking recipes (smelting, blasting, smoking, campfire).

    Args:
        comment: A string describing the recipe in natural language. Will be added
        to the script as a comment. Try to describe what mod each item is from.
        Ex: "Smelt stone into gravel in furnace and blast furnace."

        ingredient: Item identifier of the input item as a string.
        For multiple ingredient options, separate each with '|' characters.
        Ex: "minecraft:stone" or "minecraft:coal|minecraft:charcoal"

        result: Item identifier of result as a string.
        Ex: "minecraft:gravel"

        methods: A list of cooking methods to use. Valid options are:
        'smelt' (furnace), 'blast' (blast furnace), 'smoke' (smoker), 'fire' (campfire)
        Ex: ["smelt", "blast"]
        Unless otherwise specified, recipes to cook food should usually include:
        smelt, smoke, fire
        While methods for smelting ore should be
        smelt, blast

        xp: Optional XP gained from the recipe as a float. Ex: 0.35

        cooking_time: Optional cooking time in ticks as an int. Default is 200.
        Value given will be used for smelting; it will be halved in smoker/blast furnace and tripled for campfire.

        output_path: The file path for the script to be written in.
    """
    # Validate item IDs
    for item_id in [ingredient, result]:
        if not validate_item_id(item_id):
            return {"status": "error", "error_message": f"Invalid item ID: {item_id}"}

    # Validate methods
    valid_methods = {'smelt', 'blast', 'smoke', 'fire'}
    if not isinstance(methods, list) or len(methods) == 0:
        return {"status": "error", "error_message": "Methods must be a non-empty list"}
    
    for method in methods:
        if method not in valid_methods:
            return {"status": "error", "error_message": f"Invalid method '{method}'. Must be one of: {valid_methods}"}
    
    # Read output file
    try:
        with open(output_path, 'r') as file:
            lines: list[str] = file.readlines()
    except IOError as e:
        return {"status": "error", "error_message": ("Error reading file: " + str(e))}
    
    # Remove last line (should be closing "})")        
    if lines: 
        lines = lines[:-1]


    # Map method names to KubeJS function names
    method_map = {
        'smelt': 'smelting',
        'blast': 'blasting',
        'smoke': 'smoking',
        'fire': 'campfireCooking'
    }

    lines.append(f"\n\n# {comment}\n")
    # Add script to lines for each method
    for method in methods:
        if '|' in ingredient:
            ingredient_options = ingredient.split('|')
            formatted_options = ', '.join(f"'{opt}'" for opt in ingredient_options)
            ingredient_str = f"[{formatted_options}]"
        else:
            ingredient_str = f"'{ingredient}'"
        
        # Calculate time factor based on method
        time_factor = 1.0
        if method in ['blast', 'smoke']:
            time_factor = 0.5
        elif method == 'fire':
            time_factor = 3.0
        
        # Use method chaining approach
        lines.append(f"event.{method_map[method]}('{result}', {ingredient_str})")
        
        lines.append(f".xp({xp})")
        lines.append(f".cookingTime({int(cooking_time * time_factor)})")
        lines.append("\n")
    
    lines.append("})")

    # Write back to output file
    try:
        with open(output_path, 'w') as file:
            file.writelines(lines)
    except IOError as e:
        return {"status": "error", "error_message": ("Error writing file: " + str(e))}

    return {"status": "success"}

def add_stonecutting_recipe(comment: str, ingredient: str, result: str, count: int, output_path: str) -> dict:
    """Writes to a KubeJS script to create a stonecutting recipe with the given items.

    Args:
        comment: A string describing the recipe in natural language. Will be added
        to the script as a comment. Try to describe what mod each item is from.
        Ex: "Cut planks into sticks on the stonecutter."

        ingredient: Item identifier or tag of the input item as a string.
        Tags should be prefixed with '#'. Ex: "#minecraft:planks" or "minecraft:stone"

        result: Item identifier of result as a string.
        Ex: "minecraft:stick"

        count: Amount of result produced. Ex: 3

        output_path: The file path for the script to be written in.
    """
    # Validate item IDs
    for item_id in [ingredient, result]:
        if not validate_item_id(item_id):
            return {"status": "error", "error_message": f"Invalid item ID: {item_id}"}


    # Read output file
    try:
        with open(output_path, 'r') as file:
            lines: list[str] = file.readlines()
    except IOError as e:
        return {"status": "error", "error_message": ("Error reading file: " + str(e))}
    
    # Remove last line (should be closing "})")        
    if lines: 
        lines = lines[:-1]

    # Format result with count
    if count > 1:
        result_str = f"'{count}x {result}'"
    else:
        result_str = f"'{result}'"

    # Add script to lines
    lines.append(f"\n\n# {comment}\n")
    lines.append(f"event.stonecutting({result_str}, '{ingredient}')\n")
    lines.append("})")

    # Write back to output file
    try:
        with open(output_path, 'w') as file:
            file.writelines(lines)
    except IOError as e:
        return {"status": "error", "error_message": ("Error writing file: " + str(e))}

    return {"status": "success"}

# ====== VALIDATOR HELPER FUNCTIONS ===========================================



def validate_shaped_recipe(shape: list[str], ingredients: dict) -> dict:
    """Validates the shape and ingredients for a shaped recipe.
    
    Args:
        shape: A list of strings representing the crafting grid pattern.
        ingredients: A dict mapping item identifiers to letters (A-I).
    
    Returns:
        A dict with 'valid' (bool) and 'error_message' (str) if invalid.
    """
    # Validate shape is a list
    if not isinstance(shape, list):
        return {"valid": False, "error_message": "Shape must be a list of strings"}
    
    # Validate shape has 1-3 rows
    if len(shape) < 1 or len(shape) > 3:
        return {"valid": False, "error_message": "Shape must have 1-3 rows"}
    
    # Validate each row
    for i, row in enumerate(shape):
        if not isinstance(row, str):
            return {"valid": False, "error_message": f"Row {i} must be a string"}
        
        if len(row) < 1 or len(row) > 3:
            return {"valid": False, "error_message": f"Row {i} must be 1-3 characters long"}
        
        # Check that row only contains A-I and spaces
        for char in row:
            if char not in 'ABCDEFGHI ':
                return {"valid": False, "error_message": f"Row {i} contains invalid character '{char}'. Only A-I and spaces are allowed"}
    
    # Collect all letters used in shape
    letters_in_shape = set()
    for row in shape:
        for char in row:
            if char != ' ':
                letters_in_shape.add(char)
    
    # Validate ingredients is a dict
    if not isinstance(ingredients, dict):
        return {"valid": False, "error_message": "Ingredients must be a dictionary"}
    
    # Collect all letters in ingredients
    letters_in_ingredients = set(ingredients.values())
    
    # Validate that all letters in ingredients are A-I
    for letter in letters_in_ingredients:
        if not isinstance(letter, str) or len(letter) != 1 or letter not in 'ABCDEFGHI':
            return {"valid": False, "error_message": f"Invalid ingredient letter '{letter}'. Must be A-I"}
    
    # Check for duplicate letters in ingredients
    if len(letters_in_ingredients) != len(ingredients):
        return {"valid": False, "error_message": "Duplicate letters found in ingredients. Each ingredient must map to a unique letter"}
    
    # Validate that all letters in shape have corresponding ingredients
    missing_ingredients = letters_in_shape - letters_in_ingredients
    if missing_ingredients:
        return {"valid": False, "error_message": f"Letters {missing_ingredients} used in shape but not defined in ingredients"}
    
    # Warn if there are unused ingredients (technically creates valid syntax but probably bad hygiene to let the agent get away with it)
    unused_ingredients = letters_in_ingredients - letters_in_shape
    if unused_ingredients:
        return {"valid": False, "error_message": f"Letters {unused_ingredients} defined in ingredients but not used in shape"}
    
    return {"valid": True}

# ====== RECIPE MODIFIER AGENT ================================================
recipe_modifier_agent = LlmAgent(
    name="recipe_modifier_agent",
    model=Gemini(model="gemini-2.5-flash", retry_options=retry_config),
    instruction="""You are a smart assistant to aid in the custom integration of Minecraft mods by adding custom recipes or changing or removing existing recipes.

    Your only job is manipulating recipes. The mod loader being used is Fabric.
    When given a request, first, use the search_item_ids tool to search for the item IDs most relevant to the response. Please make at most 5 queries.
    Then, take a deep breath and write a paragraph considering how to fulfill the request through the tools that you have available.
    All recipe-modification tools should receive a comment explaining what you're using them to add as their first argument.
    The output path should just be "test.txt" for now.

    If any tool returns status "error", check the error message and see if you can address it.
    """,
    tools=[search_item_ids,
           add_shapeless_recipe,
           add_shaped_recipe,
           add_smithing_recipe,
           add_cooking_recipe,
           add_stonecutting_recipe],
    )

# ====== RAG SETUP ============================================================

class ItemIDSearcher:
    """Semantic search for Minecraft item IDs using embeddings."""
    
    def __init__(self, item_ids: List[str], model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the searcher with item IDs.
        
        Args:
            item_ids: List of valid item IDs
            model_name: Name of the sentence-transformer model to use
        """
        print("Loading embedding model for item search...")
        self.model = SentenceTransformer(model_name)
        self.item_ids = list(item_ids)
        
        # Precompute embeddings for all item IDs
        # Transform IDs to be more human-readable for embedding
        self.item_texts = [self._format_item_for_embedding(item_id) 
                          for item_id in self.item_ids]
        
        print(f"Computing embeddings for {len(self.item_ids)} items...")
        self.embeddings = self.model.encode(self.item_texts, show_progress_bar=True)
        print("Item search ready!")
    
    def _format_item_for_embedding(self, item_id: str) -> str:
        """
        Convert item ID to more semantic text for better embedding.
        
        Example: 'minecraft:diamond_sword' -> 'minecraft diamond sword'
        """
        # Replace underscores and colons with spaces
        formatted = item_id.replace(':', ' ').replace('_', ' ')
        return formatted
    
    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Search for item IDs relevant to the query.
        
        Args:
            query: Natural language search query
            top_k: Number of results to return
            
        Returns:
            List of (item_id, similarity_score) tuples, sorted by relevance
        """
        # Encode the query
        query_embedding = self.model.encode([query])[0]
        
        # Compute cosine similarities
        similarities = np.dot(self.embeddings, query_embedding) / (
            np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_embedding)
        )
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        # Return item IDs with scores
        results = [(self.item_ids[idx], float(similarities[idx])) 
                   for idx in top_indices]
        
        return results

# Initialize searcher at module level
print("Initializing item ID semantic search...")
ITEM_SEARCHER = ItemIDSearcher(list(VALID_ITEM_IDS))

# ====== TEST SCRIPT ==========================================================

async def main():
    """Run an interactive terminal dialogue with the recipe modifier agent."""
    # Set up valid text file.
    if not os.path.exists("test.txt"):
        with open("test.txt", 'x') as file:
            file.write("ServerEvents.recipes(event =>{\n\n\n})")
    else:
        print("Repeat test. Make sure test.txt ends in a line with })!")
    
    print("=" * 70)
    print("MINECRAFT RECIPE MODIFIER AGENT - Interactive Test")
    print("=" * 70)
    print("\nThis agent can help you create custom Minecraft recipes.")
    print("Type 'quit' or 'exit' to end the conversation.\n")
    
    USER_ID = "default"
    
    # Initialize session and runner
    session_service = InMemorySessionService()
    runner = Runner(agent=recipe_modifier_agent, app_name="default", session_service=session_service)
    
    # Attempt to create new session or retrieve existing
    try:
        session = await session_service.create_session(app_name="default", user_id=USER_ID, session_id="default")
    except:
        session = await session_service.get_session(app_name="default", user_id=USER_ID, session_id="default")
    
    session_id = session.id
    print(f"Session started (ID: {session_id})")
    print("-" * 70)
    
    while True:
        try:
            # Get user input
            user_input = input("\nYou: ").strip()
            
            # Check for exit commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\nEnding session. Goodbye!")
                break
            
            # Skip empty inputs
            if not user_input:
                continue
            
            print("\nAgent: ", end="", flush=True)
            
            # Convert the query string to the ADK Content format
            query = types.Content(role="user", parts=[types.Part(text=user_input)])
            
            # Run the agent with streaming
            async for event in runner.run_async(user_id=USER_ID, session_id=session_id, new_message=query):
                # Check if the event contains valid content
                if event.content and event.content.parts:
                    # Filter out empty or "None" responses before printing
                    if event.content.parts[0].text != "None" and event.content.parts[0].text:
                        print(event.content.parts[0].text, end="", flush=True)
            
            print()  # Newline after response
            
        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Ending session.")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print("Continuing session...\n")
    
    print("-" * 70)
    print("Session ended.")

if __name__ == "__main__":
    asyncio.run(main())