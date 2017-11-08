#!/bin/env python3

import discord
from discord.ext import commands
import random


class Misc:
    def __init__(self, bot):
        self.bot = bot
        self.ball_replies = [
                              "It is certain",
                              "It is decidedly so",
                              "Without a doubt",
                              "Yes definitely",
                              "You may rely on it",
                              "As I see it yes",
                              "Most likely",
                              "Outlook good",
                              "Yes",
                              "Signs point to yes",

                              "Reply hazy. Try again",
                              "Ask again later",
                              "Better not tell you now",
                              "Cannot predict now",
                              "Concentrate and ask again",
                              "No comment",

                              "Don't count on it",
                              "My reply is no",
                              "My sources say no",
                              "Outlook not so good",
                              "Very doubtful",
                              "Not as I see it",
                              "No. Never",
                              "Absolutely not",
                              "I doubt it"
                            ]

    @commands.command(aliases=['8ball', 'ask'])
    async def eight_ball(self, ctx, *, question):
        """Ask me whatever you want! And I will answer it..."""
        if question.endswith('?'):
            await ctx.reply(f'\U0001f52e | {random.choice(self.ball_replies)}')
        else:
            await ctx.reply('That doesn't look like a question.')
            

def setup(bot):
    bot.add_cog(Misc(bot))
            
