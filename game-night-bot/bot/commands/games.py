import asyncio
import logging

import discord
from discord import app_commands
from discord.ext import commands

from bot import config, database, enrichment
from bot.utils import embeds

logger = logging.getLogger(__name__)

_THINKING_FRAMES = [
    "🌐 I checking da intewnet...",
    "🔍 I wead da soulce...",
    "🤔 I figure out da cwossplay...",
    "⏳ Almost done, you son of bitch...",
]


async def _animate_thinking(interaction: discord.Interaction, stop: asyncio.Event):
    """Cycle through status messages on the original response every 3s until stop is set."""
    for i in range(len(_THINKING_FRAMES) * 3):
        await asyncio.sleep(3)
        if stop.is_set():
            return
        try:
            await interaction.edit_original_response(
                content=_THINKING_FRAMES[i % len(_THINKING_FRAMES)]
            )
        except Exception:
            return


async def _animate_message(msg: discord.Message, stop: asyncio.Event):
    """Cycle through status messages on a specific message every 3s until stop is set."""
    for i in range(len(_THINKING_FRAMES) * 3):
        await asyncio.sleep(3)
        if stop.is_set():
            return
        try:
            await msg.edit(content=_THINKING_FRAMES[i % len(_THINKING_FRAMES)])
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
                f"⚠️ Hey! Next 3 game all **{a}**! You son of bitch, mix it up!"
            )
    return None


async def _run_enrichment_on_message(
    msg: discord.Message,
    channel: discord.TextChannel,
    game_data: dict,
    added_by: str,
):
    """Run the Claude crossplay check and update `msg` with the result."""
    stop = asyncio.Event()
    animation = asyncio.create_task(_animate_message(msg, stop))
    try:
        result = await enrichment.check_crossplay(game_data)
    except Exception as exc:
        logger.error("Crossplay check failed for %s: %s", game_data["name"], exc)
        stop.set()
        animation.cancel()
        await msg.edit(content=f"❌ Could not velify cwossplay: {exc}")
        return
    finally:
        stop.set()
        animation.cancel()

    crossplay = result.get("crossplay", False)
    confidence = result.get("confidence", "low")

    if not crossplay:
        embed = embeds.crossplay_rejected(game_data, result)
        await msg.edit(content=None, embed=embed)
        return

    await database.add_game(
        name=game_data["name"],
        rawg_id=game_data["id"],
        rawg_slug=game_data["slug"],
        cover_url=game_data["cover_url"],
        genre_tags=game_data["genres"],
        crossplay_verified=True,
        crossplay_confidence=confidence,
        crossplay_source=result.get("source", ""),
        added_by=added_by,
    )

    embed = embeds.game_added(game_data, result, confidence)
    await msg.edit(content=None, embed=embed)

    if confidence in ("medium", "low"):
        await channel.send(
            f"⚠️ Claude not sure about cwossplay for **{game_data['name']}** "
            f"({confidence} confidence) — somebody check dis, dammit!"
        )

    queue_genres = await database.get_queue_genres()
    warning = _check_genre_warning(queue_genres)
    if warning:
        await channel.send(warning)


