#
# Description: Helper functions for Ivo Bot
#
import discord
import pathlib
import json

# Retrieves all past requested songs if metrics data is not present
async def get_all_past_songs(client):
    metrics = {}

    # Loop through every message in every text channel for every available guild
    # to find previously played songs and add them to the metrics object
    for guild in client.guilds:
        metrics[guild.name] = {}

        for channel in guild.text_channels:   
            messages = await channel.history().flatten()
    
            for message in messages:
                content = str(message.content)
                author = str(message.author)
                if content.startswith("-play "):
                    # Remove '-play ' from song
                    content = content[6:]
                    
                    # Check if author exists in guild and increment song appropriately. Otherwise, create new author
                    # with song.
                    if author in metrics[guild.name]:
                        
                        # Check if song exists, if yes, then increment count. Otherwise add new song to list
                        if content in metrics[guild.name][author]:
                            metrics[guild.name][author][content] = int(metrics[guild.name][author][content]) + 1
                        else:
                            metrics[guild.name][author][content] = 1
                    
                    else:
                        metrics[guild.name][author] = {content : 1}
                        
    return metrics

# Retrieves metrics file if it does not exist or generates one during run-time.
async def get_metrics_file(client):
    # Get metrics file
    try:
        file = pathlib.Path("metrics.json")
        if file.is_file():
            print("Loading metrics file.")
            metricsFile = open("metrics.json", "r+")
        else:
            print("No metrics file found. Creating new metrics file.")
            metricsFile = open("metrics.json", "w+")
            historical_metrics = await get_all_past_songs(client)
            metricsFile.write(json.dumps(historical_metrics))
            metricsFile.close()

    except Exception as e:
        print("Error: Could not open file! Exiting...")
        print(e)
        exit()

    # Get JSON object that holds metrics
    try:
        print("Loading metrics JSON file.")
        global metrics
        with open("metrics.json") as metricsFile:
            metrics = json.load(metricsFile,)
        
        metricsFile.close()    

    except Exception as e:
        print("Error: Could not load metrics file. Exiting...")
        print(e)
        exit()

    return metrics