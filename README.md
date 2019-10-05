# "Where to rent/buy" helper

If you've ever been looking for a property to rent or buy, but:
- You know what town/city you want to live in, but you're unsure which areas of that city to look in?
- You want to live in a safe area, but all you have to go on is your gut feeling about which areas are good/bad, or other peoples' anecdotal experiences? ("Oh yeah I lived in X for a bit, it was ok!", "Oh don't stay there, my cousin stays there and she got broken into last year"...)
- You know there's a location which you want to commute to (e.g. a workplace), and you know what your personal tolerance for commute time is, but it's hard to know what areas of the city meet those criteria unless you're super familiar with that city?
- You've seen the property search sites which let you draw a shape for the region you want to search in, but you're not sure what shape to draw because you don't know the area well enough?

Well, this tool is here to help solve that, with data! 😎

This should help you generate a meaningful search area which factors in your personal preferences for:

- Maximum walking time from a desired location (optional)
- Maximum public transport travel time from a desired location (optional)
- Maximum drive time from a desired location (optional)
- Level of deprivation in the area (according to the Scottish Index of Multiple Deprivations (https://simd.scot) or English Index of Multiple Deprivations (http://dclgapps.communities.gov.uk/imd/iod_index.html)

It'll generate shapes for each of those filters based on the parameters you specify, then find the intersection of all of those shapes, representing the area you want to search in:

![alt text](https://raw.githubusercontent.com/beveradb/home-area-helper/master/screenshots/polygon-debugging.png "Debug Output")

It'll then produce an encoded URL which is compatible with the leading property search site in the UK, Zoopla, and launch that in a web browser for your convenience:

![alt text](https://github.com/beveradb/home-area-helper/blob/master/screenshots/end-result-zoopla.png?raw=true "Zoopla Output")

You can then set up an alert for that search on Zoopla's site so you get an immediate notification whenever a new property comes on the market in your budget in that area! 
