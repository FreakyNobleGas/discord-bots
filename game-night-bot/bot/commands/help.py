import discord
from discord import app_commands
from discord.ext import commands

from bot.locale import t


class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="help", description="Show all available commands")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=t("help_title"),
            description=t("help_description"),
            color=discord.Color.gold(),
        )

        embed.add_field(
            name=t("help_rotation_field_name"),
            value=t("help_rotation_field_value"),
            inline=False,
        )

        embed.add_field(
            name=t("help_session_field_name"),
            value=t("help_session_field_value"),
            inline=False,
        )

        embed.set_footer(text=t("help_footer"))
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))
