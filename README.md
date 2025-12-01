# Project Overview - MC Pack Assistant

## Problem Statement

There are over a hundred thousand Minecraft modpacks out there (can be seen at: modpackindex.com/modpacks), yet only very few do much more than selecting mods. Modpacks can be made much more cohesive with custom integrations such as recipes and loot tables. The success of this approach can be seen in popular packs such as Create: Above and Beyond and Gregtech: New Horizons. However, the process of making these integrations is technical and burdensome. Going through hundreds to thousands of items added by mods and figuring out ways to connect them takes a lot of effort, to say nothing of learning the datapack format or how to use KubeJS and implementing the integrations one at a time. The comparison to just adding mods, with how most launchers can bring a new mod into the pack with one or two clicks, is dire. The average packmaker would benefit greatly from a way to add tailor-made integrations just as easily as they might add new mods.

## Solution Statement

As in many places, AI agents can automate the rote work and ease the hard work here. A program can connect to information from a server installation of Minecraft to find all of the information on items, recipes, etc. From there, agents can search through that data much more naturally than even the most skilled human using JEI or another recipe directory could. With some tools to format the code correctly, an agent can use this to automatically create integrations on-request, even using small models such as Gemini 2.5 Flash Lite. Creating a truly cohesive modpack becomes the work of a few prompts rather than months of tedious info-sifting and scriptwriting.

## Architecture

This program uses a portable Conda environment for its own functions, and a portable Java Runtime Environment to install and run a Minecraft server for retrieving data from. KubeJS and all of its requirements are also installed, as the recipe modification functionality uses it.

From `data/assets/models` directories in the the Jar files in the `server/mods/` folder, a database of all item IDs in the pack is retrieved. While the server is running, a KubeJS script exports all of the default recipes in the pack. These two functionalities are part of the required setup and can be done through the UI.

### Agents

The `grounded_recipe_modifier_agent`, a `SequentialAgent` (from Google ADK), is composed of two subagents: the `searcher_agent` and the `recipe_modifier_agent`. 

The `searcher_agent` uses two tools to search the pack for item IDs, then search for information on existing recipes. It summarizes the information and provides it.

Using the results from the `searcher_agent`, the `recipe_modifier_agent` first comes up with a plan to address the query. Then, it writes KubeJS script using several tools, a different one for each recipe type, which have validation functions to make sure that the ingredients and results are real item IDs. Each tool exactly matches the KubeJS format for writing recipes.

### Tools

#### `searcher_agent`
This agent only has two tools: `search_item_ids`, which uses a semantic search to find exact item IDs in the pack relevant to the user's query. The `find_recipes` tool then uses these item IDs in an exact-match search to find all recipes that either use them as an ingredient or produce them as a result.

#### `recipe_modifier_agent`
This agent has seven tools: 
    `
    add_shapeless_recipe,
    add_shaped_recipe,
    add_smithing_recipe,
    add_cooking_recipe,
    add_stonecutting_recipe,
    remove_recipes,
    replace_recipe_items
    `
These all write KubeJS script matching syntax seen in https://kubejs.com/wiki/tutorials/recipes.

#### Validation
All of the tools which require exact item IDs, namely the recipe modifier tools and the `find_recipes` tool, call a `validate_item_id` function to verify that they're only using real item IDs, providing an error to the agent informing it that the recipe is invalid if necessary.

### Conclusion

This program provides a convenient interface for modifying the recipes in a modpack by extracting data from the modpack. Its most compelling features may be the parts used by the agents rather than the agents themselves: extracting item IDs from the pack for semantic search, dumping all recipes in the pack, it's a convenient way to process all of that data.

### Value Statement

This project is a useful tool for a small part of modpack development, but unfortunately time constraints in development (and especially the author's end-of-semester projects and exams) mean that it is only able to handle that one small part. At the very least, it's algorithmically incapable of writing incorrect KubeJS script, which can save time trying to diagnose errors from typos and the like.

I have many ideas for expansions on this project, which can be seen in the issues section of the repo. An orchestrator agent, which could be given broader goals for the pack like "Make exploration more rewarding" to plan and execute on would make it easier, as could similar customizer agents for changing other features such as ore generation, loot tables, and more. The ideal version of this project could take a disparate set set of mods and create a cohesive, enjoyable modpack with just one prompt.


# Installation & Use

Requires Miniconda, which can be installed at https://docs.conda.io/en/latest/miniconda.html.

First, clone the repository. From the repository root directory, run install.ps1 on Windows (requires Unrestricted execution policy) or install.sh on Linux x64. You will be prompted to agree to the Microsoft EULA to be able to run the server.

After the server is installed, you may add all the mods that you wish to the server/mods/ directory, as normal. There's currently no built-in compatibility checker functionality, so it's recommended to use an existing modpack. Note that you'll need to add KubeJS and its requirements to the pack for clients to be able to connect to the server.

From there, you can run the webui from the terminal with `python run_ui.py`. Run all of the parts in the setup section and restart the UI before your first run.

Then, you should be able to make requests to the agent, which will automatically write recipes to the file. Running the server after using the agent and connecting with a client will allow you to see your custom recipes. Alternatively, you can move the KubeJS script in server/kubejs/server_scripts into the kubejs/server_scripts directory in the client pack to make it work on the client.