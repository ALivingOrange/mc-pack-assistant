# Project Overview - MC Pack Assistant

## Problem Statement

There are over a hundred thousand Minecraft modpacks out there (can be seen at: modpackindex.com/modpacks), yet only very few do much more than selecting mods. Modpacks can be made much more cohesive with custom integrations such as recipes and loot tables. The success of this approach can be seen in popular packs such as Create: Above and Beyond and Gregtech: New Horizons. However, the process of making these integrations is technical and burdensome. Going through hundreds to thousands of items added by mods and figuring out ways to connect them takes a lot of effort, to say nothing of learning the datapack format or how to use KubeJS and implementing the integrations one at a time. The comparison to just adding mods, with how most launchers can bring a new mod into the pack with one or two clicks, is dire. The average packmaker would benefit greatly from a way to add tailor-made integrations just as easily as they might add new mods.

## Solution Statement

As in many places, AI agents can automate the rote work and ease the hard work here. A program can connect to information from a server installation of Minecraft to find all of the information on items, recipes, etc. From there, agents can search through that data much more naturally than even the most skilled human using JEI or another recipe directory could. With some tools to format the code correctly, an agent can use this to automatically create integrations on-request, even using small models such as Gemini 2.5 Flash Lite. From there, connecting a smarter orchestrator model to the integrator's inputs facilitate the system becoming a one-stop mod integrator. The user can simply make a request for how the pack should be balanced, the orchestrator can create a plan and summon the integrators, and the integrators can turn that into real changes to the modpack. Creating a truly cohesive modpack becomes the work of a few prompts rather than months of tedious info-sifting and scriptwriting.

## Architecture

This program uses a portable Conda environment for its own functions, and a portable Java Runtime Environment to install and run a Minecraft server for retrieving data from. KubeJS and all of its requirements are also installed, as the recipe modification functionality uses it. From `data/assets/models` directories in the the Jar files in the `server/mods/` folder, a database of all item IDs in the pack is retrieved. While the server is running, a KubeJS script exports all of the default recipes in the pack.

[Core: Orchestrator. Not yet implemented]

The `grounded_recipe_modifier_agent`, a `SequentialAgent` (from Google ADK), is composed of two subagents: the `searcher_agent` and the `recipe_modifier_agent`. 

The `searcher_agent` uses two tools in a specific order. First, it uses `search_item_ids` to query the database of item IDs. This is a semantic search, using a `sentence-transformers` embedding search to find exact item IDs related to the query. Then, it uses `find-recipes` to find all of the recipes using IDs it deems most relevant, either as an ingredient or as a result.

Using the results from the `searcher_agent`, the `recipe_modifier_agent` first comes up with a plan to address the query. Then, it writes KubeJS script using several tools, a different one for each recipe type, which have validation functions to make sure that the ingredients and results are real item IDs. Each tool exactly matches the KubeJS format for writing recipes.