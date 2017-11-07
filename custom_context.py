import discord
from discord.ext import commands


class TanjoContext(commands.Context):
    async def error(self, err: str, delete_after=None):
        em = discord.Embed(title=':x: Error',
                           color=discord.Color.dark_red(),
                           description=err.format())

        await self.message.edit(embed=em, delete_after=delete_after)
        
    async def reply(self):
        """ replies with mention """
        await ctx.send(
