import asyncio
import logging

import discord
from discord import app_commands
from discord.ext import commands

from bot import config, database, enrichment
from bot.utils import embeds

logger = logging.getLogger(__name__)

_THINKING_FRAMES = [
    "🌐 Searching the web...",
    "🔍 Reading sources...",
    "🤔 Analyzing crossplay support...",
    "⏳ Checking Xbox & PC compatibility...",
]


async def _animate_thinking(interaction: discord.Interaction, stop: asyncio.Event):
    """Cycle through status messages every 3s until stop is set."""
    for i in range(len(_THINKING_FRAMES) * 3):  # cap iterations
        await asyncio.sleep(3)
        if stop.is_set():
            return
        try:
            await interaction.edit_original_response(
                content=_THINKING_FRAMES[i % len(_THINKING_FRAMES)]
            )
        except Exception:
            return


def _check_genre_warning(queue_genres: list[str]) -> str | None:
    """Return a warning string if 3+ consecutive queue games share the same primary genre."""
    if len(queue_genres) < 3:
        return None
    for i in range(len(queue_genres) - 2):
        a, b, c = queue_genres[i], queue_genres[i + 1], queue_genres[i + 2]
        if a.lower() == b.lower() == c.lower():
            return (
                f"⚠️ Heads up — the next 3 games in queue are all **{a}**. "
                "Worth mixing it up?"
            )
    return None


class RAWGMatchView(discord.ui.View):
    """Ephemeral select-menu for picking the correct RAWG match."""

    def __init__(self, matches: list[dict], added_by: str):
        super().__init__(timeout=120)
        self.matches = matches
        self.added_by = added_by

        options = []
        for m in matches:
            year = (m.get("released") or "")[:4]
            label = f"{m['name'][:80]} ({year})" if year else m["name"][:100]
            options.append(
                discord.SelectOption(
                    label=label,
                    value=str(m["id"]),
                    description=(", ".join(m["genres"][:3])[:100]) if m["genres"] else "No genres",
                )
            )

        self._select = discord.ui.Select(
            placeholder="Pick the correct game...",
            options=options,
        )
        self._select.callback = self._on_select
        self.add_item(self._select)

    async def _on_select(self, interaction: discord.Interaction):
        chosen_id = int(self._select.values[0])
        game_data = next(m for m in self.matches if m["id"] == chosen_id)

        self._select.disabled = True
        await interaction.response.edit_message(
            content=_THINKING_FRAMES[0],
            embed=None,
            view=self,
        )

        # Duplicate check
        if await database.game_exists_by_rawg_id(game_data["id"]):
            await interaction.edit_original_response(
                content=f"⚠️ **{game_data['name']}** is already in the system!",
                view=None,
            )
            return

        # Claude crossplay check with animated status
        stop = asyncio.Event()
        animation = asyncio.create_task(_animate_thinking(interaction, stop))
        try:
            result = await enrichment.check_crossplay(game_data)
        except Exception as exc:
            logger.error("Crossplay check failed for %s: %s", game_data["name"], exc)
            stop.set()
            animation.cancel()
            await interaction.edit_original_response(
                content=f"❌ Could not verify crossplay status: {exc}",
                view=None,
            )
            return
        finally:
            stop.set()
            animation.cancel()

        crossplay = result.get("crossplay", False)
        confidence = result.get("confidence", "low")

        if not crossplay:
            embed = embeds.crossplay_rejected(game_data, result)
            await interaction.edit_original_response(content=None, embed=embed, view=None)
            return

        # Persist
        await database.add_game(
            name=game_data["name"],
            rawg_id=game_data["id"],
            rawg_slug=game_data["slug"],
            cover_url=game_data["cover_url"],
            genre_tags=game_data["genres"],
            crossplay_verified=True,
            crossplay_confidence=confidence,
            crossplay_source=result.get("source", ""),
            added_by=self.added_by,
        )

        embed = embeds.game_added(game_data, result, confidence)
        await interaction.edit_original_response(content=None, embed=embed, view=None)

        # Post public follow-ups
        if confidence in ("medium", "low"):
            await interaction.channel.send(
                f"⚠️ Claude wasn't fully confident on crossplay for **{game_data['name']}** "
                f"({confidence} confidence) — someone double-check before we queue this up!"
            )

        queue_genres = await database.get_queue_genres()
        warning = _check_genre_warning(queue_genres)
        if warning:
            await interaction.channel.send(warning)


class BenchVoteButton(discord.ui.Button):
    def __init__(self, game_id: int, game_name: str, vote_count: int):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label=f"👍 {game_name[:20]} ({vote_count})",
            custom_id=f"bench_vote_{game_id}",
        )
        self.game_id = game_id
        self.game_name = game_name

    async def callback(self, interaction: discord.Interaction):
        voted = await database.add_vote(self.game_id, "bench_up", str(interaction.user.id))
        if voted:
            new_count = await database.get_vote_count(self.game_id, "bench_up")
            self.label = f"👍 {self.game_name[:20]} ({new_count})"
            await interaction.response.edit_message(view=self.view)
            await interaction.followup.send(
                f"Voted for **{self.game_name}**!", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "You've already voted for this game!", ephemeral=True
            )


class BenchView(discord.ui.View):
    def __init__(self, bench_games: list[dict]):
        super().__init__(timeout=300)
        for game in bench_games[:25]:  # Discord component limit
            self.add_item(
                BenchVoteButton(game["id"], game["name"], game.get("vote_count", 0))
            )


class GamesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="add-game", description="Add a game to the rotation bench")
    @app_commands.describe(name="Name of the game to search for")
    async def add_game(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer()

        try:
            matches = await enrichment.search_rawg(name)
        except Exception as exc:
            logger.error("RAWG search error: %s", exc)
            await interaction.followup.send(f"❌ Could not reach RAWG API: {exc}")
            return

        if not matches:
            await interaction.followup.send(
                f"No games found matching **{name}**. Try a more specific search term."
            )
            return

        embed = embeds.rawg_matches(matches, name)
        view = RAWGMatchView(matches=matches, added_by=interaction.user.name)
        await interaction.followup.send(embed=embed, view=view)

    @app_commands.command(name="remove-game", description="Retire a game from the rotation")
    @app_commands.describe(name="Full or partial name of the game to retire")
    async def remove_game(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer()

        matches = await database.find_games_by_name(name)
        if not matches:
            await interaction.followup.send(f"No game found matching **{name}**.")
            return

        game = matches[0]
        await database.retire_game(game["id"])
        await interaction.followup.send(
            embed=discord.Embed(
                title="🗑️ Game Retired",
                description=f"**{game['name']}** has been removed from the rotation.",
                color=discord.Color.red(),
            )
        )

    @app_commands.command(name="bench", description="View bench games and upvote for queue priority")
    async def bench(self, interaction: discord.Interaction):
        await interaction.response.defer()

        bench_games = await database.get_bench()
        if not bench_games:
            await interaction.followup.send(
                "The bench is empty! Use `/add-game` to add games."
            )
            return

        embed = embeds.bench_list(bench_games)
        view = BenchView(bench_games)
        await interaction.followup.send(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(GamesCog(bot))
