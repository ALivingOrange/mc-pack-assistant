from ..script_writer import append_to_script
from ..validation import validate_item_id


def add_cooking_recipe(
    comment: str,
    ingredient: str,
    result: str,
    methods: list[str],
    xp: float = 0.35,
    cooking_time: int = 200,
) -> dict:
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

        cooking_time: Optional cooking time in ticks as an int. Default is 200. **Don't mess with this unless specifically requested.**
        Value given will be used for smelting; it will be halved in smoker/blast furnace and tripled for campfire.
    """

    for item_id in [ingredient, result]:
        if not validate_item_id(item_id):
            return {"status": "error", "error_message": f"Invalid item ID: {item_id}"}

    valid_methods = {"smelt", "blast", "smoke", "fire"}
    if not isinstance(methods, list) or len(methods) == 0:
        return {"status": "error", "error_message": "Methods must be a non-empty list"}

    for method in methods:
        if method not in valid_methods:
            return {
                "status": "error",
                "error_message": f"Invalid method '{method}'. Must be one of: {valid_methods}",
            }

    method_map = {
        "smelt": "smelting",
        "blast": "blasting",
        "smoke": "smoking",
        "fire": "campfireCooking",
    }

    if "|" in ingredient:
        options = ", ".join(f"'{opt}'" for opt in ingredient.split("|"))
        ingredient_str = f"[{options}]"
    else:
        ingredient_str = f"'{ingredient}'"

    block: list[str] = [f"\n\n// {comment}\n"]
    for method in methods:
        time_factor = 1.0
        if method in ("blast", "smoke"):
            time_factor = 0.5
        elif method == "fire":
            time_factor = 3.0

        block.append(f"event.{method_map[method]}('{result}', {ingredient_str})")
        block.append(f".xp({xp})")
        block.append(f".cookingTime({int(cooking_time * time_factor)})")
        block.append("\n")

    return append_to_script(block)
