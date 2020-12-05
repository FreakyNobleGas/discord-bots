import os
import discord

from discord.ext import commands
from dotenv import load_dotenv


#loads token from .env
load_dotenv()
#saves token to TOKEN variable
TOKEN = os.getenv('DISCORD_TOKEN')

#sets command prefix
client = commands.Bot(command_prefix='!')

#loads specify Cog
@client.command()
async def load(ctx,extension):
    client.load_extension(f'cogs.{extension}')

#unload specify Cog
@client.command()
async def unload(ctx,extension):
    client.unload_extension(f'cogs.{extension}')

#iterates through cog files and loads them
for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')

client.run(TOKEN)