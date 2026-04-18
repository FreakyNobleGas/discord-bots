import logging

import discord
from discord import app_commands
from discord.ext import commands

from bot import config, database
from bot.scheduler import _send_thursday_reminder
from bot.utils import embeds

logger = logging.getLogger(__name__)

# Tracks active propose-swap views by game_id so we don't double-post
_active_swap_views: dict[int, "ProposeSwapView"] = {}


class ProposeSwapView(discord.ui.View):
    def __init__(self, bot: commands.Bot, game_id: int, game_name: str):
        super().__init__(timeout=config.VOTE_WINDOW_HOURS * 3600)
        self.bot = bot
        self.game_id = game_id
        self.game_name = game_name
        self.message: discord.Message | None = None

    @discord.ui.button(label="✅ Move On! (0)", style=discord.ButtonStyle.green)
    async def vote_advance(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await database.has_voted(self.game_id, "early_exit", str(interaction.user.id)):
            await interaction.response.send_message("You aweady vote, I see you!", ephemeral=True)
            return

        await database.add_vote(self.game_id, "early_exit", str(interaction.user.id))
        count = await database.get_vote_count(self.game_id, "early_exit")
        button.label = f"✅ Move On! ({count}/{config.EARLY_EXIT_VOTES})"

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
                f"I count you vote! ({count}/{config.EARLY_EXIT_VOTES}), keep going!", ephemeral=True
            )

    async def on_timeout(self):
        _active_swap_views.pop(self.game_id, None)
        count = await database.get_vote_count(self.game_id, "early_exit")
        await database.clear_votes(self.game_id, "early_exit")
        if self.message:
            try:
                await self.message.edit(
                    content=(
                        f"⏰ Time up! {count}/{config.EARLY_EXIT_VOTES} vote — "
                        "not enough, game stay. Dammit!"
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
        result = await database.advance_rotation()

        if active:
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
            await interaction.followup.send("No game even pwaying! What you doing?")
            return

        game_id = active["id"]

        if game_id in _active_swap_views:
            await interaction.followup.send(
                f"⚠️ Aweady a vote going on for **{active['name']}**! Patience!"
            )
            return

        session_count = active.get("session_count", 0)
        min_met = session_count >= config.MIN_SESSIONS

        embed = discord.Embed(
            title="🔄 You Want Switch Game?",
            description=(
                f"Pwoposing to swap out **{active['name']}**\n"
                f"Session pwayed: **{session_count}** "
                f"{'✅' if min_met else f'(min: {config.MIN_SESSIONS})'}\n\n"
                f"Need **{config.EARLY_EXIT_VOTES}** vote to advance."
                + (
                    ""
                    if min_met
                    else f"\n⚠️ Dis would be eawly exit (before {config.MIN_SESSIONS} minimum session). You bettah be sure!"
                )
            ),
            color=discord.Color.orange(),
        )

        view = ProposeSwapView(self.bot, game_id, active["name"])
        msg = await interaction.followup.send(embed=embed, view=view)
        view.message = msg
        _active_swap_views[game_id] = view


    @app_commands.command(name="send-reminder", description="Manually trigger the Thursday night reminder")
    async def send_reminder(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await _send_thursday_reminder(self.bot)
        await interaction.followup.send("I send da lemindel, you bettah show up!", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(RotationCog(bot))
