from ..script_writer import append_to_script
from ..validation import validate_item_id, validate_shaped_recipe


def add_shaped_recipe(
    comment: str, shape: list[str], ingredients: dict, result: str, count: int
) -> dict:
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
    """

    for item_id in list(ingredients.keys()) + [result]:
        if not validate_item_id(item_id):
            return {"status": "error", "error_message": f"Invalid item ID: {item_id}"}

    validation = validate_shaped_recipe(shape, ingredients)
    if not validation["valid"]:
        return {"status": "error", "error_message": validation["error_message"]}

    block = [
        f"\n\n// {comment}\n",
        "event.shaped(\n",
        f"\tItem.of('{result}', {count}),\n",
        "\t[\n",
    ]
    shape_lines = [f"\t\t'{row}',\n" for row in shape]
    if shape_lines:
        shape_lines[-1] = shape_lines[-1][:-2] + "\n"
    block.extend(shape_lines)
    block.append("\t],\n")
    block.append("\t{\n")

    ing_lines: list[str] = []
    for key, letter in ingredients.items():
        if "|" in key:
            options = ", ".join(f"'{opt}'" for opt in key.split("|"))
            ing_lines.append(f"\t\t{letter}: [{options}],\n")
        else:
            ing_lines.append(f"\t\t{letter}: '{key}',\n")
    if ing_lines:
        ing_lines[-1] = ing_lines[-1][:-2] + "\n"
    block.extend(ing_lines)
    block.append("\t}\n")
    block.append(")\n")

    return append_to_script(block)
