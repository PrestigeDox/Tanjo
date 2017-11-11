from __future__ import division
import discord
import asyncio
import random
import math
import operator
import json
import urbandict
import requests

from bs4 import BeautifulSoup
from discord.ext import commands
from urllib.request import urlopen
from enum import Enum
from pyparsing import (Literal, CaselessLiteral, Word, Combine, Group, Optional,
                       ZeroOrMore, Forward, nums, alphas, oneOf)


class RPSLS(Enum):
    rock = "\N{RAISED FIST} **Rock!**"
    paper = "\N{RAISED HAND WITH FINGERS SPLAYED} **Paper!**"
    scissors = "\N{BLACK SCISSORS} **Scissors!**"
    lizard = "\N{LIZARD} **Lizard!**"
    spock = "\N{RAISED HAND WITH PART BETWEEN MIDDLE AND RING FINGERS} **Spock!**"


class RPSLSParser:
    def __init__(self, argument):
        argument = argument.lower()
        if argument == "rock":
            self.choice = RPSLS.rock
        elif argument == "paper":
            self.choice = RPSLS.paper
        elif argument == "scissors":
            self.choice = RPSLS.scissors
        elif argument == "lizard":
            self.choice = RPSLS.lizard
        elif argument == "spock":
            self.choice = RPSLS.spock
        else:
            raise


class NumericStringParserForPython3(object):
    # So, this is the whole code for calculator
    # It converts the input into something that can give some
    # sort of result, or at least tries to do so
    def pushFirst(self, strg, loc, toks):
        self.exprStack.append( toks[0] )
    def pushUMinus(self, strg, loc, toks):
        if toks and toks[0]=='-':
            self.exprStack.append( 'unary -' )
    def __init__(self):
        point = Literal( "." )
        e     = CaselessLiteral( "E" )
        fnumber = Combine( Word( "+-"+nums, nums ) +
                        Optional( point + Optional( Word( nums ) ) ) +
                        Optional( e + Word( "+-"+nums, nums ) ) )
        ident = Word(alphas, alphas+nums+"_$")
        plus  = Literal( "+" )
        minus = Literal( "-" )
        mult  = Literal( "*" )
        div   = Literal( "/" )
        lpar  = Literal( "(" ).suppress()
        rpar  = Literal( ")" ).suppress()
        addop  = plus | minus
        multop = mult | div
        expop = Literal( "^" )
        pi    = CaselessLiteral( "PI" )
        expr = Forward()
        atom = ((Optional(oneOf("- +")) +
                (pi|e|fnumber|ident+lpar+expr+rpar).setParseAction(self.pushFirst))
                | Optional(oneOf("- +")) + Group(lpar+expr+rpar)
                ).setParseAction(self.pushUMinus)
        # By defining exp as "atom [ ^ factor ]..." instead of "atom [ ^ atom ]...", 
        # the exponents are parsed right-to-left exponents, instead of left-to-right
        # that is, 2^3^2 = 2^(3^2), instead of (2^3)^2.
        factor = Forward()
        factor << atom + ZeroOrMore( ( expop + factor ).setParseAction( self.pushFirst ) )
        term = factor + ZeroOrMore( ( multop + factor ).setParseAction( self.pushFirst ) )
        expr << term + ZeroOrMore( ( addop + term ).setParseAction( self.pushFirst ) )
        addop_term = ( addop + term ).setParseAction( self.pushFirst )
        general_term = term + ZeroOrMore( addop_term ) | OneOrMore( addop_term)
        expr <<  general_term
        self.bnf = expr
        # Here the code maps operator symbols to their corresponding arithmetic operations
        # decided to go for * instead of x to be used in multiplications, for obvious reasons:
        # it is commonly used that way with computer keypads that have numbers using one hand
        # And yeah, I know where you keep the other hand... lewd!
        epsilon = 1e-12
        self.opn = {
                "+" : operator.add,
                "-" : operator.sub,
                "*" : operator.mul,
                "/" : operator.truediv,
                "^" : operator.pow }
        # After getting the correct operators, now to make use of strings for more advanced
        # mathematical calculations, haven't tried them all intensively, so they might break,
        # if that happens, use your phone's calculator instead, kthx.
        self.fn  = {
                "sin" : math.sin,
                "cos" : math.cos,
                "tan" : math.tan,
                "abs" : abs,
                "trunc" : lambda a: int(a),
                "round" : round,
                "sgn" : lambda a: abs(a)>epsilon and cmp(a,0) or 0}

    def evaluateStack(self, s):
        op = s.pop()
        if op == 'unary -':
            return -self.evaluateStack( s )
        if op in "+-*/^":
            op2 = self.evaluateStack( s )
            op1 = self.evaluateStack( s )
            return self.opn[op]( op1, op2 )
        elif op == "PI":
            return math.pi # 3.1415926535
        elif op == "E":
            return math.e  # 2.718281828
        elif op in self.fn:
            return self.fn[op]( self.evaluateStack( s ) )
        elif op[0].isalpha():
            return 0
        else:
            return float( op )
    def eval(self,num_string,parseAll=True):
        self.exprStack=[]
        results=self.bnf.parseString(num_string,parseAll)
        val=self.evaluateStack( self.exprStack[:] )
        return val


