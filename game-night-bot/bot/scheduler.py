import logging

import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from bot import config, database
from bot.utils.embeds import get_primary_emoji

logger = logging.getLogger(__name__)


class GameNightPollView(discord.ui.View):
    """Thursday night poll — one button per game + 'Find a New Game'."""

    def __init__(self, games: list[dict]):
        super().__init__(timeout=43200)  # 12 hours
        self.games = games
        # votes: user_id -> game_id (or "new")
        self._votes: dict[str, int | str] = {}

        for game in games[:24]:  # leave room for the "new game" button
            btn = discord.ui.Button(
                label=f"🎮 {game['name'][:40]} (0)",
                style=discord.ButtonStyle.secondary,
                custom_id=f"poll_{game['id']}",
            )
            btn.callback = self._make_game_callback(game["id"], game["name"])
            self.add_item(btn)

        new_btn = discord.ui.Button(
            label="🆕 Find a New Game (0)",
            style=discord.ButtonStyle.blurple,
            custom_id="poll_new",
        )
        new_btn.callback = self._new_game_callback
        self.add_item(new_btn)

    def _make_game_callback(self, game_id: int, game_name: str):
        async def callback(interaction: discord.Interaction):
            user_id = str(interaction.user.id)
            if user_id in self._votes:
                await interaction.response.send_message(
                    "You aweady vote, I see you!", ephemeral=True
                )
                return
            self._votes[user_id] = game_id
            self._update_labels()
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(
                f"Vote counted for **{game_name}**!", ephemeral=True
            )
        return callback

    async def _new_game_callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        if user_id in self._votes:
            await interaction.response.send_message(
                "You aweady vote, I see you!", ephemeral=True
            )
            return
        self._votes[user_id] = "new"
        self._update_labels()
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(
            "Someone use `/add-game` to add something new, dammit!", ephemeral=False
        )

    def _update_labels(self):
        vote_counts: dict[str, int] = {}
        for v in self._votes.values():
            key = str(v)
            vote_counts[key] = vote_counts.get(key, 0) + 1

        for item in self.children:
            if not isinstance(item, discord.ui.Button):
                continue
            if item.custom_id == "poll_new":
                count = vote_counts.get("new", 0)
                item.label = f"🆕 Find a New Game ({count})"
            elif item.custom_id and item.custom_id.startswith("poll_"):
                game_id = item.custom_id[5:]
                count = vote_counts.get(game_id, 0)
                # Trim name from current label to rebuild it
                name_part = item.label.split(" (")[0][2:]  # strip "🎮 "
                item.label = f"🎮 {name_part} ({count})"

    async def on_timeout(self):
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass


async def _send_reminder_to_guild(bot, guild_id: int, channel_id: int):
    games = await database.get_game_stats(guild_id)

    embed = discord.Embed(
        title="🎮 It Thulsday! Git In Here!",
        color=discord.Color.blue(),
    )

    if not games:
        embed.description = (
            "No game in da lotation yet, you son of bitch!\n"
            "Use `/add-game` to add something!"
        )
        view = None
    else:
        lines = []
        for g in games:
            emoji = get_primary_emoji(g.get("genre_tags", []))
            session_count = g.get("session_count", 0)
            last_played = g.get("last_played")
            date_str = str(last_played)[:10] if last_played else "never"
            lines.append(
                f"{emoji} **{g['name']}** — {session_count} session{'s' if session_count != 1 else ''}, last pwayed {date_str}"
            )

        embed.description = (
            "\n".join(lines)
            + "\n\n**What game you want play tonight? Vote below, dammit!**"
        )
        view = GameNightPollView(games)

    try:
        channel = bot.get_channel(channel_id) or await bot.fetch_channel(channel_id)
        msg = await channel.send(embed=embed, view=view)
        if view:
            view.message = msg
    except Exception as exc:
        logger.error("Thursday reminder: could not send to channel %d (guild %d): %s", channel_id, guild_id, exc)


async def _send_thursday_reminder(bot):
    for guild_id, channel_id in config.GUILD_CHANNEL_MAP.items():
        await _send_reminder_to_guild(bot, guild_id, channel_id)


def create_scheduler(bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    hour, minute = config.REMINDER_TIME.split(":")
    scheduler.add_job(
        _send_thursday_reminder,
        CronTrigger(
            day_of_week="thu",
            hour=int(hour),
            minute=int(minute),
            timezone="America/New_York",
        ),
        args=[bot],
    )
    logger.info("Thursday reminder scheduled for %s ET.", config.REMINDER_TIME)
    return scheduler
