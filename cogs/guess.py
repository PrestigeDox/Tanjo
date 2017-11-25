import discord
import asyncio
import random
from discord.ext import commands

class Guess:
    def __init__(self, bot):
        self.bot = bot
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


    @commands.command()
    async def guess(self, ctx, number: int=None):
        """ Guess a number between 1 and 11 """
        answer = random.randint(1, 11)
        u = ctx.message.author.display_name

        e = discord.Embed(colour=self.bot.user_color)
        if number is None:
            return await ctx.error('Guess a number between 1 and 11')

        if answer < number < answer:
            q_mark = '\N{BLACK QUESTION MARK ORNAMENT}'
            e.add_field(name=f'{q_mark} Your choice {u}: `{number}`',
                        value=msg, inline=True)
            try:
                await ctx.send(embed=e)
            except discord.HTTPException:
                return await ctx.send(f'```{random.choice(self.guessed_wrong)} {answer}```')

        elif number == answer:
            q_mark = '\N{BLACK QUESTION MARK ORNAMENT}'
            e.add_field(name=f'{q_mark} Correct number: `{answer}`',
                        value=msg, inline=True)
            try:
                await ctx.send(embed=e)
            except discord.HTTPException:
                return await ctx.send(f'```{random.choice(self.guessed_right)} {u}!```')


def setup(bot):
    bot.add_cog(Guess(bot))
