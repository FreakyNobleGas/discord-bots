import logging

import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from bot import config, database

logger = logging.getLogger(__name__)


async def _send_thursday_reminder(bot):
    channel = bot.get_channel(config.REMINDER_CHANNEL_ID)
    if not channel:
        logger.error("Thursday reminder: channel %d not found.", config.REMINDER_CHANNEL_ID)
        return

    active = await database.get_active()

    if not active:
        embed = discord.Embed(
            title="🎮 It's Thursday!",
            description="No active game — use `/advance` to pick one from the queue!",
            color=discord.Color.blue(),
        )
    else:
        session_count = active.get("session_count", 0)
        embed = discord.Embed(
            title="🎮 It's Thursday!",
            description=(
                f"Tonight we're playing:\n"
                f"**{active['name']}** — Session {session_count + 1} of {config.MIN_SESSIONS} minimum\n"
                f"Use `/log-session` after you're done!"
            ),
            color=discord.Color.blue(),
        )
        if active.get("cover_url"):
            embed.set_thumbnail(url=active["cover_url"])

    await channel.send(embed=embed)


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
