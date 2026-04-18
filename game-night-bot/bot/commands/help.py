import discord
from discord import app_commands
from discord.ext import commands


class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="help", description="Show all available commands")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎮 City Wok Game Night — All Da Command!",
            description=(
                "Listen up, you son of bitch! Dese awe da command for City Wok Game Night. "
                "You use dem or you git out!"
            ),
            color=discord.Color.gold(),
        )

        embed.add_field(
            name="🗓️ Da Lotation",
            value=(
                "`/rotation` — See who pwaying, who in queue, who on bench. Look at it!\n"
                "`/advance` — Move to da next game in da lotation. Do it!\n"
                "`/propose-swap` — Start a vote to swap out da current game. Need "
                f"enough vote or it no work, dammit."
            ),
            inline=False,
        )

        embed.add_field(
            name="🕹️ Da Bench",
            value=(
                "`/add-game` — Add a game to da bench. I check cwossplay first, you bettah wait!\n"
                "`/remove-game` — Retire a game flom da lotation. Git out, game!\n"
                "`/bench` — See all da bench game and vote 👍 for your favorite!"
            ),
            inline=False,
        )

        embed.add_field(
            name="📝 Da Session",
            value=(
                "`/log-session` — Wog tonight session after you done pwaying. Don't forget!\n"
                "`/history` — See da history book of all past session.\n"
                "`/stats` — See City Wok game stat. Very impwessive!"
            ),
            inline=False,
        )

        embed.add_field(
            name="🔔 Da Lemindel",
            value="`/send-reminder` — Manually send da Thulsday lemindel. In case you forget, son of bitch.",
            inline=False,
        )

        embed.set_footer(text="City Wok Game Night — Best game night in all of South Pawk!")

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))
