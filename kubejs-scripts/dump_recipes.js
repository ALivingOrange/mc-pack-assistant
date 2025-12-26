ServerEvents.recipes(event => {
    console.log("AGENTSYS_RECIPE_DUMP_START")

    let count = 0
    event.forEachRecipe({}, r => {
        try {
            let recipeId = r.getId().toString()
            let recipeType = r.getType().toString()

            // Raw JSON data contains ingredients, results, patterns, etc.
            let rawData = JSON.parse(r.json.toString())
            
            let cleanEntry = {
                id: recipeId,
                type: recipeType, 
                data: rawData 
            }
            
            console.log("AGENTSYS_DATA::" + JSON.stringify(cleanEntry))
            count++
        } catch (e) {
            console.error(`AGENTSYS_ERROR::${r.getId()}`)
        }
    })

    console.log(`AGENTSYS_RECIPE_DUMP_END::${count}`)
});
