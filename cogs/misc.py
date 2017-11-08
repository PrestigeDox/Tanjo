#!/bin/env python3

import ast
import random
import discord
from discord.ext import commands


class Misc:
    def __init__(self, bot):
        self.bot = bot
        self.session = bot.session
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

    @commands.command(name='choose', aliases=['choice', 'decide'])
    async def choices(self, ctx, *, choices):
        """ Have Tanjo decide what you should do with your life (comma separated) """
        choice_list = choices.split(',')
        if len(choice_list) < 2:
            return await ctx.error("Need at least two choices.")

        await ctx.send(random.choice(choice_list))

    @commands.command(aliases=['pingtime'])
    async def ping(self, ctx):
        pingtime = self.bot.latency * 1000
        emb = discord.Embed(colour=self.color)
        emb.add_field(name='Pong!', value=f'{pingtime:.1f}ms')
        await ctx.send(embed=emb)

    @commands.group()
    async def random(self, ctx):
        pass

    @random.command()
    async def cat(self, ctx):
        """ Random Cat Picture """
        async with self.session.get('http://random.cat/meow') as r:
            image = (await r.json())['file']
        image_embed = discord.Embed(title="Cat Pic!", color=self.color)
        image_embed.set_image(url=image)

        await ctx.send(embed=image_embed)

    @random.command()
    async def dog(self, ctx):
        """ Random Dog Picture """
        async with self.session.get('http://random.dog/woof.json') as r:
            image = (await r.json())['url']
        image_embed = discord.Embed(title="Dog Pic!", color=self.color)
        image_embed.set_image(url=image)

        await ctx.send(embed=image_embed)
        
    @random.command(aliases=["hackerman"])
    async def hacker(self, ctx):
        """ Random Hacker Quote """
        async with self.session.get('https://hacker.actor/quote') as r:
            quote = ast.literal_eval(await r.text())['quote']
        quote_embed = discord.Embed(title="Hackerman Quote", description=quote, color=self.color)
        quote_embed.set_thumbnail(url="https://being-a-weeb.is-bad.com/a4d747.png")

        await ctx.send(embed=quote_embed)

        
def setup(bot):
    bot.add_cog(Misc(bot))
