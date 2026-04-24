from ..script_writer import append_to_script
from ..validation import validate_item_id


def add_shapeless_recipe(comment: str, ingredients: dict, result: str, count: int) -> dict:
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
    """

    for item_id in list(ingredients.keys()) + [result]:
        if not validate_item_id(item_id):
            return {"status": "error", "error_message": f"Invalid item ID: {item_id}"}

    block = [
        f"\n\n// {comment}\n",
        "event.shapeless(\n",
        f"\tItem.of('{result}', {count}),\n",
        "\t[\n",
    ]
    ing_lines: list[str] = []
    for key, amount in ingredients.items():
        if "|" in key:
            options = ", ".join(f"'{opt}'" for opt in key.split("|"))
            if amount == 1:
                ing_lines.append(f"\t\t[{options}],\n")
            else:
                ing_lines.append(f"\t\t'{amount}x [{options}]',\n")
        else:
            if amount == 1:
                ing_lines.append(f"\t\t'{key}',\n")
            else:
                ing_lines.append(f"\t\t'{amount}x {key}',\n")
    if ing_lines:
        ing_lines[-1] = ing_lines[-1][:-2] + "\n"
    block.extend(ing_lines)
    block.append("\t]\n")
    block.append(")\n")

    return append_to_script(block)
