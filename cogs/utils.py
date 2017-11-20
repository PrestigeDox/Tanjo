from __future__ import division
import discord
import asyncio
import random
import json
import urbandictionary as ud
import string
import win_unicode_console

win_unicode_console.enable()

from bs4 import BeautifulSoup
from discord.ext import commands
from utils.calcparser import NumericStringParserForPython3


class Utilities:
    # Init with the bot reference, and a reference to the settings var
    def __init__(self, bot):
        self.bot = bot
        self.nsp = NumericStringParserForPython3()
        textmoji_strs = '\u200B🅰\u200B🅱\u200B🇨\u200B🇩\u200B🇪\u200B🇫\u200B🇬' \
                        '\u200B🇭\u200B🇮\u200B🇯\u200B🇰\u200B🇱\u200B🇲\u200B🇳' \
                        '\u200B🅾\u200B🅿\u200B🇶\u200B🇷\u200B🇸\u200B🇹\u200B🇺' \
                        '\u200B🇻\u200B🇼\u200B🇽\u200B🇾\u200B🇿'
        self.textmoji_table = dict((ord(char), trans) for char, trans in zip(string.ascii_letters, textmoji_strs))
        dev_server = discord.utils.find(lambda s: s.id == 365893884053553162, bot.servers)
        self.feedback_channel = dev_server.get_channel(365893884053553162)
        self.guessed_wrong = [
                'Not even close, the right number was:',
                'Better luck next time, the number was:',
                'How could you not have known that the number was:',
                'Hmm, well, the right number was:',
                'Not getting any better, the number was:',
                'Right number was:'
                 ]
        self.guessed_right = [
                'You guessed correctly',
                'Everyone knew you could do it',
                'You got the right answer',
                'History will remember you...'
            ]
        self.RPSLS = {'rock': "\N{RAISED FIST} **Rock!**",
                      'paper': "\N{RAISED HAND WITH FINGERS SPLAYED} **Paper!**",
                      'scissors': "\N{BLACK SCISSORS} **Scissors!**",
                      'lizard': "\N{LIZARD} **Lizard!**",
                      'spock': "\N{RAISED HAND WITH PART BETWEEN MIDDLE AND RING FINGERS} **Spock!**"}

    @commands.command(aliases=['yt', 'vid'])
    async def video(self, ctx, *, search):
        """ Search for the first videos match on YouTube """

        with await ctx.channel.typing():
            search = search.replace(' ', '+').lower()

            with await self.bot.session.get(f"https://www.youtube.com/results?search_query={search}") as resp:
                response = await resp.text()

            result = BeautifulSoup(response, "lxml")
            dir_address = f"{result.find_all(attrs={'class': 'yt-uix-tile-link'})[0].get('href')}"
            output = f"**Top Result:**\nhttps://www.youtube.com{dir_address}"

            if not dir_address:
                return await ctx.errer("No results found!")

            await ctx.send(output)

    @commands.command(aliases=['rock', 'paper', 'scissors', 'lizard', 'spock', 'rps'], no_pm=True)
    async def settle(self, ctx, opt: str = None):
        """ Play rock paper scissors, lizard spock

        Scissors cut paper, paper covers rock,
        rock crushes lizard, lizard poisons Spock,
        Spock smashes scissors, scissors decapitate lizard,
        lizard eats paper, paper disproves Spock,
        Spock vaporizes rock and, as it’s always been,
        rock crushes scissors.
        """
        if opt is None:
            return await ctx.error("Please select one of rock, paper, scissors, lizard and spock")
        player_choice = self.RPSLS[opt]
        a = ctx.message.author.display_name
        b = self.bot.user.name

        available = RPSLS.rock, RPSLS.paper, RPSLS.scissors, RPSLS.lizard, RPSLS.spock
        bot_choice = random.choice(available)

        # I know, this is a mess, but trust me, it works correctly
        # each item wins or loses depending on the random choice
        # against the user's input.
        # Fun fact, this cond took me 15 min to write, and after that I slept
        # 18 hours straight!
        cond = {
            (self.RPSLS['rock'], self.RPSLS['paper']): False,
            (self.RPSLS['rock'], self.RPSLS['scissors']): True,
            (self.RPSLS['rock'], self.RPSLS['lizard']): True,
            (self.RPSLS['rock'], self.RPSLS['spock']): False,
            (self.RPSLS['paper'], self.RPSLS['rock']): True,
            (self.RPSLS['paper'], self.RPSLS['scissors']): False,
            (self.RPSLS['paper'], self.RPSLS['lizard']): False,
            (self.RPSLS['paper'], self.RPSLS['spock']): True,
            (self.RPSLS['scissors'], self.RPSLS['rock']): False,
            (self.RPSLS['scissors'], self.RPSLS['paper']): True,
            (self.RPSLS['scissors'], self.RPSLS['lizard']): True,
            (self.RPSLS['scissors'], self.RPSLS['spock']): False,
            (self.RPSLS['lizard'], self.RPSLS['rock']): False,
            (self.RPSLS['lizard'], self.RPSLS['paper']): True,
            (self.RPSLS['lizard'], self.RPSLS['scissors']): False,
            (self.RPSLS['lizard'], self.RPSLS['spock']): True,
            (self.RPSLS['spock'], self.RPSLS['rock']): True,
            (self.RPSLS['spock'], self.RPSLS['paper']): False,
            (self.RPSLS['spock'], self.RPSLS['scissors']): True,
            (self.RPSLS['spock'], self.RPSLS['lizard']): False
            }

        e = discord.Embed(colour=self.bot.user_color)
        e.add_field(name=f"{a}'s choice:", value=f'{player_choice.value}', inline=True)
        e.add_field(name=f"{b}'s choice:", value=f'{bot_choice.value}', inline=True)

        if bot_choice == player_choice:
            outcome = None
        else:
            outcome = cond[(player_choice, bot_choice)]

        if outcome:
            e.set_footer(text=f"{a} wins, {b} loses...")
        elif not outcome:
            e.set_footer(text=f"{b} wins! {a} loses...")
        else:
            e.set_footer(text="We're square")
        try:
            await ctx.send(embed=e)
        except discord.HTTPException:
            return await ctx.error('Unable to send embeds here!')

    @commands.command(aliases=['post_channel'], no_pm=True)
    async def post(self, ctx, channel: discord.TextChannel, *, message: str = None):
        """ Send a message to any channel in Guild
        Usage: post #general Hello world! """

        if channel is None:
            return await ctx.error('Use a channel ID or name to send a message from here.')

        if message is None:
            return await ctx.error("Please provide a message to send to the provided channel")

        try:
            await channel.send(message)
            await ctx.channel.send('Success!')
        except discord.Forbidden:
            return await ctx.error('The bot does Not have enough permissions to send messages in that channel.')

    @commands.command()
    async def textmojify(self, ctx, *, msg):
        """ Convert text into emojis """

        if msg is not None:
            text = msg.lower().translate(self.textmoji_table)
            await ctx.send(text)
        else:
            return await ctx.error('Please provide something to TextMojify.')

    '''@commands.command(description='To use the webapp go to http://eeemo.net/')
    async def zalgo(self, ctx, *, message: str=None):
        """Fuck up text

        BROKEN!!! I'll fix it soon™
        """
        try:
            await ctx.channel.trigger_typing()
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        user = ctx.message.author.display_name
        if message != None:
            words = message.split()
            try:
                iterations = int(words[len(words) - 1])
                words = words[:-1]
            except Exception:
                iterations = 1

            if iterations > 100:
                iterations = 100
            if iterations < 1:
                iterations = 1

            zalgo = " ".join(words)
            for i in range(iterations):
                if len(zalgo) > 2000:
                    break
                zalgo = self._zalgo(zalgo)

            zalgo = zalgo[:2000]
            e = discord.Embed(colour=discord.Colour(0xed791d))
            e.set_author(name=user, icon_url=ctx.message.author.avatar_url)
            e.description = zalgo
            try:
                await ctx.send(embed=e)
            except discord.HTTPException:
                await ctx.send('Unable to send embeds here!')
        else:
            await ctx.send(f'Usage: `{ctx.prefix}zalgo [your text]`', delete_after=5)'''

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

    @commands.command(aliases=['thisis'])
    async def thisistisis(self, ctx, *, text):
        """ Secret language for initiates only. Not! """

        sis = text.replace('a', 'i').replace('A', 'I').replace('e', 'i').replace('E', 'I') \
            .replace('o', 'i').replace('O', 'I').replace('u', 'i').replace('U', 'I')

        e = discord.Embed(colour=self.bot.user_color)
        e.add_field(name=f'~~*{text}*~~', value=f'```{sis}```')
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

    @commands.group(invoke_without_command=True, aliases=['ud', 'urbandict'])
    async def urban(self, ctx, *, query: str):
        """ Check UrbanDictionary for the meaning of a word """
        try:
            resultlst = await self.bot.loop.run_in_executor(None, ud.define, query)
            item = resultlst[0]
        except IndexError:
            return await ctx.error(f'Unable to find definition for `{query}`.')

        em = discord.Embed(color=self.bot.user_color)
        em.set_author(name="\U0001f4d6 Urban Dictionary")
        em.add_field(name="Word", value=item.word, inline=False)
        em.add_field(name="Definition", value=item.definition, inline=False)
        em.add_field(name="Example(s)", value=item.example, inline=False)

        await ctx.send(embed=em)

    @urban.command(aliases=['-s'])
    async def search(self, ctx, *, query: str):
        """ Search UrbanDictoinary for a Specific Word """

        resultlst = await self.bot.loop.run_in_executor(None, ud.define, query)

        msg = []
        for number, option in enumerate(resultlst[:4]):
            msg.append(f"{number + 1}. {option.word}\n  " 
                       f"{option.definition[:57]+'...' if len(option.definition)>65 else option.definition}")
        send_msg = '\n'.join(msg)
        em = discord.Embed(title="Results", description=send_msg, color=self.bot.user_color)
        em.set_footer(text="Type 'exit' to leave the menu.")
        menumsg = await ctx.send(embed=em)

        def check(m):
            return m.author == ctx.message.author and m.channel == ctx.message.channel and m.content.isdigit()
        response = await self.bot.wait_for('message', check=check)

        try:
            if response.content.lower() == 'exit':
                await response.delete()
                await menumsg.delete()
                return
            else:
                await response.delete()
                await menumsg.delete()
                item = resultlst[int(response.content) - 1]
        except IndexError:
            return await ctx.error('Invalid option!')

        em = discord.Embed(color=self.bot.user_color)
        em.set_author(name="\U0001f4d6 Urban Dictionary")
        em.add_field(name="Word", value=item.word)
        em.add_field(name="Definition", value=item.definition)
        em.add_field(name="Example(s)", value=item.example)
        await ctx.send(embed=em)

    @urban.command(aliases=['-r'])
    async def random(self, ctx):
        """ Get a Random Word and its Meaning from UrbanDictionary """
        item = await self.bot.loop.run_in_executor(None, ud.random)

        em = discord.Embed(color=self.bot.user_color)
        em.set_author(name="\U0001f4d6 Urban Dictionary")
        em.add_field(name="Word", value=item[0].word)
        em.add_field(name="Definition", value=item[0].definition)
        em.add_field(name="Example(s)", value=item[0].example)

        await ctx.send(embed=em)

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

    @commands.command()
    async def guess(self, ctx, number: int = None):
        """ Guess a number between 1 and 11 """
        answer = random.randint(1, 11)
        u = ctx.message.author.display_name

        e = discord.Embed(colour=self.bot.user_color)
        if number is None:
            return await ctx.send('Guess a number between 1 and 11')

        if number < answer or number > answer:
            q_mark = '\N{BLACK QUESTION MARK ORNAMENT}'
            e.add_field(name=f'{q_mark} Your choice {u}: `{number}`',
                        value=f'```{random.choice(self.guessed_wrong)} {answer}```', inline=True)
            try:
                await ctx.send(embed=e)
            except discord.HTTPException:
                return await ctx.error('Unable to send embeds here!')

        if number == answer:
            q_mark = '\N{BLACK QUESTION MARK ORNAMENT}'

            e.add_field(name=f'{q_mark} Correct number: `{answer}`',
                        value=f'```{random.choice(self.guessed_right)} {u}!```', inline=True)
            try:
                await ctx.send(embed=e)
            except discord.HTTPException:
                return await ctx.error('Unable to send embeds here!')

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
