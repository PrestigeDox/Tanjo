#!/bin/env python3

import discord
from discord.ext import commands


# This bit allows to more easily unban members via ID or name#discrim
# Taken mostly from R. Danny
# https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/mod.py#L83-L94
class BannedMember(commands.Converter):
    async def convert(self, ctx, arg):
        bans = await ctx.guild.bans()

        try:
            member_id = int(arg)
            user = discord.utils.find(lambda u: u.user.id == member_id, bans)
        except ValueError:
            user = discord.utils.find(lambda u: str(u.user) == arg, bans)

        if user is None:
            return None

        return user


# TODO:
# Tighten down the except clauses

class Mod:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['k'])
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        """ Kick a member from the server """
        try:
            await ctx.guild.kick(member, reason=reason)
        except:
            await ctx.error('Unable to kick member.')
        else:
            await ctx.send(f'Member `{member}` kicked.\nReason: `{reason}`.')

    @commands.command(aliases=['kb'])
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        """ Ban a member from the server """
        try:
            await ctx.guild.ban(member, reason=reason, delete_message_days=0)
        except:
            await ctx.error('Unable to ban member.')
        else:
            await ctx.send(f'Member `{member}` banned.\nReason: `{reason}`.')

    @commands.command(aliases=['ub'])
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, member: BannedMember, *, reason=None):
        """ Unban a member from the server
        Since you can't highlight them anymore use their name#discrim or ID """
        if member is not None:
            try:
                await ctx.guild.unban(member.user, reason=reason)
            except:
                await ctx.error('Could not unban member.')
            else:
                await ctx.send(f'Member `{member.user}` unbanned.\nReason: `{reason}`.')

        else:
            await ctx.send("Could not find user to unban.")

    @commands.group()
    @commands.has_permissions(manage_messages=True)
    async def clean(self, ctx):
        """ Remove bot messages from the last X messages """
        pass

    @clean.group(name='bot')
    async def clean_bot(self, ctx, num_msg: int = 100):
        """ Remove Tanjo messages from the last X messages (default 100) """
        if num_msg > 100:
            return await ctx.error('Number of messages to be deleted must not exceed 100.')

        # Check so that only bot msgs are removed
        def check(message):
            return message.author.id == self.bot.user.id

        try:
            await ctx.channel.purge(check=check, limit=num_msg)
        except Exception as e:
            await ctx.error(f'Failed to delete messages.\n ```py\n{e}```')

    @clean.group(name='user')
    async def clean_user(self, ctx, member: discord.Member, num_msg: int = 100):
        """ Remove user messages from the last X messages (default 100)
        Note: if the member conversion fails above, it will throw an exception """
        if num_msg > 100:
            return await ctx.error('Number of messages to be deleted must not exceed 100.')

        # Makes sure to only delete the member's messages
        def check(message):
            return message.author.id == member.id

        try:
            await ctx.channel.purge(check=check, limit=num_msg)
        except Exception as e:
            await ctx.error(f'Failed to delete messages.\n ```py\n{e}```')

    @commands.command()
    async def purge(self, ctx, num_msg: int = 100):
        """ Remove the last X messages in a channel (default 100) """
        if num_msg > 100:
            return await ctx.error('Number of messages to be deleted must not exceed 100.')

        try:
            await ctx.channel.purge(limit=num_msg)
        except Exception as e:
            await ctx.error(f'Failed to delete messages.\n ```py\n{e}```')


def setup(bot):
    bot.add_cog(Mod(bot))
