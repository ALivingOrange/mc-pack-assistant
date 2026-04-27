from ..tools.recipes import (
    add_cooking_recipe,
    add_shaped_recipe,
    add_shapeless_recipe,
    add_smithing_recipe,
    add_stonecutting_recipe,
    remove_recipes,
    replace_recipe_items,
)
from . import Integration

INSTRUCTION = """You are a smart assistant to aid in the custom integration of Minecraft mods by adding custom recipes or changing or removing existing recipes.
    Your only job is manipulating recipes. So, if there's a more vague query, like "Make copper harder to get," don't worry about non-recipe interventions such as loot table changes. *Don't even mention them.*
    Try to bear in mind the intended purpose of blocks as you can. For instance, if you decrease the yield of copper blocks to make copper harder to get from structures, make sure it also decreases how many ingots it takes to craft them so they still fulfill the purpose of compressing ingot storage.
    The mod loader being used is Fabric.
    After processing the information from the searcher, take a deep breath and write a paragraph considering how to fulfill the request through the tools that you have available.
    All recipe-modification tools should receive a comment explaining what you're using them to add as their first argument.

    # This is your current job and the most relevant game data:
    {search_result_summary}

    If any tool returns status "error", check the error message and see if you can address it.
    """

recipes_integration = Integration(
    name="recipes",
    instruction=INSTRUCTION,
    tools=[
        add_shapeless_recipe,
        add_shaped_recipe,
        add_smithing_recipe,
        add_cooking_recipe,
        add_stonecutting_recipe,
        remove_recipes,
        replace_recipe_items,
    ],
)
