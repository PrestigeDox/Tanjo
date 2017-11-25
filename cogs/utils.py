from __future__ import division
import discord
import asyncio
import random
import json

from discord.ext import commands


class Utilities:
    # Useful commands
    def __init__(self, bot):
        self.bot = bot
        dev_server = discord.utils.find(lambda s: s.id == 365893884053553162, bot.guilds)
        self.feedback_channel = dev_server.get_channel(365893884053553162)

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


def setup(bot):
    bot.add_cog(Utilities(bot))
