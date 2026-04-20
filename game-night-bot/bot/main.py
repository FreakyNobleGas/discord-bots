import asyncio
import logging

import discord
from discord.ext import commands

from bot import config, database
from bot.scheduler import create_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


class RotationBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix=[], intents=intents)
        self.scheduler = None

    async def setup_hook(self):
        await database.init_db()
        logger.info("Database initialized.")

        await self.load_extension("bot.commands.games")
        await self.load_extension("bot.commands.sessions")
        await self.load_extension("bot.commands.help")
        logger.info("Cogs loaded.")

        for guild_id in config.DISCORD_GUILD_IDS:
            guild = discord.Object(id=guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        logger.info("Slash commands synced to %d guild(s).", len(config.DISCORD_GUILD_IDS))

    async def on_ready(self):
        logger.info("Logged in as %s (ID: %s)", self.user, self.user.id)

        if self.scheduler is None:
            self.scheduler = create_scheduler(self)
            self.scheduler.start()

    async def close(self):
        if self.scheduler:
            self.scheduler.shutdown(wait=False)
        await super().close()


async def main():
    bot = RotationBot()
    async with bot:
        await bot.start(config.DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
