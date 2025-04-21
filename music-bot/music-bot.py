# Name: X'Zaiver Wolfinbarger
# Created: 04/20/2025
# Description: Discord bot that plays music a user requests.

import os
import logging
import asyncio
import discord

from discord.ext import commands
from time import time
from dotenv import load_dotenv

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Grab secret env variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    logger.info(f'{bot.user} has connected to Discord!')
    for guild in bot.guilds:
        logger.info(f"Connected to {guild.name}")

async def setup():
     for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            print(f'loading {filename[:-3]}...')
            await bot.load_extension(f'cogs.{filename[:-3]}')

async def main():
    await setup()
    await bot.start(TOKEN)

asyncio.run(main())
