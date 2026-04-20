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
                "`/rotation` — See all da game, when dey last pwayed, and how many session.\n"
                "`/add-game` — Add a game to da lotation. Pick flom da list!\n"
                "`/remove-game` — Remove a game flom da lotation. Git out, game!"
            ),
            inline=False,
        )

        embed.add_field(
            name="📝 Da Session",
            value="`/log-session` — Log a session for da game you pwayed tonight. Don't forget!",
            inline=False,
        )

        embed.add_field(
            name="🔔 Da Lemindel",
            value="`/send-reminder` — Manually send da Thulsday lemindel with da voting poll.",
            inline=False,
        )

        embed.set_footer(text="City Wok Game Night — Best game night in all of South Pawk!")
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))
