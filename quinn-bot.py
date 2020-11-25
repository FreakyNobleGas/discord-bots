# Name: Nicholas Quinn
# Created: 11/25/2020
# Description: Discord bot that notifies the channel when a user joins a voice channel.
# Helpful Links: https://realpython.com/how-to-make-a-discord-bot-python/

import os

import discord
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

client = discord.Client()

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    print(f'{client.user} is connected to the following servers:')
    for guild in client.guilds:
        print('\t', guild.name, ' - ', guild.id)

@client.event
async def on_voice_state_update(member, before, after):
    #print(f'{member.voice}')
    if (member.voice is not None):
        print(f'{member} just joined the {member.voice.channel} voice channel!')

client.run(TOKEN)