# Creaters: Nick Quinn and X'Zavier Wolfinbarger
#
# Description: Ivo is a Groovy music tracker and will track how often a song is played, who played it, and much more.

import os
import discord
import time
import json
import helper_functions
from dotenv import load_dotenv
from discord.ext import commands

# Grab secret env variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

client = discord.Client()

# Sets command prefix
client = commands.Bot(command_prefix = '$')

# Loads specific cog
@client.command()
async def load(ctx, extension):
    print("loading...")
    print("Extension is ", extension)
    client.load_extension(f'cogs.{extension}')

# Unload specific cog
@client.command()
async def unload(ctx, extension):
    client.unload_extension(f'cogs.{extension}')

# Iterates through cog files and loads them
for filename in os.listdir('./ivo-bot/cogs'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    print(f'{client.user} is connected to the following servers:')
    for guild in client.guilds:
        print('\t', guild.name, ' - ', guild.id)

    global metrics
    metrics = helper_functions.get_metrics_file(client)

@client.event
async def on_message(message):
    global metrics

    if "-play" in message.content:
        author = str(message.author)
        guild = str(message.channel.guild)
        songPlayed = message.content[5:].strip()

        print(author, " has requested the song ", songPlayed)

        # Initialize guild if it is empty and add first user
        if guild not in metrics.keys():
            metrics[guild] = {
                "users" : {
                    author : {
                        "totalSongs" : 1,
                        "songsPlayed" : {
                            songPlayed : 1
                        }
                    }
                }
            }
        # Initialize user if this is their first song
        elif author not in metrics[guild]["users"].keys():
            metrics[guild]["users"][author] = {
                "totalSongs" : 1,
                "songsPlayed" : {
                     songPlayed : 1
                }
            }
        # Update previous user's total
        else:
            userData = metrics[str(guild)]["users"][str(author)]
            userData["totalSongs"] = userData["totalSongs"] + 1

            if songPlayed not in userData["songsPlayed"].keys():
                userData["songsPlayed"][songPlayed] = 1
            else:
                userData["songsPlayed"][songPlayed] += 1
        
        with open("metrics.json", "w+") as metricsFile:
            metricsFile.write(json.dumps(metrics))
        metricsFile.close()

    await commands.Bot.process_commands(client, message)

client.run(TOKEN)