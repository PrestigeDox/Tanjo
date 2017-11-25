from __future__ import division
import discord
import asyncio
import random
import json
import win_unicode_console

win_unicode_console.enable()

from discord.ext import commands
from utils.calcparser import NumericStringParserForPython3


class Utilities:
    # Init with the bot reference, and a reference to the settings var
    def __init__(self, bot):
        self.bot = bot
        self.nsp = NumericStringParserForPython3()
        dev_server = discord.utils.find(lambda s: s.id == 365893884053553162, bot.guilds)
        self.feedback_channel = dev_server.get_channel(365893884053553162)

    @commands.command()
    async def esrever(self, ctx, *, msg: str = None):
        """ Write backwards because reasons, in Embed """

        e = discord.Embed(colour=self.bot.user_color)

        if msg is None:
            return await ctx.error('Write a message after command!')
        else:
            e.description = f'`{msg.lower()[::-1]}`    \N{LEFTWARDS BLACK ARROW}'

        try:
            await ctx.send(embed=e)
        except discord.HTTPException:
            return await ctx.error('Unable to send embeds here!')

    @commands.command(aliases=['tu'])
    async def tinyurl(self, ctx, *, link: str = None):
        """Shorten URLs"""

        if link is None:
            return await ctx.error('Please provide a link to shorten!')

        api_tiny = 'http://tinyurl.com/api-create.php?url='

        async with self.bot.session.get(api_tiny + link) as tiny:
            shortenurl = await tiny.read()

        shortenurl = shortenurl.decode("utf-8")

        emb = discord.Embed(colour=self.bot.user_color)
        emb.add_field(name="\U0001f30d Original Link",
                      value=link, inline=False)
        emb.add_field(name="\U0001f517 Shortened Link",
                      value=shortenurl, inline=False)

        await ctx.send(embed=emb)

    @commands.command(aliases=['calc', 'maths'])
    async def calculate(self, ctx, *, formula=None):
        """Python calculator command
        Usage: Add: 2+3, Sub: 2-3, Mul: 2*3, Div: 2/3, Exp: 2^3,
        Pi: PI, E: e, Sin: sin, Cos: cos, Tan: tan, Abs: abs,
        Tru: trunc, Rou: round, Sgn: sgn

        This command uses: Paul McGuire's fourFn.py."""
        u = ctx.message.author.display_name

        if formula is None:
            # How can it calculate an empty message? Reee!
            msg = f'\u200BUsage: `{ctx.prefix}{ctx.invoked_with} [any maths formula]`'
            e = discord.Embed(colour=self.bot.user_color)
            e.description = f'{msg}'
            try:
                await ctx.send(embed=e)
            except discord.HTTPException:
                return await ctx.error('Unable to send embeds here!')

        # Okay, so here it tries to solve the problem, so far it has received
        # some numbers and operators, it will try to parse the input into intelligeble
        # formulas and solve them...
        try:
            answer = self.nsp.eval(formula)

        except:
            # If there's a problem with the input, shows examples instead of hanging up
            e = discord.Embed(colour=self.bot.user_color)
            e.description = f'\u200B\N{THINKING FACE} wrong `{formula}` input {u}!.\n' \
                            f'Available operations:\n\n' \
                            f'**Add:** `2+3`, **Sub:** `2-3`, **Mul:** `2*3`, **Div:** `2/3`,\n' \
                            f'**Exp:** `2^3`, **Pi:** `PI`, **E:** `e`,\n' \
                            f'**Sin:** `sin()`, **Cos:** `cos()`, **Tan:** `tan()`, **Abs:** `abs()`,\n' \
                            f'**Tru:** `trunc()`, **Rou:** `round()`, **Sgn:** `sgn()`,\n' \
                            f'**Int:** `0 to 9`'
            try:
                await ctx.send(embed=e)
            except discord.HTTPException:
                return await ctx.error('Unable to send embeds here!')

        # If we made it here, then the correct input prints correct answer
        # everything else was just to make sure the input was somewhat logical
        e = discord.Embed(colour=self.bot.user_color)
        e.add_field(name='Input:', value=f'```{formula}```', inline=True)
        e.add_field(name='Result:', value=f'```{round(answer, 2)}```', inline=True)
        try:
            await ctx.send(embed=e)
        except discord.HTTPException:
            return await ctx.error('Unable to send embeds here!')

    @commands.command(aliases=['suggestion'])
    async def feedback(self, ctx, *, text: str = 'Sorry, forgot to write.'):
        """Suggestions and feature requests"""

        user = ctx.message.author
        c = ctx.invoked_with

        e = discord.Embed(colour=self.bot.user_color)
        e.title = 'Feedback'
        e.set_author(name=f'{user.name}{user.discriminator}', icon_url=user.avatar_url)
        e.description = f'{text}'

        try:
            await self.feedback_channel.send(embed=e)
            await ctx.send(f'Feedback received successfully. Thank you!')
        except discord.Forbidden:
            return await ctx.error('Unable to send feedback, please join Support Server\nhttps://discord.gg/9qgzkQV')


    @commands.command(aliases=['prediction', 'crystalball', 'oracle', 'i-ching', 'fortune'])
    async def iching(self, ctx, *, member: discord.Member = None):
        """Based on the ancient I Ching oracle,
        `Usage: command [member]>`
        use it as a guide"""

        ich = await ctx.send('Tossing 3 antique coins for your result.')
        await asyncio.sleep(2)

        with open('data/oracle.json') as f:
            choices = json.load(f)

        iching = 'http://i.imgur.com/biEvXBN.png'
        m = member or ctx.author
        p = ctx.invoked_with.title()

        e = discord.Embed(colour=self.bot.user_color)
        e.set_thumbnail(url=iching)
        e.set_footer(text="+-<§) Ancient Oracle's wisdom interpreted for now (§>-+")
        e.set_author(name=f"{p}'s inspiration for: {m.display_name} | {m}", icon_url=ctx.message.author.avatar_url)
        e.description = f'Meditation:\n{random.choice(choices)}'

        try:
            await ich.edit(embed=e, content=None)
        except discord.HTTPException:
            return await ctx.error('Unable to send embeds here!')


def setup(bot):
    bot.add_cog(Utilities(bot))
