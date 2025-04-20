# music_cmd.py
import asyncio
import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp

import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('music_bot')

class MusicCmd(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # YouTube/YT-DLP setup with newer app versions
        self.YDL_OPTIONS = {
            'format': 'bestaudio/best',
            'quiet': True,
            'noplaylist': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android_music', 'android', 'web'],
                    'player_skip': ['webpage', 'configs'],
                    'player_js_variant': 'android',
                    'player_params': {
                        'json': '{"client":{"clientName":"ANDROID_MUSIC","clientVersion":"7.09.52"}}',
                    },
                    'app': 'android_music',
                    'use_oauth': 'True'
                }
            },
            'user_agent': 'com.google.android.apps.youtube.music/7.09.52 (Linux; U; Android 13; SM-G998B)'
        }

        self.FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn -c:a libopus -b:a 128k'
        }

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info('Music commands ready.')

    def _extract(self, query, YDL_OPTIONS):
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            return ydl.extract_info(query, download=False)

    async def search_yt(self, query):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: self._extract(query, self.YDL_OPTIONS))

    @app_commands.command(name="play", description="Play a song or add it to the queue")
    @app_commands.describe(song_query="Search query or YouTube URL")
    async def play(self, interaction: discord.Interaction, song_query: str):
        await interaction.response.defer()

        # Detailed voice channel connection debugging
        if not interaction.user.voice:
            await interaction.followup.send("You must be in a voice channel to use this command.")
            return

        voice_channel = interaction.user.voice.channel
        logger.info(f"Attempting to connect to voice channel: {voice_channel.name} (ID: {voice_channel.id})")

        # Check for proper permissions
        permissions = voice_channel.permissions_for(interaction.guild.me)
        if not permissions.connect or not permissions.speak:
            await interaction.followup.send("I don't have permission to join or speak in your voice channel.")
            logger.error(f"Missing permissions for channel {voice_channel.name}: Connect: {permissions.connect}, Speak: {permissions.speak}")
            return

        voice_client = interaction.guild.voice_client

        # Connect to voice channel if needed
        try:
            if voice_client is None:
                logger.info(f"Connecting to voice channel {voice_channel.name}")
                voice_client = await voice_channel.connect(timeout=60, reconnect=True)
                logger.info(f"Successfully connected to {voice_channel.name}")
            elif voice_channel != voice_client.channel:
                logger.info(f"Moving from {voice_client.channel.name} to {voice_channel.name}")
                await voice_client.move_to(voice_channel)
                logger.info(f"Successfully moved to {voice_channel.name}")
        except Exception as e:
            await interaction.followup.send(f"Failed to connect to voice channel: {str(e)}")
            logger.error(f"Voice connection error: {e}")
            return

        # Search YouTube for the song (if not a direct link)
        if not "youtube.com" in song_query and not "youtu.be" in song_query:
            youtube_query = "ytsearch1: " + song_query
        else:
            youtube_query = song_query

        try:
            # Extract video information from YouTube
            logger.info(f"Searching for: {youtube_query}")
            info = await self.search_yt(youtube_query)

            # Handle the search results
            if 'entries' in info:
                video = info['entries'][0]
            else:
                video = info

            # Get the audio URL and info
            audio_url = video['url']
            title = video.get('title', 'Unknown')
            thumbnail = video.get('thumbnail', None)
            duration = video.get('duration', 0)

            logger.info(f"Creating audio source for: {title}")

            # Create audio source and play
            try:
                source = await discord.FFmpegOpusAudio.from_probe(
                    audio_url,
                    **self.FFMPEG_OPTIONS
                )

                # Stop any current playback and play the new audio
                if voice_client.is_playing():
                    voice_client.stop()

                voice_client.play(source)
                logger.info(f"Now playing: {title}")

                # Format duration
                duration_str = "Unknown duration"
                if duration:
                    minutes, seconds = divmod(duration, 60)
                    duration_str = f"{minutes:02d}:{seconds:02d}"

                # Create a rich embed with song info
                embed = discord.Embed(
                    title="Now Playing",
                    description=f"**{title}**",
                    color=discord.Color.green()
                )

                if thumbnail:
                    embed.set_thumbnail(url=thumbnail)

                embed.add_field(name="Duration", value=duration_str, inline=True)
                embed.set_footer(text=f"Requested by {interaction.user.display_name}")

                await interaction.followup.send(embed=embed)
            except Exception as e:
                await interaction.followup.send(f"Error playing audio: {str(e)}")
                logger.error(f"Audio playback error: {e}")

        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}")
            logger.error(f"YouTube search error: {e}")

    @app_commands.command(name="stop", description="Stop playing music")
    async def stop(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client

        if voice_client and voice_client.is_connected():
            voice_client.stop()
            await voice_client.disconnect()
            await interaction.response.send_message("⏹️ Stopped playing and disconnected.")
        else:
            await interaction.response.send_message("I'm not connected to a voice channel.")

    @app_commands.command(name="pause", description="Pause the current song")
    async def pause(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client

        if voice_client and voice_client.is_playing():
            voice_client.pause()
            await interaction.response.send_message("⏸️ Paused the music.")
        else:
            await interaction.response.send_message("Nothing is playing right now.")

    @app_commands.command(name="resume", description="Resume the paused song")
    async def resume(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client

        if voice_client and voice_client.is_paused():
            voice_client.resume()
            await interaction.response.send_message("▶️ Resumed the music.")
        else:
            await interaction.response.send_message("Nothing is paused right now.")

async def setup(bot):
    await bot.add_cog(MusicCmd(bot))
