import logging

import discord
from discord import app_commands
from discord.ext import commands

from bot import database
from bot.locale import t

logger = logging.getLogger(__name__)


async def _game_autocomplete(
    interaction: discord.Interaction, current: str
) -> list[app_commands.Choice[str]]:
    try:
        games = await database.search_games(interaction.guild_id, current)
    except Exception:
        games = []
    return [
        app_commands.Choice(name=g["name"][:100], value=str(g["id"]))
        for g in games
    ]


class SessionsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="log-session", description="Log a gaming session")
    @app_commands.describe(
        game="The game you played tonight",
        notes="Optional notes about the session",
    )
    @app_commands.autocomplete(game=_game_autocomplete)
    async def log_session(self, interaction: discord.Interaction, game: str, notes: str | None = None):
        await interaction.response.defer()
        guild_id = interaction.guild_id

        target = await database.get_game_by_id(guild_id, int(game)) if game.isdigit() else None
        if not target:
            await interaction.followup.send(t("session_not_found"))
            return

        total_sessions = await database.log_session(
            game_id=target["id"],
            logged_by=interaction.user.name,
            notes=notes,
        )

        session_word = "sessions" if total_sessions != 1 else "session"
        embed = discord.Embed(
            title=t("session_logged_title"),
            description=t(
                "session_logged_description",
                name=target["name"],
                total=total_sessions,
                session_word=session_word,
            ),
            color=discord.Color.green(),
        )
        if notes:
            embed.add_field(name="Notes", value=notes, inline=False)

        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(SessionsCog(bot))
