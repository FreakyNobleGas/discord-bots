import logging

import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from bot import config, database

logger = logging.getLogger(__name__)


async def _send_thursday_reminder(bot):
    for guild_id, channel_id in config.GUILD_CHANNEL_MAP.items():
        await _send_reminder_to_guild(bot, guild_id, channel_id)


async def _send_reminder_to_guild(bot, guild_id: int, channel_id: int):
    active = await database.get_active(guild_id)
    queue = await database.get_queue(guild_id)

    if not active:
        embed = discord.Embed(
            title="🎮 It Thulsday! Git In Here!",
            description=(
                "No game set yet, you son of bitch!\n\n"
                "**Quick command:**\n"
                "`/advance` — pull a game flom da queue or bench\n"
                "`/rotation` — see da full lotation"
            ),
            color=discord.Color.blue(),
        )
    else:
        session_count = active.get("session_count", 0)
        sessions_left = max(0, config.MIN_SESSIONS - session_count)

        lines = [f"Tonight we play:\n**{active['name']}** — Session {session_count + 1} of {config.MIN_SESSIONS} minimum"]

        if queue:
            lines.append("")
            lines.append("**Up next in line:**")
            for g in queue:
                lines.append(f"• {g['name']}")

        lines.append("")
        lines.append("**Command, dammit:**")
        lines.append("`/log-session` — wog tonight session when you done")
        if session_count >= config.MIN_SESSIONS:
            lines.append("`/propose-swap` — vote to wotate to da next game")
        else:
            lines.append(f"`/propose-swap` — vote to skip eawly ({sessions_left} session{'s' if sessions_left != 1 else ''} left before min)")
        lines.append("`/rotation` — see da full lotation & bench")

        embed = discord.Embed(
            title="🎮 It Thulsday! Git In Here!",
            description="\n".join(lines),
            color=discord.Color.blue(),
        )
        if active.get("cover_url"):
            embed.set_image(url=active["cover_url"])

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
