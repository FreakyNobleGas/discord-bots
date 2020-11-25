# Name: Nicholas Quinn
# Created: 11/25/2020
# Description: Discord bot that notifies the channel when a user joins an empty voice channel.
# Helpful Links: https://realpython.com/how-to-make-a-discord-bot-python/

import os
import discord
import time
from dotenv import load_dotenv

# Grab secret env variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

client = discord.Client()

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
    guild = discord.utils.get(client.guilds, name="Just The Young Folk")
    now = time.time()

    # Go through each voice channel in the guild and determine if the voice channel was previously empty,
    # it hasn't been empty longer than 30 seconds, and the member joined the channel.
    for vc in guild.voice_channels:
        if (member.voice is not None) and (len(vc.members) == 1) and ((now - time_of_last_msg) > 30.0):
            for ch in guild.channels[0].text_channels:
                if (ch.name == "general"):
                    channel = ch
            await channel.send(f'{member} just joined the {member.voice.channel} voice channel!')
            print(f'{member.voice}')

            # Update the last time a member joined an empty voice channel
            time_of_last_msg = time.time()

client.run(TOKEN)