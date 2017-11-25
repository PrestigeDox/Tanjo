import discord
import random
from discord.ext import commands

class Hexa:
    def __init__(self, bot):
        self.bot = bot
        self.reply = ['Your lucky', "Today's", 'Your random', 'Your generated', 'For you this', 'Got this']


    @commands.command(description="A random number from 1 to 100")
    async def hexa(self, ctx):
        """ Get a random number from 1 to 100 """
        u = ctx.message.author.display_name
        e = discord.Embed(colour=self.bot.user_color)
        e.add_field(name=f"{u}'s hexa:", value=msg)
        try:
            await ctx.send(embed=e)
        except discord.HTTPException:
            return await ctx.error(f'{random.choice(self.reply)} number between 1 and 100: **`{random.randint(1, 99)}`**')


def setup(bot):
    bot.add_cog(Hexa(bot))
