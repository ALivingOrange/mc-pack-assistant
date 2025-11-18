ServerEvents.recipes(event => {
    console.log("AGENTSYS_RECIPE_DUMP_START")

    let count = 0
    event.forEachRecipe({}, r => {
        try {
            // 1. Force ID and Type to be simple strings immediately
            let recipeId = r.getId().toString()
            let recipeType = r.getType().toString()

            // 2. Get the raw JSON data (this contains ingredients, results, patterns, etc.)
            let rawData = JSON.parse(r.json.toString())
            
            // 3. Construct the clean object
            let cleanEntry = {
                id: recipeId,
                type: recipeType, 
                data: rawData 
            }
            
            // 4. Log it
            console.log("AGENTSYS_DATA::" + JSON.stringify(cleanEntry))
            count++
        } catch (e) {
            console.error(`AGENTSYS_ERROR::${r.getId()}`)
        }
    })

    console.log(`AGENTSYS_RECIPE_DUMP_END::${count}`)
});