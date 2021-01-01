import discord
import json
from discord.ext import commands

class AdminCmd(commands.Cog):
    def __init__(self,client):
        self.client=client
    
    @commands.Cog.listener()
    async def on_ready(self):
        pass
    
    # Returns the top favorite songs in a server
    @commands.command(pass_context=True)
    @commands.has_permissions(administrator=True)
    async def topFavoriteSongs(self, ctx):
        print("bye")
        id = ctx.message.guild.id
        try:
            with open("metrics.json") as metricsFile:
                metrics = json.load(metricsFile,)
    
            metricsFile.close()
        except Exception as e:
            print("Error: Failed to open metrics.json.")
            print(e)

        print("hi")
 
    @commands.command(pass_context=True)
    @commands.has_permissions(administrator=True)
    async def leave(self,ctx):
        await ctx.message.guild.voice_client.disconnect()

    #joins voice channel  needs PyNaCL to function
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def join(self,ctx):
        guild = ctx.message.author.voice.channel
        
        await guild.connect()

    #puges test in channel command invoke
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx):
        await ctx.channel.purge()
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def quit(self, ctx):
        await self.client.logout()
        await self.client.close()
        
    @commands.command()
    async def kick(self, ctx, member : discord.Member):
        await  member.kick()

    @commands.command()
    async def ban(self, ctx, member : discord.Member):
        await  member.ban()
        await ctx.send(f'Banned {member.mention}')

    @commands.command()
    async def unban(self, ctx, *, member):
        banned_users = await ctx.guild.bans()
        member_name, member_discriminator = member.split('#')

        for ban_entry in banned_users:
            user = ban_entry.user

            if(user.name, user.discriminator) == (member_name,member_discriminator):
                await ctx.guild.unban(user)
                await ctx.send(f'Unbanned {user.mention}')
                return
    

def setup(client):
    print("Setting up commands")
    client.add_cog(AdminCmd(client))