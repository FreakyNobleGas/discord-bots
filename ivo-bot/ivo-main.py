# Creaters: Nick Quinn and X'Zavier Wolfinbarger
#
# Description: Ivo is a Groovy music tracker and will track how often a song is played, who played it, and much more.

import os
import discord
import time
import json
import pathlib
from dotenv import load_dotenv
from discord.ext import commands

# Grab secret env variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

client = discord.Client()

#sets command prefix
client = commands.Bot(command_prefix = '$')

try:
    file = pathlib.Path("metrics.json")
    if file.is_file():
        print("Loading metrics file.")
        metricsFile = open("metrics.json", "r+")
    else:
        print("No metrics file found. Creating new metrics file.")
        metricsFile = open("metrics.json", "w+")
        metricsFile.write("{}")
        metricsFile.close()

except Exception as e:
    print("Error: Could not open file! Exiting...")
    print(e)
    exit()

try:
    # Get JSON object that holds metrics
    print("Loading metrics JSON file.")
    global metrics
    with open("metrics.json") as metricsFile:
        metrics = json.load(metricsFile,)
    
    metricsFile.close()    

except Exception as e:
    print("Error: Could not load metrics file. Exiting...")
    print(e)
    exit()

#loads specific cog
@client.command()
async def load(ctx, extension):
    client.load_extension(f'cogs.{extension}')

#unload specific cog
@client.command()
async def unload(ctx, extension):
    client.unload_extension(f'cogs.{extension}')

#iterates through cog files and loads them
for filename in os.listdir('./ivo-bot/cogs'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')

# Keep track of how often a user joins an empty voice channel
global time_of_last_msg
time_of_last_msg = time.time()

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    print(f'{client.user} is connected to the following servers:')
    for guild in client.guilds:
        print('\t', guild.name, ' - ', guild.id)

@client.event
async def on_voice_state_update(member, before, after):
    # Define important variables
    global time_of_last_msg
    
    guild = discord.utils.get(client.guilds, name="FreakyNobleGas's server")
    now = time.time()

    # Go through each voice channel in the guild and determine if the voice channel was previously empty,
    # it hasn't been empty longer than 30 seconds, and the member joined the channel.
    for vc in guild.voice_channels:
        if (member.voice is not None) and (len(vc.members) == 1):
            for ch in guild.channels[0].text_channels:
                if (ch.name == "general"):
                    channel = ch
            await channel.send(f'{member} just joined the {member.voice.channel} voice channel!')
            print(f'{member.voice}')

            # Update the last time a member joined an empty voice channel
            time_of_last_msg = time.time()

@client.event
async def on_message(message):
    global metrics
    print(type(metrics))

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

client.run(TOKEN)