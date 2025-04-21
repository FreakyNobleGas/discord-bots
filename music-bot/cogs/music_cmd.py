# music_cmd.py
import asyncio
import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp

import logging
from collections import deque

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('music_bot')

class MusicCmd(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Music queue storage - using guild ID as key
        self.music_queues = {}
        self.current_songs = {}
        self.is_loop_playing = {}

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

    def get_queue(self, guild_id):
        """Get or create a queue for a guild"""
        if guild_id not in self.music_queues:
            self.music_queues[guild_id] = deque()
        return self.music_queues[guild_id]

    async def play_next(self, interaction, voice_client):
        """Play the next song in the queue"""
        guild_id = interaction.guild_id
        queue = self.get_queue(guild_id)

        # Check if queue is empty
        if not queue:
            logger.info(f"Queue is empty for guild {guild_id}")
            self.current_songs[guild_id] = None
            return

        # Get the next song from the queue
        song_info = queue.popleft()

        # If loop is enabled, add the current song back to the end of the queue
        if guild_id in self.is_loop_playing and self.is_loop_playing[guild_id]:
            queue.append(song_info)

        # Store current song
        self.current_songs[guild_id] = song_info

        try:
            # Create audio source and play
            source = await discord.FFmpegOpusAudio.from_probe(
                song_info['audio_url'],
                **self.FFMPEG_OPTIONS
            )

            # Play the song
            voice_client.play(
                source,
                after=lambda e: asyncio.run_coroutine_threadsafe(
                    self.song_finished(interaction, voice_client, e),
                    self.bot.loop
                )
            )

            logger.info(f"Now playing: {song_info['title']}")

            # Send now playing message
            embed = discord.Embed(
                title="Now Playing",
                description=f"**{song_info['title']}**",
                color=discord.Color.green()
            )

            if song_info['thumbnail']:
                embed.set_thumbnail(url=song_info['thumbnail'])

            duration_str = "Unknown duration"
            if song_info['duration']:
                minutes, seconds = divmod(song_info['duration'], 60)
                duration_str = f"{minutes:02d}:{seconds:02d}"

            embed.add_field(name="Duration", value=duration_str, inline=True)
            embed.set_footer(text=f"Requested by {song_info['requester']}")

            # Use the channel where the command was used
            channel = self.bot.get_channel(song_info['channel_id'])
            if channel:
                await channel.send(embed=embed)

        except Exception as e:
            logger.error(f"Error playing next song: {e}")
            # Try to play the next song if this one fails
            await self.play_next(interaction, voice_client)

    async def song_finished(self, interaction, voice_client, error):
        """Called when a song finishes playing"""
        if error:
            logger.error(f"Error in playback: {error}")

        # Play the next song if available
        await self.play_next(interaction, voice_client)

    @app_commands.command(name="play", description="Play a song or add it to the queue")
    @app_commands.describe(song_query="Search query or YouTube URL")
    async def play(self, interaction: discord.Interaction, song_query: str):
        await interaction.response.defer()

        # Check if user is in voice channel
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

        # Search YouTube for the song
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

            # Create song info dict
            song_info = {
                'title': title,
                'audio_url': audio_url,
                'thumbnail': thumbnail,
                'duration': duration,
                'requester': interaction.user.display_name,
                'requester_id': interaction.user.id,
                'channel_id': interaction.channel_id
            }

            # Add to queue
            guild_id = interaction.guild_id
            queue = self.get_queue(guild_id)
            queue.append(song_info)

            position = len(queue)

            # If nothing is currently playing, start playing
            if not voice_client.is_playing():
                await self.play_next(interaction, voice_client)
                await interaction.followup.send(f"🎵 Added to queue and playing now: **{title}**")
            else:
                # Otherwise just add to queue
                await interaction.followup.send(f"🎵 Added to queue (position {position}): **{title}**")

        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}")
            logger.error(f"YouTube search error: {e}")

    @app_commands.command(name="skip", description="Skip the current song")
    async def skip(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client

        if not voice_client or not voice_client.is_playing():
            await interaction.response.send_message("Nothing is playing right now.")
            return

        voice_client.stop()  # This will trigger the play_next method
        await interaction.response.send_message("⏭️ Skipped to the next song.")

    @app_commands.command(name="queue", description="Show the current music queue")
    async def queue(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        queue = self.get_queue(guild_id)

        if not queue and guild_id not in self.current_songs:
            await interaction.response.send_message("The queue is empty and nothing is playing.")
            return

        embed = discord.Embed(
            title="Music Queue",
            color=discord.Color.blue()
        )

        # Add current song if there is one
        if guild_id in self.current_songs and self.current_songs[guild_id]:
            current = self.current_songs[guild_id]
            embed.add_field(
                name="Now Playing",
                value=f"**{current['title']}** (Requested by {current['requester']})",
                inline=False
            )

        # Add queue
        if queue:
            queue_text = ""
            for i, song in enumerate(queue, 1):
                queue_text += f"{i}. **{song['title']}** (Requested by {song['requester']})\n"

                # Split into multiple fields if too long
                if i % 10 == 0 or i == len(queue):
                    embed.add_field(
                        name=f"Queue (Total: {len(queue)})",
                        value=queue_text,
                        inline=False
                    )
                    queue_text = ""
        else:
            embed.add_field(
                name="Queue",
                value="The queue is empty. Add songs with /play!",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="clear", description="Clear the music queue")
    async def clear(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id

        if guild_id in self.music_queues:
            self.music_queues[guild_id].clear()
            await interaction.response.send_message("🧹 Queue cleared!")
        else:
            await interaction.response.send_message("The queue is already empty.")

    @app_commands.command(name="stop", description="Stop playing music and clear the queue")
    async def stop(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        guild_id = interaction.guild_id

        if voice_client and voice_client.is_connected():
            # Clear the queue
            if guild_id in self.music_queues:
                self.music_queues[guild_id].clear()

            # Stop playing and disconnect
            voice_client.stop()
            await voice_client.disconnect()

            # Clear current song
            self.current_songs[guild_id] = None

            await interaction.response.send_message("⏹️ Stopped playing, cleared queue, and disconnected.")
        else:
            await interaction.response.send_message("I'm not connected to a voice channel.")

    @app_commands.command(name="loop", description="Toggle looping the current queue")
    async def loop(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id

        # Toggle loop status
        current_status = self.is_loop_playing.get(guild_id, False)
        self.is_loop_playing[guild_id] = not current_status

        if self.is_loop_playing[guild_id]:
            await interaction.response.send_message("🔄 Loop mode enabled! The queue will repeat.")
        else:
            await interaction.response.send_message("➡️ Loop mode disabled.")

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
