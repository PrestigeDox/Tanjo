import discord
import random
from discord.ext import commands


class RPS:
    def __init__(self, bot):
        self.bot = bot
        self.rps_choices = {'rock': {'val': 1, 'str': '\U0000270a **Rock**'},
                            'paper': {'val': 2, 'str': '\U0001f5d2 **Paper**'},
                            'scissors': {'val': 3, 'str': '\U00002702 **Scissors**'}
                            }

    def get_result(self, bot_choice: str, user_choice: str) -> str:
        """ Small func to determine the winner of RPS """
        if self.rps_choices[user_choice]['val'] - self.rps_choices[bot_choice]['val'] == 0:
            return "It's a draw!"
        elif self.rps_choices[user_choice]['val'] - self.rps_choices[bot_choice]['val'] in (-1, 2):
            return 'You lose!'
        else:
            return 'You win!'

    @commands.command(aliases=['rps'])
    async def rock_paper_scissors(self, ctx, choice: str = None):
        """ Play Rock, Paper, Scissors with Tanjo """
        if choice is None:
            return await ctx.error('Feel free to play the game.')

        choice = choice.lower()
        if choice not in self.rps_choices:
            return await ctx.error("There are three choices here. I'll let you figure that out.")

        bot_choice = random.choice(list(self.rps_choices))
        result = self.get_result(bot_choice, choice)

        # Create embed
        em = discord.Embed(title=result)
        em.add_field(name=ctx.author.display_name, value=self.rps_choices[choice]['str'])
        em.add_field(name='Tanjo', value=self.rps_choices[bot_choice]['str'])

        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(RPS(bot))