class RAWGMatchView(discord.ui.View):
    """Fallback select-menu for picking the correct RAWG match (used when no autocomplete selection was made)."""

    def __init__(self, matches: list[dict], added_by: str, search_term: str):
        super().__init__(timeout=120)
        self.matches = matches
        self.added_by = added_by
        self.search_term = search_term

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

        options.append(
            discord.SelectOption(
                label="None of dese, I add myself",
                value="manual",
                description="Game not in dere? No pwoblem, I handle it.",
                emoji="✏️",
            )
        )

        self._select = discord.ui.Select(
            placeholder="Pick the correct game...",
            options=options,
        )
        self._select.callback = self._on_select
        self.add_item(self._select)

    async def _on_select(self, interaction: discord.Interaction):
        if self._select.values[0] == "manual":
            view = ManualAddView(game_name=self.search_term, added_by=self.added_by)
            await interaction.response.edit_message(
                content=f"Does **{self.search_term}** support Xbox ↔ PC cwossplay?",
                embed=None,
                view=view,
            )
            return

        chosen_id = int(self._select.values[0])
        game_data = next(m for m in self.matches if m["id"] == chosen_id)

        self._select.disabled = True
        await interaction.response.edit_message(
            content=_THINKING_FRAMES[0],
            embed=None,
            view=self,
        )

        if await database.game_exists_by_rawg_id(game_data["id"]):
            await interaction.edit_original_response(
                content=f"⚠️ **{game_data['name']}** aweady in da system!",
                view=None,
            )
            return

        stop = asyncio.Event()
        animation = asyncio.create_task(_animate_thinking(interaction, stop))
        try:
            result = await enrichment.check_crossplay(game_data)
        except Exception as exc:
            logger.error("Crossplay check failed for %s: %s", game_data["name"], exc)
            stop.set()
            animation.cancel()
            await interaction.edit_original_response(
                content=f"❌ Could not velify cwossplay: {exc}",
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

        if confidence in ("medium", "low"):
            await interaction.channel.send(
                f"⚠️ Claude not sure about cwossplay for **{game_data['name']}** "
                f"({confidence} confidence) — somebody check dis, dammit!"
            )

        queue_genres = await database.get_queue_genres()
        warning = _check_genre_warning(queue_genres)
        if warning:
            await interaction.channel.send(warning)


class ManualAddView(discord.ui.View):
    """Shown when a game isn't found on RAWG — lets the user confirm crossplay and add manually."""

    def __init__(self, game_name: str, added_by: str):
        super().__init__(timeout=120)
        self.game_name = game_name
        self.added_by = added_by

    @discord.ui.button(label="✅ Yes! Cwossplay work!", style=discord.ButtonStyle.green)
    async def confirm_crossplay(self, interaction: discord.Interaction, button: discord.ui.Button):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)

        await database.add_game(
            name=self.game_name,
            rawg_id=None,
            rawg_slug=None,
            cover_url="",
            genre_tags=[],
            crossplay_verified=True,
            crossplay_confidence="high",
            crossplay_source="Manually confirmed by user",
            added_by=self.added_by,
        )

        await interaction.edit_original_response(
            content=None,
            embed=discord.Embed(
                title=f"🎮 {self.game_name} — On Da Bench Now, Git!",
                description="Add manually by City Wok. No cover art, no genre. You happy now?",
                color=discord.Color.green(),
            ),
            view=None,
        )
        self.stop()

    @discord.ui.button(label="❌ No cwossplay, git out!", style=discord.ButtonStyle.red)
    async def deny_crossplay(self, interaction: discord.Interaction, button: discord.ui.Button):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(
            content=f"❌ **{self.game_name}** not added — no Xbox ↔ PC cwossplay. Git out!",
            view=None,
        )
        self.stop()


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
        for game in bench_games[:25]:
            self.add_item(
                BenchVoteButton(game["id"], game["name"], game.get("vote_count", 0))
            )


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


class GamesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="add-game", description="Add a game to the rotation bench")
    @app_commands.describe(name="Search for a game — pick from the dropdown for best results")
    @app_commands.autocomplete(name=_game_name_autocomplete)
    async def add_game(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer()

        # "None of these" selected from autocomplete
        if name.startswith("manual:"):
            game_name = name[len("manual:"):]
            view = ManualAddView(game_name=game_name, added_by=interaction.user.name)
            await interaction.followup.send(
                content=f"Does **{game_name}** support Xbox ↔ PC cwossplay?",
                view=view,
            )
            return

        # If the user selected a match from autocomplete, name is the RAWG ID
        if name.isdigit():
            try:
                game_data = await enrichment.get_rawg_game_by_id(int(name))
            except Exception as exc:
                logger.error("RAWG fetch by ID failed: %s", exc)
                await interaction.followup.send(f"❌ Could not fetch game from RAWG: {exc}")
                return

            if await database.game_exists_by_rawg_id(game_data["id"]):
                await interaction.followup.send(
                    f"⚠️ **{game_data['name']}** aweady in da system!"
                )
                return

            msg = await interaction.followup.send(content=_THINKING_FRAMES[0])
            await _run_enrichment_on_message(msg, interaction.channel, game_data, interaction.user.name)

        # Otherwise fall back to search + select menu
        else:
            try:
                matches = await enrichment.search_rawg(name, limit=5)
            except Exception as exc:
                logger.error("RAWG search error: %s", exc)
                await interaction.followup.send(f"❌ Could not reach RAWG API: {exc}")
                return

            if not matches:
                view = ManualAddView(game_name=name, added_by=interaction.user.name)
                await interaction.followup.send(
                    content=f"**{name}** not in RAWG. Does it support Xbox ↔ PC cwossplay?",
                    view=view,
                )
                return

            embed = embeds.rawg_matches(matches, name)
            view = RAWGMatchView(matches=matches, added_by=interaction.user.name, search_term=name)
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
                "Da bench empty! Use `/add-game`, you son of bitch!"
            )
            return

        embed = embeds.bench_list(bench_games)
        view = BenchView(bench_games)
        await interaction.followup.send(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(GamesCog(bot))
