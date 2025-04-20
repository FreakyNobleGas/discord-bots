from discord.ext import commands

class Notifications(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('Notifications ready')

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel is None and len(after.channel.members) == 1:
            await after.channel.send(f'{str(member).capitalize()} joined {after.channel.name}')

async def setup(bot):
    await bot.add_cog(Notifications(bot))
