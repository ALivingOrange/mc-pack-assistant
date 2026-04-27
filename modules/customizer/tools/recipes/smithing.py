from ...script_writer import append_to_script
from ...validation import validate_item_id


def add_smithing_recipe(comment: str, template: str, base: str, addition: str, result: str) -> dict:
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
    """

    for item_id in [template, base, addition, result]:
        if not validate_item_id(item_id):
            return {"status": "error", "error_message": f"Invalid item ID: {item_id}"}

    block = [
        f"\n\n// {comment}\n",
        "event.smithing(\n",
        f"\t'{result}',\n",
        f"\t'{template}',\n",
        f"\t'{base}',\n",
        f"\t'{addition}'\n",
        ")\n",
    ]

    return append_to_script(block)
