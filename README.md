# Project Overview - MC Pack Assistant

## Problem Statement

There are over a hundred thousand Minecraft modpacks out there (visible at [this modpack index](https://modpackindex.com)), yet only very few do much more than selecting mods. Modpacks can be made much more cohesive with custom integrations such as recipes and loot tables. The success of this approach can be seen in popular packs such as Create: Above and Beyond and Gregtech: New Horizons, in which all the tools, machines, and recipes of the pack are revised in order to center around a customized progression path that allows them all to fit together. However, the process of making these integrations is technical and burdensome. Going through hundreds to thousands of items added by mods and figuring out ways to connect them takes a lot of effort, to say nothing of learning the datapack format or how to use KubeJS and implementing the integrations one at a time. By comparison, in most launchers, adding a new mod into the pack is done with just one or two clicks. The average packmaker would benefit greatly from a way to add tailor-made integrations just as easily as they might add new mods.

## Solution Statement

As in many places, AI agents can automate the rote work and ease the hard work here. A program can connect to information from a server installation of Minecraft to find all of the information on items, recipes, etc. From there, agents can search through that data much more naturally than even the most skilled human using JEI or another recipe directory could. With some tools to format the code correctly, an agent can use this to automatically create integrations on-request, even using small models such as Gemini 2.5 Flash Lite. Creating a truly cohesive modpack becomes the work of a few prompts rather than months of tedious info-sifting and scriptwriting.

## Architecture

This program uses a portable Conda environment for its own functions, and a portable Java Runtime Environment to install and run a Minecraft server (currently uses 1.20.1) for retrieving data from. KubeJS is used for recipe modification functionality. The Conda and Java environments, the server, and these mods are all installed by running the install script.

From `data/assets/models` directories in the the Jar files in the `server/mods/` folder, a database of all item IDs in the pack is retrieved. While the server is running, a KubeJS script exports all of the default recipes in the pack. These two functionalities are part of the required setup and can be done through the UI.

### Agents

The `grounded_recipe_modifier_agent`, a `SequentialAgent` (from Google ADK), is composed of two subagents: the `searcher_agent` and the `recipe_modifier_agent`. 

The `searcher_agent` uses two tools to search the pack for item IDs, then search for information on existing recipes. It summarizes the information and provides it.

Using the results from the `searcher_agent`, the `recipe_modifier_agent` first comes up with a plan to address the query. Then, it writes KubeJS script using several tools, a different one for each recipe type, which have validation functions to make sure that the ingredients and results are real item IDs. Each tool exactly matches the KubeJS format for writing recipes.

### Tools

#### `searcher_agent`
This agent only has two tools: `search_item_ids`, which uses a semantic search to find exact item IDs in the pack relevant to the user's query. The `find_recipes` tool then uses these item IDs in an exact-match search to find all recipes that either use them as an ingredient or produce them as a result.

#### `recipe_modifier_agent`
This agent has seven tools: `add_shapeless_recipe, add_shaped_recipe, add_smithing_recipe, add_cooking_recipe, add_stonecutting_recipe, remove_recipes, replace_recipe_items`
These all write KubeJS script matching syntax seen in [the KubeJS docs](https://kubejs.com/wiki/tutorials/recipes).

#### Validation
All of the tools which require exact item IDs, namely the recipe modifier tools and the `find_recipes` tool, call a `validate_item_id` function to verify that they're only using real item IDs, providing an error to the agent informing it that the recipe is invalid if necessary.

## Value Statement

Currently, this program just provides a convenient interface for modifying the recipes in a modpack by extracting data from the modpack. Since the agents use tools with validation to write recipes in, they are incapable of writing scripts that cause loading errors. This program is also able to extract item IDs from the pack for semantic search and dump all recipes in the pack—these have a lot of potential for use that is not being taken advantage of yet.


# Installation & Use
## Requirements
* Miniconda, which can be installed from [here](https://docs.conda.io/en/latest/miniconda.html).
* Gemini API key from [Google AI Studio](https://aistudio.google.com)
* Required libraries automatically installed by the install scripts.

## Setup
First, clone the repository. From the repository root directory, run `install.ps1` on Windows (requires Unrestricted execution policy) or `install.sh` on Linux x64. You will be prompted to agree to the Microsoft EULA to be able to run the server.

After the server is installed, you may add all the mods that you wish to the `server/mods/` directory, as normal. There's currently no built-in compatibility checker functionality, so it's recommended to use an existing modpack. Note that you'll need to add KubeJS and its requirements to the pack for clients to be able to connect to the server.

From there, you can run the webui from the terminal with `python run_ui.py`. Run all of the parts in the setup section and restart the UI before your first run.

## Use
You should be able to make requests to the agent, which will automatically write recipes to the file. Running the server after using the agent and connecting with a client will allow you to see your custom recipes. Alternatively, you can move the KubeJS script in `server/kubejs/server_scripts` into the `kubejs/server_scripts directory` in the client pack to make it work on the client.
