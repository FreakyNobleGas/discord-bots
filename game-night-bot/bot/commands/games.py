import logging

import discord
from discord import app_commands
from discord.ext import commands

from bot import database, enrichment
from bot.utils import embeds

logger = logging.getLogger(__name__)


async def _game_name_autocomplete(
    interaction: discord.Interaction, current: str
) -> list[app_commands.Choice[str]]:
    if len(current) < 2:
        return []
    try:
        matches = await enrichment.search_rawg(current, limit=5)
    except Exception:
        matches = []
    choices = [
        app_commands.Choice(
            name=f"{m['name']} ({(m['released'] or '')[:4]})"[:100],
            value=str(m["id"]),
        )
        for m in matches
    ]
    choices.append(
        app_commands.Choice(
            name="✏️ None of dese, I add myself",
            value=f"manual:{current}",
        )
    )
    return choices


async def _rotation_game_autocomplete(
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


class ManualAddView(discord.ui.View):
    """Simple confirm/cancel for games not found on RAWG."""

    def __init__(self, game_name: str, added_by: str, guild_id: int):
        super().__init__(timeout=120)
        self.game_name = game_name
        self.added_by = added_by
        self.guild_id = guild_id

    @discord.ui.button(label="✅ Yes, add it!", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)

        await database.add_game(
            guild_id=self.guild_id,
            name=self.game_name,
            rawg_id=None,
            rawg_slug=None,
            cover_url="",
            genre_tags=[],
            added_by=self.added_by,
        )

        await interaction.edit_original_response(
            content=None,
            embed=discord.Embed(
                title=f"🎮 {self.game_name} — Added to Lotation!",
                description="Add manually by City Wok. No cover art, no genre. You happy now?",
                color=discord.Color.green(),
            ),
            view=None,
        )
        self.stop()

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(
            content=f"❌ **{self.game_name}** not added. Git out!",
            view=None,
        )
        self.stop()


class GamesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="rotation", description="Show the current game rotation")
    async def rotation(self, interaction: discord.Interaction):
        await interaction.response.defer()
        games = await database.get_game_stats(interaction.guild_id)
        embed = embeds.rotation_board(games)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="add-game", description="Add a game to the rotation")
    @app_commands.describe(name="Search for a game — pick from the dropdown for best results")
    @app_commands.autocomplete(name=_game_name_autocomplete)
    async def add_game(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer()
        guild_id = interaction.guild_id

        # "None of these" selected from autocomplete
        if name.startswith("manual:"):
            game_name = name[len("manual:"):]
            view = ManualAddView(game_name=game_name, added_by=interaction.user.name, guild_id=guild_id)
            await interaction.followup.send(
                content=f"Add **{game_name}** to da lotation?",
                view=view,
            )
            return

        # User selected a RAWG match from autocomplete
        if name.isdigit():
            try:
                game_data = await enrichment.get_rawg_game_by_id(int(name))
            except Exception as exc:
                logger.error("RAWG fetch by ID failed: %s", exc)
                await interaction.followup.send(f"❌ Could not fetch game flom RAWG: {exc}")
                return

            if await database.game_exists_by_rawg_id(guild_id, game_data["id"]):
                await interaction.followup.send(
                    f"⚠️ **{game_data['name']}** aweady in da lotation!"
                )
                return

            await database.add_game(
                guild_id=guild_id,
                name=game_data["name"],
                rawg_id=game_data["id"],
                rawg_slug=game_data["slug"],
                cover_url=game_data["cover_url"],
                genre_tags=game_data["genres"],
                added_by=interaction.user.name,
            )
            await interaction.followup.send(embed=embeds.game_added(game_data))
            return

        # Typed text without picking from autocomplete — search and show results
        try:
            matches = await enrichment.search_rawg(name, limit=5)
        except Exception as exc:
            logger.error("RAWG search error: %s", exc)
            await interaction.followup.send(f"❌ Could not weach RAWG API: {exc}")
            return

        if not matches:
            view = ManualAddView(game_name=name, added_by=interaction.user.name, guild_id=guild_id)
            await interaction.followup.send(
                content=f"**{name}** not in RAWG. Add it manually?",
                view=view,
            )
            return

        # Show search results embed and prompt them to use the autocomplete
        embed = embeds.rawg_matches(matches, name)
        embed.set_footer(text="Tip: Use the autocomplete dropdown when typing for a faster flow!")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="remove-game", description="Remove a game from the rotation")
    @app_commands.describe(name="The game to remove")
    @app_commands.autocomplete(name=_rotation_game_autocomplete)
    async def remove_game(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer()
        guild_id = interaction.guild_id

        game = await database.get_game_by_id(guild_id, int(name)) if name.isdigit() else None
        if not game:
            await interaction.followup.send(f"Dat game not found, son of bitch!")
            return

        await database.remove_game(guild_id, game["id"])
        await interaction.followup.send(
            embed=discord.Embed(
                title="🗑️ Game Removed",
                description=f"**{game['name']}** has been removed flom da lotation.",
                color=discord.Color.red(),
            )
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(GamesCog(bot))
