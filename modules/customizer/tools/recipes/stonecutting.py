from ..script_writer import append_to_script
from ..validation import validate_item_id


def add_stonecutting_recipe(comment: str, ingredient: str, result: str, count: int) -> dict:
    """Writes to a KubeJS script to create a stonecutting recipe with the given items.

    Args:
        comment: A string describing the recipe in natural language. Will be added
        to the script as a comment. Try to describe what mod each item is from.
        Ex: "Cut planks into sticks on the stonecutter."

        ingredient: Item identifier of the input item as a string.
        Ex: "minecraft:stone"

        result: Item identifier of result as a string.
        Ex: "minecraft:stone_bricks"

        count: Amount of result produced. Ex: 3
    """

    for item_id in [ingredient, result]:
        if not validate_item_id(item_id):
            return {"status": "error", "error_message": f"Invalid item ID: {item_id}"}

    result_str = f"'{count}x {result}'" if count > 1 else f"'{result}'"

    block = [
        f"\n\n// {comment}\n",
        f"event.stonecutting({result_str}, '{ingredient}')\n",
    ]

    return append_to_script(block)
