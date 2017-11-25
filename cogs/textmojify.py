import discord
import string
from discord.ext import commands


class TextMojify:
    def __init__(self, bot):
        self.bot = bot
        textmoji_strs = '🅰🅱🇨🇩🇪🇫🇬🇭🇮🇯🇰🇱🇲🇳🅾🅿🇶🇷🇸🇹🇺🇻🇼🇽🇾🇿'
        self.textmoji_table = dict((ord(char), trans) for char, trans in zip(string.ascii_lowercase, textmoji_strs))

    @commands.command()
    async def textmojify(self, ctx, *, emb: str=None, msg):
        """ Convert text into emojis
        supports plain output, or embed
        Usage: <textmojify> [emb] message to convert """
        if emb is None:
            if msg is not None:
                text = msg.lower().translate(self.textmoji_table)
                await ctx.send(text)
            else:
                return await ctx.error('Please provide something for me to *TextMojify* it!.', delete_after=3.0)

        if emb is str:
            out = msg.lower()
            text = out.replace(' ', '    ')\
                .replace('10', '\u200B\N{KEYCAP TEN}') \
                .replace('ab', '\u200B🆎').replace('cl', '\u200B🆑') \
                .replace('0', '\u200B0\N{COMBINING ENCLOSING KEYCAP}') \
                .replace('1', '\u200B1\N{COMBINING ENCLOSING KEYCAP}') \
                .replace('2', '\u200B2\N{COMBINING ENCLOSING KEYCAP}') \
                .replace('3', '\u200B3\N{COMBINING ENCLOSING KEYCAP}') \
                .replace('4', '\u200B4\N{COMBINING ENCLOSING KEYCAP}') \
                .replace('5', '\u200B5\N{COMBINING ENCLOSING KEYCAP}') \
                .replace('6', '\u200B6\N{COMBINING ENCLOSING KEYCAP}') \
                .replace('7', '\u200B7\N{COMBINING ENCLOSING KEYCAP}') \
                .replace('8', '\u200B8\N{COMBINING ENCLOSING KEYCAP}') \
                .replace('9', '\u200B9\N{COMBINING ENCLOSING KEYCAP}') \
                .replace('!', '\u200B❗')\
                .replace('?', '\u200B❓') \
                .replace('vs', '\u200B🆚')\
                .replace('.', '\u200B🔸') \
                .replace(',', '🔻')\
                .replace('a', '\u200B🅰') \
                .replace('b', '\u200B🅱').replace('c', '\u200B🇨') \
                .replace('d', '\u200B🇩').replace('e', '\u200B🇪') \
                .replace('f', '\u200B🇫').replace('g', '\u200B🇬') \
                .replace('h', '\u200B🇭').replace('i', '\u200B🇮') \
                .replace('j', '\u200B🇯').replace('k', '\u200B🇰') \
                .replace('l', '\u200B🇱').replace('m', '\u200B🇲') \
                .replace('n', '\u200B🇳').replace('ñ', '\u200B🇳') \
                .replace('o', '\u200B🅾').replace('p', '\u200B🅿') \
                .replace('q', '\u200B🇶').replace('r', '\u200B🇷') \
                .replace('s', '\u200B🇸').replace('t', '\u200B🇹') \
                .replace('u', '\u200B🇺').replace('v', '\u200B🇻') \
                .replace('w', '\u200B🇼').replace('x', '\u200B🇽') \
                .replace('y', '\u200B🇾').replace('z', '\u200B🇿')

            try:
                m = ctx.message.author
                e = discord.Embed(colour=self.bot.user_color)
                # e.set_thumbnail(url=)
                e.set_author(name=f"{m.display_name}'s message", icon_url=m.avatar_url)
                e.description = text

            except discord.HTTPException:
                text = msg.lower().translate(self.textmoji_table)
                await ctx.send(text)

            else:
                return await ctx.error('Please provide something for me to *TextMojify* it!.', delete_after=3.0)


def setup(bot):
    bot.add_cog(TextMojify(bot))

