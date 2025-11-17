def add_shapeless_recipe(comment: str, ingredients: dict, result: str,count: int, output_path: str) -> dict:
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

        output_path: The file path for the script to be written in.
    """
 # Read output file
    try:
        with open(output_path, 'r') as file:
            lines:list[str] = file.readlines()
    except IOError as e:
        return {"status": "error", "error_message": ("Error reading file: " + str(e))}
# Remove last line (should be closing "})")        
    if lines: lines = lines[:-1]

# TO-DO: Validate Item IDs

# Add script to lines
    lines.append(f"\n\n# {comment}\n")
    lines.append("event.shapeless(\n")
    lines.append(f"\tItem.of({result}, {count}),\n")
    lines.append("\t[\n")
    for key in ingredients:
        # Only specify count if >1
        if ingredients[key] == 1:
            lines.append(f"\t\t'{key}',\n")
        else:
            lines.append(f"\t\t'{ingredients[key]}x {key}',\n")
    # Remove comment from last ingredient
    lines[-1] = lines[-1][:-2] + "\n"
    
    lines.append("\t]\n")
    lines.append(")\n")
    lines.append("})")

# Write back to output file
    try:
        with open(output_path, 'w') as file:
            file.writelines(lines)
    except IOError as e:
        return {"status": "error", "error_message": ("Error writing file: " + str(e))}

    return {"status": "success"}