#!/bin/env python3

import random
import discord
from discord.ext import commands


class Misc:
    def __init__(self, bot):
        self.bot = bot
        self.ball_replies = ["It is certain", "It is decidedly so", "Without a doubt", "Yes definitely",
                              "You may rely on it", "As I see it yes", "Most likely", "Outlook good", "Yes",
                              "Signs point to yes", "Reply hazy. Try again", "Ask again later",
                              "Better not tell you now", "Cannot predict now", "Concentrate and ask again",
                              "No comment", "Don't count on it", "My reply is no", "My sources say no",
                              "Outlook not so good", "Very doubtful", "Not as I see it", "No. Never", "Absolutely not",
                              "I doubt it"]
        self.coins = ["Heads", "Tails"]
        self.color = bot.user_color

    @commands.command(name='8ball', aliases=['ball', 'ask'])
    async def eight_ball(self, ctx, *, question):
        """Ask me whatever you want! And I will answer it..."""
        if not question.endswith('?'):
            return await ctx.error("That doesn't look like a question to me.")

        await ctx.reply(f'\U0001f3b1 | {random.choice(self.ball_replies)}')

    @commands.command(name="flip", aliases=["coinflip"])
    async def coin_flip(self, ctx):
        """ Toss a coin """
        result = random.choice(self.coins)
        emb = discord.Embed(title=result, colour=self.color)
        emb.set_thumbnail(url="http://researchmaniacs.com/Random/Images/Quarter-Tails.png" if self.coins.index(result)
                              else "http://researchmaniacs.com/Random/Images/Quarter-Heads.png")
        await ctx.send(embed=emb)

    @commands.command(aliases=['pingtime'])
    async def ping(self, ctx):
      pingtime = self.bot.latency * 1000
      emb = discord.Embed(colour=0x00ffff)
      emb.add_field(name='Pong!', value=pingtime)
      await ctx.send(embed=emb)

def setup(bot):
    bot.add_cog(Misc(bot))

