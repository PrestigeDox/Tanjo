import discord
import random

from discord.ext import commands
from enum import Enum


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


class Rpsls:
    # Init with the bot reference, and a reference to the settings var
    def __init__(self, bot):
        self.bot = bot
        self.RPSLS = {'rock': "\N{RAISED FIST} **Rock!**",
                      'paper': "\N{RAISED HAND WITH FINGERS SPLAYED} **Paper!**",
                      'scissors': "\N{BLACK SCISSORS} **Scissors!**",
                      'lizard': "\N{LIZARD} **Lizard!**",
                      'spock': "\N{RAISED HAND WITH PART BETWEEN MIDDLE AND RING FINGERS} **Spock!**"}

    @commands.command(aliases=['rock', 'paper', 'scissors', 'lizard', 'spock', 'rps'], no_pm=True)
    async def settle(self, ctx, opt: str=None):
        """ Play rock paper scissors, lizard spock!
        Scissors cut Paper, Paper covers Rock,
        Rock crushes Lizard, Lizard poisons Spock,
        Spock smashes Scissors, Scissors decapitate Lizard,
        Lizard eats Paper, Paper disproves Spock,
        Spock vaporizes Rock and, as it’s always been,
        Rock crushes Scissors.
        """
        if opt is None:
            msg = f"Please select one either `rock`, `paper`, `scissors`, `lizard` OR `spock` as your option!\n" \
                  f"for an explanation use help:\n\n" \
                  f"`{ctx.prefix}help {ctx.invoked_with}`"
            return await ctx.error(msg)

        player_choice = self.RPSLS[opt]
        a = ctx.message.author.display_name
        b = self.bot.user.name

        available = self.RPSLS['rock'], self.RPSLS['paper'], self.RPSLS['scissors'], \
                    self.RPSLS['lizard'], self.RPSLS['spock']
        bot_choice = random.choice(available)

        # Okay, this has now its own cog, try to make the cond smaller ;P
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

        opt1 = f"{a} wins, {b} loses..."
        opt2 = f"{b} wins! {a} loses..."
        opt3 = "We're square"

        e = discord.Embed(colour=self.bot.user_color)
        e.add_field(name=f"{a}'s choice:", value=f'{player_choice.value}', inline=True)
        e.add_field(name=f"{b}'s choice:", value=f'{bot_choice.value}', inline=True)

        if bot_choice == player_choice:
            outcome = None
        else:
            outcome = cond[(player_choice, bot_choice)]

        if outcome:
            e.set_footer(text=opt1)
        elif not outcome:
            e.set_footer(text=opt2)
        else:
            e.set_footer(text=opt3)

        try:
            await ctx.send(embed=e)

        # This is in case bot cannot answer with embeds, result still prints output
        except discord.HTTPException:
            for x in outcome:
                if x is outcome:
                    result = opt1
                elif x is not outcome:
                    result = opt2
                else:
                    result = opt3
                return await ctx.send(result)


def setup(bot):
    bot.add_cog(Rpsls(bot))
