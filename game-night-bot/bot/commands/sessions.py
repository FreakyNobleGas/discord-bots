import math
import logging

import discord
from discord import app_commands
from discord.ext import commands

from bot import config, database
from bot.utils import embeds

logger = logging.getLogger(__name__)

SESSIONS_PER_PAGE = 10


class HistoryView(discord.ui.View):
    def __init__(self, current_page: int, total_pages: int):
        super().__init__(timeout=120)
        self.current_page = current_page
        self.total_pages = total_pages
        self._refresh_buttons()

    def _refresh_buttons(self):
        self.prev_btn.disabled = self.current_page <= 1
        self.next_btn.disabled = self.current_page >= self.total_pages

    @discord.ui.button(label="◀ Prev", style=discord.ButtonStyle.secondary)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        await self._update(interaction)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        await self._update(interaction)

    async def _update(self, interaction: discord.Interaction):
        sessions, total = await database.get_sessions_paginated(
            self.current_page, SESSIONS_PER_PAGE
        )
        self.total_pages = max(1, math.ceil(total / SESSIONS_PER_PAGE))
        self._refresh_buttons()
        embed = embeds.session_history(sessions, self.current_page, self.total_pages)
        await interaction.response.edit_message(embed=embed, view=self)


class SessionsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="log-session", description="Log a gaming session for tonight's game")
    @app_commands.describe(notes="Optional notes about tonight's session")
    async def log_session(self, interaction: discord.Interaction, notes: str | None = None):
        await interaction.response.defer()

        active = await database.get_active()
        if not active:
            await interaction.followup.send(
                "No active game! Use `/advance` to set one first."
            )
            return

        new_count = await database.log_session(
            game_id=active["id"],
            logged_by=interaction.user.name,
            notes=notes,
        )

        embed = discord.Embed(
            title="📝 Session Logged",
            description=(
                f"Logged a session for **{active['name']}**\n"
                f"Session **{new_count}** of {config.MIN_SESSIONS} minimum"
            ),
            color=discord.Color.green(),
        )
        if notes:
            embed.add_field(name="Notes", value=notes, inline=False)

        await interaction.followup.send(embed=embed)

        if new_count >= config.MIN_SESSIONS:
            await interaction.channel.send(
                f"✅ **{active['name']}** has hit its minimum sessions — "
                "use `/propose-swap` to rotate out!"
            )

    @app_commands.command(name="history", description="View session history")
    async def history(self, interaction: discord.Interaction):
        await interaction.response.defer()

        sessions, total = await database.get_sessions_paginated(1, SESSIONS_PER_PAGE)
        if not sessions:
            await interaction.followup.send("No sessions logged yet!")
            return

        total_pages = max(1, math.ceil(total / SESSIONS_PER_PAGE))
        embed = embeds.session_history(sessions, 1, total_pages)
        view = HistoryView(current_page=1, total_pages=total_pages)
        await interaction.followup.send(embed=embed, view=view)

    @app_commands.command(name="stats", description="View rotation statistics")
    async def stats(self, interaction: discord.Interaction):
        await interaction.response.defer()
        stats = await database.get_stats()
        embed = embeds.stats_board(stats)
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(SessionsCog(bot))
