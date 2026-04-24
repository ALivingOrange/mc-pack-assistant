import json

from ..script_writer import append_to_script
from ..validation import validate_item_id


def remove_recipes(comment: str, filters: dict) -> dict:
    """Writes to a KubeJS script to remove recipes based on specific filters.

    Args:
        comment: A description of the removal.

        filters: A dictionary of conditions. The recipe must match ALL conditions
        to be removed. Common keys:
        - 'output': Item ID of the result (ex: "minecraft:stone")
        - 'input': Item ID of an ingredient (ex: "minecraft:cobblestone")
        - 'mod': Mod ID (ex: "thermal")
        - 'id': Specific recipe ID (ex: "minecraft:chest")
    """
    if not filters:
        return {"status": "error", "error_message": "Filters dictionary cannot be empty."}

    if "output" in filters and not validate_item_id(filters["output"]):
        return {
            "status": "error",
            "error_message": f"Invalid output item ID: {filters['output']}",
        }
    if "input" in filters and not validate_item_id(filters["input"]):
        return {
            "status": "error",
            "error_message": f"Invalid input item ID: {filters['input']}",
        }

    block = [
        f"\n\n// {comment}\n",
        f"event.remove({json.dumps(filters)})\n",
    ]

    return append_to_script(block)


def replace_recipe_items(
    comment: str, type: str, to_replace: str, replace_with: str, filter_criteria: dict
) -> dict:
    """Writes to a KubeJS script to bulk-replace inputs or outputs in recipes.

    Args:
        comment: A description of the change.

        type: Must be either "input" or "output". Determines whether to use
        event.replaceInput() or event.replaceOutput().

        to_replace: The item ID to be replaced.
        Ex: "minecraft:stick"

        replace_with: The item ID to use as the replacement.
        Ex: "minecraft:bone"

        filter_criteria: Optional dictionary to limit scope. To replace globally, use an empty dict.
        Keys can be 'mod', 'id', 'input', 'output'.
        Ex: {"mod": "minecraft"} to only replace items in Minecraft recipes.
    """
    if type not in ["input", "output"]:
        return {"status": "error", "error_message": "Type must be 'input' or 'output'"}

    for item_id in [to_replace, replace_with]:
        if not validate_item_id(item_id):
            return {"status": "error", "error_message": f"Invalid item ID: {item_id}"}

    func_name = "replaceInput" if type == "input" else "replaceOutput"
    filter_str = json.dumps(filter_criteria)

    block = [
        f"\n\n// {comment}\n",
        f"event.{func_name}(\n",
        f"\t{filter_str},\n",
        f"\t'{to_replace}',\n",
        f"\t'{replace_with}'\n",
        ")\n",
    ]

    return append_to_script(block)
