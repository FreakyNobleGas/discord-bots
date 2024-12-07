# Name: Nicholas Quinn
# Created: 11/25/2020
# Description: Discord bot that notifies the channel when a user joins an empty voice channel.
# Helpful Links: https://realpython.com/how-to-make-a-discord-bot-python/

from os import getenv
import discord
from time import time
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Grab secret env variables
load_dotenv()
TOKEN = getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Keep track of how often a user joins an empty voice channel
global time_of_last_msg
time_of_last_msg = time()

@client.event
async def on_ready():
    logger.info(f'{client.user} has connected to Discord!')
    for guild in client.guilds:
        logger.info(f"Connected to {guild.name}")

@client.event
async def on_voice_state_update(member, before, after):
    # TODO: Update this variable to be unique across all servers.
    global time_of_last_msg
        
    guild = discord.utils.get(client.guilds, name=str(member.guild))
    now = time()
        
    # Go through each voice channel in the guild and determine if the voice channel was previously empty,
    # it hasn't been empty longer than 30 seconds, and the member joined the channel.
    for vc in guild.voice_channels:
        if (member.voice is not None) and (len(vc.members) == 1) and ((now - time_of_last_msg) > 30.0):

            # Find text channel to post in
            channel = None
            for ch in guild.channels[0].text_channels:
                if (ch.name == "general"):
                    channel = ch

            # Set channel to first in the list if there is no general text channel
            if channel is None: channel = guild.channels[0].text_channels[0]

            # Delete previous announcements from the bot
            try:
                async for message in channel.history(limit=200):
                    if message.author == client.user:
                        logger.info(f"Deleting message: {message.content}")
                        await message.delete()
            except:
                logger.info("Error: Failed to delete previous messages.")

            # Send a message that a user just joined the channel
            try:
                await channel.send(f'{member} just joined the {member.voice.channel} voice channel!')
                logger.info(f'{member.voice}')
            except:
                logger.info("Error: Failed to send message to text channel.")

            # Update the last time a member joined an empty voice channel
            time_of_last_msg = time()

client.run(TOKEN)