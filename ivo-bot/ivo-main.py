# Creaters: Nick Quinn and X'Zavier Wolfinbarger
#
# Description: Ivo is a Groovy music tracker and will track how often a song is played, who played it, and much more.

import os
import discord
import time
from dotenv import load_dotenv
from discord.ext import commands

# Grab secret env variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

client = discord.Client()

#sets command prefix
client = commands.Bot(command_prefix = '$')

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

client.run(TOKEN)