#
# Description: Helper functions for Ivo Bot
#
import discord
import pathlib
import json

# Retrieves all past requested songs if metrics data is not present
def get_all_past_songs(client):
    metrics = {}
    print(client.guilds)
    exit()
    return metrics

# Retrieves metrics file if it does not exist or generates one during run-time.
def get_metrics_file(client):
    # Get metrics file
    try:
        file = pathlib.Path("metrics.json")
        if file.is_file():
            print("Loading metrics file.")
            metricsFile = open("metrics.json", "r+")
        else:
            print("No metrics file found. Creating new metrics file.")
            metricsFile = open("metrics.json", "w+")
            #historical_metrics = get_all_past_songs(client)
            metricsFile.write("{}")
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