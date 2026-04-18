import logging

import discord
from discord import app_commands
from discord.ext import commands

from bot import config, database
from bot.utils import embeds

logger = logging.getLogger(__name__)

# Tracks active propose-swap views by game_id so we don't double-post
_active_swap_views: dict[int, "ProposeSwapView"] = {}


class ProposeSwapView(discord.ui.View):
    def __init__(self, bot: commands.Bot, game_id: int, game_name: str):
        super().__init__(timeout=86400)  # 24 hours
        self.bot = bot
        self.game_id = game_id
        self.game_name = game_name
        self.message: discord.Message | None = None

    @discord.ui.button(label="✅ Advance (0)", style=discord.ButtonStyle.green)
    async def vote_advance(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await database.has_voted(self.game_id, "early_exit", str(interaction.user.id)):
            await interaction.response.send_message("You've already voted!", ephemeral=True)
            return

        await database.add_vote(self.game_id, "early_exit", str(interaction.user.id))
        count = await database.get_vote_count(self.game_id, "early_exit")
        button.label = f"✅ Advance ({count}/{config.EARLY_EXIT_VOTES})"

        if count >= config.EARLY_EXIT_VOTES:
            button.disabled = True
            await interaction.response.edit_message(view=self)
            self.stop()
            _active_swap_views.pop(self.game_id, None)

            result = await database.advance_rotation()
            await database.clear_votes(self.game_id, "early_exit")

            embed = embeds.rotation_advanced(result)
            await interaction.channel.send(embed=embed)
        else:
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(
                f"Vote recorded! ({count}/{config.EARLY_EXIT_VOTES})", ephemeral=True
            )

    async def on_timeout(self):
        _active_swap_views.pop(self.game_id, None)
        count = await database.get_vote_count(self.game_id, "early_exit")
        await database.clear_votes(self.game_id, "early_exit")
        if self.message:
            try:
                await self.message.edit(
                    content=(
                        f"⏰ Vote expired. {count}/{config.EARLY_EXIT_VOTES} votes — "
                        "threshold not met. Game stays!"
                    ),
                    view=None,
                )
            except Exception:
                pass


class RotationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="rotation", description="Show the current game rotation")
    async def rotation(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await database.refresh_cooldowns()

        active = await database.get_active()
        queue = await database.get_queue()
        bench = await database.get_bench()
        cooldown = await database.get_cooldown()

        embed = embeds.rotation_board(active, queue, bench, cooldown)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="advance", description="Advance to the next game in the rotation")
    async def advance(self, interaction: discord.Interaction):
        await interaction.response.defer()

        active = await database.get_active()
        if not active:
            await interaction.followup.send("No active game to advance from!")
            return

        result = await database.advance_rotation()
        await database.clear_votes(active["id"], "early_exit")
        _active_swap_views.pop(active["id"], None)

        embed = embeds.rotation_advanced(result)
        await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="propose-swap",
        description="Start a vote to swap out the current game",
    )
    async def propose_swap(self, interaction: discord.Interaction):
        await interaction.response.defer()

        active = await database.get_active()
        if not active:
            await interaction.followup.send("No active game to swap out!")
            return

        game_id = active["id"]

        if game_id in _active_swap_views:
            await interaction.followup.send(
                f"⚠️ There's already an active swap vote for **{active['name']}**!"
            )
            return

        session_count = active.get("session_count", 0)
        min_met = session_count >= config.MIN_SESSIONS

        embed = discord.Embed(
            title="🔄 Propose Swap",
            description=(
                f"Proposing to swap out **{active['name']}**\n"
                f"Sessions played: **{session_count}** "
                f"{'✅' if min_met else f'(min: {config.MIN_SESSIONS})'}\n\n"
                f"Need **{config.EARLY_EXIT_VOTES}** votes to advance."
                + (
                    ""
                    if min_met
                    else f"\n⚠️ This would be an early exit (before {config.MIN_SESSIONS} minimum sessions)."
                )
            ),
            color=discord.Color.orange(),
        )

        view = ProposeSwapView(self.bot, game_id, active["name"])
        msg = await interaction.followup.send(embed=embed, view=view)
        view.message = msg
        _active_swap_views[game_id] = view


async def setup(bot: commands.Bot):
    await bot.add_cog(RotationCog(bot))
