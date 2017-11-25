import discord
import string
from discord.ext import commands


class TextMojify:
    def __init__(self, bot):
        self.bot = bot
        textmoji_strs = '🅰🅱🇨🇩🇪🇫🇬🇭🇮🇯🇰🇱🇲🇳🅾🅿🇶🇷🇸🇹🇺🇻🇼🇽🇾🇿'
        self.textmoji_table = dict((ord(char), trans) for char, trans in zip(string.ascii_lowercase, textmoji_strs))

    @commands.command()
    async def textmojify(self, ctx, *, msg):
        """ Convert text into emojis """

        if msg is not None:
            text = msg.lower().translate(self.textmoji_table)
            await ctx.send(text)
        else:
            return await ctx.error('Please provide something to TextMojify.')


def setup(bot):
    bot.add_cog(TextMojify(bot))