class Utilities:
    # Init with the bot reference, and a reference to the settings var
    def __init__(self, bot):
        self.bot = bot
        self.nsp=NumericStringParserForPython3()

        # Might work for share command into any particular channel
        # but haven't had luck thus far
        # self.TextChannel = discord.Channel

    @commands.command(aliases=['yt', 'vid'])
    async def video(self, ctx, *, search):
        """ Search for the first videos match on YouTube """
        try:
            await ctx.channel.trigger_typing()
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        search = search.replace(' ', '+').lower()
        response = requests.get(f"https://www.youtube.com/results?search_query={search}").text
        result = BeautifulSoup(response, "lxml")
        dir_address = f"{result.find_all(attrs={'class': 'yt-uix-tile-link'})[0].get('href')}"
        output = f"**Top Result:**\nhttps://www.youtube.com{dir_address}"
        try:
            await ctx.send(output)
        except Exception as e:
            await ctx.send(f'```{e}```')

    @commands.command(description="A random number from 1 to 100")
    async def hexa(self, ctx):
        """ Get a random number from 1 to 100 """
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        user = ctx.message.author.display_name
        reply = ['Lucky', "Today's",
                 'Random', 'Generated',
                 'A', 'Got this']
        e = discord.Embed(colour=discord.Colour(0xed791d))
        e.add_field(name=f"{user}'s hexa:",
                    value=f'{random.choice(reply)} number from 1 to 100: **`{random.randint(1, 99)}`**')
        try:
            await ctx.send(embed=e)
        except discord.HTTPException:
            await ctx.send('Unable to send embeds here!')

    @commands.command(aliases=['rock', 'paper', 'scissors', 'lizard', 'spock', 'rps'], no_pm=True)
    async def settle(self, ctx, your_choice: RPSLSParser=None):
        """ Play rock paper scissors, lizard spock

        Scissors cut paper, paper covers rock,
        rock crushes lizard, lizard poisons Spock,
        Spock smashes scissors, scissors decapitate lizard,
        lizard eats paper, paper disproves Spock,
        Spock vaporizes rock and, as it’s always been,
        rock crushes scissors.
        """
        try:
            await ctx.channel.trigger_typing()
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        if your_choice is not None:
            a = ctx.message.author.display_name
            b = self.bot.user.name
            player_choice = your_choice.choice
            available = RPSLS.rock, RPSLS.paper, RPSLS.scissors, RPSLS.lizard, RPSLS.spock
            bot_choice = random.choice(available)
            # I know, this is a mess, but trust me, it works correctly
            # each item wins or loses depending on the random choice
            # against the user's input.
            # Fun fact, this cond took me 15 min to write, and after that I slept
            # 18 hours straight!
            cond = {
                    (RPSLS.rock,     RPSLS.paper): False,
                    (RPSLS.rock,     RPSLS.scissors): True,
                    (RPSLS.rock,     RPSLS.lizard): True,
                    (RPSLS.rock,     RPSLS.spock): False,
                    (RPSLS.paper,    RPSLS.rock): True,
                    (RPSLS.paper,    RPSLS.scissors): False,
                    (RPSLS.paper,    RPSLS.lizard): False,
                    (RPSLS.paper,    RPSLS.spock): True,
                    (RPSLS.scissors, RPSLS.rock): False,
                    (RPSLS.scissors, RPSLS.paper): True,
                    (RPSLS.scissors, RPSLS.lizard): True,
                    (RPSLS.scissors, RPSLS.spock): False,
                    (RPSLS.lizard,   RPSLS.rock): False,
                    (RPSLS.lizard,   RPSLS.paper): True,
                    (RPSLS.lizard,   RPSLS.scissors): False,
                    (RPSLS.lizard,   RPSLS.spock): True,
                    (RPSLS.spock,    RPSLS.rock): True,
                    (RPSLS.spock,    RPSLS.paper): False,
                    (RPSLS.spock,    RPSLS.scissors): True,
                    (RPSLS.spock,    RPSLS.lizard): False
                   }
            e = discord.Embed(colour=discord.Colour(0xed791d))
            e.add_field(name=f"{a}'s choice:", value=f'{player_choice.value}', inline=True)
            e.add_field(name=f"{b}'s choice:", value=f'{bot_choice.value}', inline=True)
            
            if bot_choice == player_choice:
                outcome = None
            else:
                outcome = cond[(player_choice, bot_choice)]
            if outcome is True:
                e.set_footer(text=f"{a} wins, {b} loses...")
                try:
                    await ctx.send(embed=e)
                except discord.HTTPException:
                    await ctx.send('Unable to send embeds here!')
            elif outcome is False:
                e.set_footer(text=f"{b} wins! {a} loses...")
                try:
                    await ctx.send(embed=e)
                except discord.HTTPException:
                    await ctx.send('Unable to send embeds here!')
            else:
                e.set_footer(text="We're square")
                try:
                    await ctx.send(embed=e)
                except discord.HTTPException:
                    await ctx.send('Unable to send embeds here!')
        else:
            msg = 'Scissors cut paper, paper covers rock, rock crushes lizard, ' \
                  'lizard poisons Spock, Spock smashes scissors, scissors decapitate lizard, ' \
                  'lizard eats paper, paper disproves Spock, Spock vaporizes rock and, ' \
                  'as it’s always been, rock crushes scissors.\n\n~Sheldon Cooper,\n ' \
                  'S02E08 – “The Lizard-Spock Expansion”'
            await ctx.send(f'```{msg}```', delete_after=60)
            pass

    @commands.command(aliases=['post_channel'], no_pm=True)
    async def post(self, ctx, channel: discord.TextChannel, *, message: str=None):
        """ Send a message to any channel in Guild
        Usage: post #general Hello world! """
        try:
            await ctx.channel.trigger_typing()
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        if channel is None:
            msg = 'Use a channel ID or name to send a message from here.'
            await ctx.send(msg, delete_after=5)
            return

        if channel is not None:
            if message is not None:
                try:
                    await channel.send(message)
                    await ctx.channel.send('Success!', delete_after=5)
                except discord.Forbidden:
                    msg = 'Reee! Not enough permissions to send messages in that channel!'
                    await ctx.send(msg, delete_after=5)
            else:
                msg = 'Reee! Write something to send to that channel!'
                await ctx.send(msg, delete_after=5)

    @commands.command()
    async def textmojify(self, ctx, *, msg):
        """ Convert text into emojis """
        try:
            await ctx.channel.trigger_typing()
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        if msg != None:
            out = msg.lower()
            # Okay, I need to include numbers, but so far it works for words
            text = out.replace(' ', '    ')\
                      .replace('ab', '\u200B🆎').replace('cl', '\u200B🆑')\
                      .replace('!', '\u200B❗').replace('?', '\u200B❓')\
                      .replace('vs', '\u200B🆚').replace('.', '\u200B🔸')\
                      .replace(',', '🔻').replace('a', '\u200B🅰')\
                      .replace('b', '\u200B🅱').replace('c', '\u200B🇨')\
                      .replace('d', '\u200B🇩').replace('e', '\u200B🇪')\
                      .replace('f', '\u200B🇫').replace('g', '\u200B🇬')\
                      .replace('h', '\u200B🇭').replace('i', '\u200B🇮')\
                      .replace('j', '\u200B🇯').replace('k', '\u200B🇰')\
                      .replace('l', '\u200B🇱').replace('m', '\u200B🇲')\
                      .replace('n', '\u200B🇳').replace('ñ', '\u200B🇳')\
                      .replace('o', '\u200B🅾').replace('p', '\u200B🅿')\
                      .replace('q', '\u200B🇶').replace('r', '\u200B🇷')\
                      .replace('s', '\u200B🇸').replace('t', '\u200B🇹')\
                      .replace('u', '\u200B🇺').replace('v', '\u200B🇻')\
                      .replace('w', '\u200B🇼').replace('x', '\u200B🇽')\
                      .replace('y', '\u200B🇾').replace('z', '\u200B🇿')
            try:
                await ctx.send(text)
            except Exception as e:
                await ctx.send(f'```{e}```')
        else:
            await ctx.send('Write something, reee!', delete_after=3.0)

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
        try:
            await ctx.channel.trigger_typing()
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        e = discord.Embed(colour=discord.Colour(0xed791d))
        if msg is None:
            usage = 'Write a message after command!'
            e.description = usage
        else:
            e.description = f'`{msg.lower()[::-1]}`    \N{LEFTWARDS BLACK ARROW}'
        try:
            await ctx.send(embed=e)
        except discord.HTTPException:
            await ctx.send('Unable to send embeds here!')

    @commands.command(aliases=['thisis'])
    async def thisistisis(self, ctx, *, text):
        """ Secret language for initiates only. Not! """
        try:
            await ctx.channel.trigger_typing()
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        sis = text.replace('a', 'i').replace('A', 'I').replace('e', 'i').replace('E', 'I')\
                  .replace('o', 'i').replace('O', 'I').replace('u', 'i').replace('U', 'I')\
                  .replace('á', 'i').replace('Á', 'I').replace('é', 'i').replace('É', 'I')\
                  .replace('ó', 'i').replace('Ó', 'I').replace('ú', 'i').replace('Ú', 'I')
        author = ctx.message.author

        e = discord.Embed(colour=discord.Colour(0xed791d))
        e.add_field(name=f'~~*{text}*~~', value=f'```{sis}```')
        try:
            await ctx.send(embed=e)
        except discord.HTTPException:
            await ctx.send('Unable to send embeds here!')

    @commands.command(aliases=['tu'])
    async def tinyurl(self, ctx, *, link: str=None):
        """Shorten URLs"""
        gif = 'https://cdn.discordapp.com/avatars/323578534763298816/a_e9ce069bedf43001b27805cd8ef9c0db.gif'
        usage = f'**Usage:**\n`{ctx.prefix}{ctx.invoked_with} {gif}`'
        try:
            await ctx.channel.trigger_typing()
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        if link != None:
            if link.startswith('http'):
                apitiny = 'http://tinyurl.com/api-create.php?url='
                tiny_url = urlopen(apitiny + link).read().decode("utf-8")
                u = ctx.message.author.display_name

                e = discord.Embed(colour=discord.Colour(0xed791d))
                e.description = f'Requested by: *{u}*'
                e.add_field(name="Original 🌏", value=f'~~`{link}`~~', inline=False)
                e.add_field(name="Tinyurl 🔗", value=f'```{tiny_url}```', inline=False)
                try:
                    await ctx.send(embed=e)
                except discord.HTTPException:
                    await ctx.send('Unable to send embeds here!')
            else:
                await ctx.send("That doesn't look like a valid URL!", delete_after=5)

        else:
            await ctx.send(usage, delete_after=15)
            return

    @commands.command(aliases=['calc', 'maths'], name="calculate")
    async def _calculate(self, ctx, *, formula=None):
        """Python calculator command
        Usage: Add: 2+3, Sub: 2-3, Mul: 2*3, Div: 2/3, Exp: 2^3,
        Pi: PI, E: e, Sin: sin, Cos: cos, Tan: tan, Abs: abs,
        Tru: trunc, Rou: round, Sgn: sgn

        This command uses: Paul McGuire's fourFn.py."""
        u = ctx.message.author.display_name
        try:
            await ctx.channel.trigger_typing()
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        if formula == None:
            # How can it calculate an empty message? Reee!
            msg = f'\u200BUsage: `{ctx.prefix}{ctx.invoked_with} [any maths formula]`'
            e = discord.Embed(colour=discord.Colour(0xed791d))
            e.description = f'{msg}'
            try:
                await ctx.send(embed=e)
            except discord.HTTPException:
                await ctx.send('Unable to send embeds here!')
            return

        # Okay, so here it tries to solve the problem, so far it has received
        # some numbers and operators, it will try to parse the input into intelligeble
        # formulas and solve them...
        try:
            answer=self.nsp.eval(formula)
        except:
            # If there's a problem with the input, shows examples instead of hanging up
            e = discord.Embed(colour=discord.Colour(0xed791d))
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
                await ctx.send('Unable to send embeds here!')
            return

        # If we made it here, then the correct input prints correct answer
        # everything else was just to make sure the input was somewhat logical
        e = discord.Embed(colour=discord.Colour(0xed791d))
        e.add_field(name='Input:', value=f'```{formula}```', inline=True)
        e.add_field(name='Result:', value=f'```{round(answer, 2)}```', inline=True)
        try:
            await ctx.send(embed=e)
        except discord.HTTPException:
            await ctx.send('Unable to send embeds here!')

    @commands.command()
    async def ud(self, ctx, *, term):
        """Retrieves a definition from Urban Dictionary
        Type command and the entry you want to search"""
        # Gotta put this command in an executor, so it makes the coro sleep 
        # and returns other commands that are executed simultaneously once it finishes
        try:
            await ctx.channel.trigger_typing()
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        list1 = urbandict.define(term)

        e = discord.Embed(colour=discord.Colour(0xed791d))
        try:
            e.set_footer(text='Pocket Edition:', icon_url="http://i.imgur.com/OSwN4R2.png")
            e.add_field(name='Search:', value=term)
            e.add_field(name='Definition:', value=list1[0]['def'])
            try:
                await ctx.send(embed=e)
            except discord.HTTPException:
                await ctx.send('Unable to send embeds here!')

        except Exception as e:
            await ctx.send(f'```{e}```')
            return

    @commands.command(aliases=['suggestion'])
    async def feedback(self, ctx, *, text: str='Sorry, forgot to write.'):
        """Suggestions and feature requests"""
        # need to call get_channel, send method exists only in messageables
        try:
            await ctx.channel.trigger_typing()
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        user = ctx.message.author
        c = ctx.invoked_with

        e = discord.Embed(colour=discord.Colour(0xed791d))
        e.title = 'Sum feedbak:'
        e.set_author(name=f'{user.name} | {user.display_name}', icon_url=user.avatar_url)
        e.description = f'{text}'
        
        try:
            # Sends a message with feedback into channel 366119729728978944
            # but so far it doesn't work, rip!
            await channel.send(discord.utils.get(id=366119729728978944), embed=e)
            await ctx.send(f'{c.title()} received successfully. Thank you!', delete_after=5)
        except discord.Forbidden:
            msg = f'Unable to send {c.lower()}, please join Support Server\nhttps://discord.gg/9qgzkQV'
            await ctx.send(msg)

    @commands.command()
    async def guess(self, ctx, number: int=None):
        """ Guess a number between 1 and 11 """
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        answer = random.randint(1, 11)
        u = ctx.message.author.display_name

        e = discord.Embed(colour=discord.Colour(0xed791d))
        if number == None:
            await ctx.send('Guess a number between 1 and 11', delete_after=5)
            return

        if number < answer or number > answer:
            q_mark = '\N{BLACK QUESTION MARK ORNAMENT}'
            guessed_wrong = [
                'Not even close, the right number was:',
                'Better luck next time, the number was:',
                'How could you have known that the number was:',
                'Hmm, well, the right number was:',
                'Not getting any better, the number was:',
                'Right number was:'
                ]
            e.add_field(name=f'{q_mark} Your choice {u}: `{number}`',
                        value=f'```{random.choice(guessed_wrong)} {answer}```', inline=True)
            try:
                await ctx.send(embed=e)
            except discord.HTTPException:
                # em_list = await embedtobox.etb(em)
                # for page in em_list:
                #    await ctx.send(page)
                await ctx.send('Unable to send embeds here!')

        if number is answer:
            q_mark = '\N{BLACK QUESTION MARK ORNAMENT}'
            guessed_right = [
                'You guessed correctly',
                'Everyone knew you could do it',
                'You got the right answer',
                'History will remember you...'
                ]
            e.add_field(name=f'{q_mark} Correct number: `{answer}`', 
                        value=f'```{random.choice(guessed_right)} {u}!```', inline=True)
            try:
                await ctx.send(embed=e)
            except discord.HTTPException:
                # em_list = await embedtobox.etb(em)
                # for page in em_list:
                #    await ctx.send(page)
                await ctx.send('Unable to send embeds here!')

    @commands.command(aliases=['prediction', 'crystalball', 'oracle', 'i-ching', 'fortune'])
    async def iching(self, ctx, *, member : discord.Member=None):
        """Based on the ancient I Ching oracle,
        `Usage: command [member]>`
        use it as a guide"""
        try:
            await ctx.message.delete()
            await ctx.send('Tossing 3 antique coins for your result.', delete_after=5)
            await ctx.channel.trigger_typing()
            await asyncio.sleep(6)
        except discord.Forbidden:
            pass

        with open('data/oracle.json') as f:
            choices = json.load(f)

        iching = 'http://i.imgur.com/biEvXBN.png'
        m = member or ctx.author
        p = ctx.invoked_with.title()

        try:
            e = discord.Embed(colour=discord.Colour(0xed791d))
            e.set_thumbnail(url=iching)
            e.set_footer(text="+-<§) Ancient Oracle's wisdom interpreted for now (§>-+")
            e.set_author(name=f"{p}'s inspiration for: {m.display_name} | {m}", icon_url=ctx.message.author.avatar_url)
            e.description = f'Meditation:\n{random.choice(choices)}'
            try:
                await ctx.send(embed=e)
            except discord.HTTPException:
                await ctx.send('Unable to send embeds here!')

        except Exception as e:
            await ctx.send(f'```{e}```')
            pass


def setup(bot):
    bot.add_cog(Utilities(bot))
