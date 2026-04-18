import logging

import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from bot import config, database

logger = logging.getLogger(__name__)


async def _send_thursday_reminder(bot):
    active = await database.get_active()
    queue = await database.get_queue()

    if not active:
        embed = discord.Embed(
            title="🎮 It's Thursday!",
            description=(
                "No active game set yet.\n\n"
                "**Quick commands:**\n"
                "`/advance` — pull a game from the queue or bench\n"
                "`/rotation` — see the full rotation"
            ),
            color=discord.Color.blue(),
        )
    else:
        session_count = active.get("session_count", 0)
        sessions_left = max(0, config.MIN_SESSIONS - session_count)

        lines = [f"**{active['name']}** — Session {session_count + 1} of {config.MIN_SESSIONS} minimum"]

        if queue:
            lines.append("")
            lines.append("**Up next:**")
            for g in queue:
                lines.append(f"• {g['name']}")

        lines.append("")
        lines.append("**Commands:**")
        lines.append("`/log-session` — log tonight's session after you're done")
        if session_count >= config.MIN_SESSIONS:
            lines.append("`/propose-swap` — vote to rotate to the next game")
        else:
            lines.append(f"`/propose-swap` — vote to skip early ({sessions_left} session{'s' if sessions_left != 1 else ''} left before min)")
        lines.append("`/rotation` — see the full rotation & bench")

        embed = discord.Embed(
            title="🎮 It's Thursday!",
            description="\n".join(lines),
            color=discord.Color.blue(),
        )
        if active.get("cover_url"):
            embed.set_image(url=active["cover_url"])

    for guild_id, channel_id in config.GUILD_CHANNEL_MAP.items():
        try:
            channel = bot.get_channel(channel_id) or await bot.fetch_channel(channel_id)
            await channel.send(embed=embed)
        except Exception as exc:
            logger.error("Thursday reminder: could not send to channel %d (guild %d): %s", channel_id, guild_id, exc)


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
