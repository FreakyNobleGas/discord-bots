# Name: Nicholas Quinn
# Created: 11/25/2020
# Description: Discord bot that notifies the channel when a user joins an empty voice channel.
# Helpful Links: https://realpython.com/how-to-make-a-discord-bot-python/

from os import getenv
import discord
from time import time
from dotenv import load_dotenv
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

trace.set_tracer_provider(
TracerProvider(
        resource=Resource.create({SERVICE_NAME: "voice-chat-bot"})
    )
)
tracer = trace.get_tracer(__name__)

# create a JaegerExporter
jaeger_exporter = JaegerExporter(
    # Configure agent
    agent_host_name='localhost',
    agent_port=6831
)

# Create a BatchSpanProcessor and add the exporter to it
span_processor = BatchSpanProcessor(jaeger_exporter)

# add to the tracer
trace.get_tracer_provider().add_span_processor(span_processor)

# Grab secret env variables
load_dotenv()
TOKEN = getenv('DISCORD_TOKEN')

client = discord.Client()

# Keep track of how often a user joins an empty voice channel
global time_of_last_msg
time_of_last_msg = time()

@client.event
async def on_ready():
    with tracer.start_as_current_span('on_ready'):
        print(f'{client.user} has connected to Discord!')
        print(f'{client.user} is connected to the following servers:')
        for guild in client.guilds:
            print('\t', guild.name, ' - ', guild.id)

@client.event
async def on_voice_state_update(member, before, after):
    with tracer.start_as_current_span('on_voice_state_update'):
        # Define important variables
        global time_of_last_msg
        
        with tracer.start_as_current_span(f'Get all guilds for member {member}'):
            guild = discord.utils.get(client.guilds, name=str(member.guild))
        now = time()
        
        # Go through each voice channel in the guild and determine if the voice channel was previously empty,
        # it hasn't been empty longer than 30 seconds, and the member joined the channel.
        for vc in guild.voice_channels:
            with tracer.start_as_current_span('Check Voice Channel ' + str(vc)):
                if (member.voice is not None) and (len(vc.members) == 1) and ((now - time_of_last_msg) > 30.0):

                    # Find text channel to post in
                    channel = None
                    for ch in guild.channels[0].text_channels:
                        if (ch.name == "general"):
                            channel = ch
                    
                    # Set channel to first in the list if there is no general text channel
                    if channel is None: channel = guild.channels[0].text_channels[0]

                    # Delete previous announcements from the bot
                    with tracer.start_as_current_span('Delete previous Bot Announcement'):
                        try:
                            async for message in channel.history(limit=200):
                                if message.author == client.user:
                                    print("Deleting message: ", message.content)
                                    await message.delete()
                        except:
                            print("Error: Failed to delete previous messages.")

                    # Send a message that a user just joined the channel
                    with tracer.start_as_current_span(f'Send announcement that {member} joined'):
                        try:
                            await channel.send(f'{member} just joined the {member.voice.channel} voice channel!')
                            print(f'{member.voice}')
                        except:
                            print("Error: Failed to send message to text channel.")

                    # Update the last time a member joined an empty voice channel
                    time_of_last_msg = time()

client.run(TOKEN)
