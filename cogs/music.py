#!/bin/env python3

import asyncio
import discord

from datetime import timedelta
from discord.ext import commands
from utils import playlist
from utils import player
from utils.ytsearch import ytsearch


class Music:

    def __init__(self, bot):
        self.bot = bot
        self.reaction_emojis = ['⬅', '➡']

    @commands.command()
    async def play(self, ctx):
        """ Add a song to the playlist """
        message = ctx.message
        bot = self.bot
        effect = 'None'
        searchmode = 0
        if '-rape' in message.content.split():
            print('rape')
            effect = 'rape'
        elif '-c' in message.content.split():
            print('chip')
            effect = 'c'
        elif '-k' in message.content.split():
            effect = 'k'
        if '-s' in message.content.split():
            searchmode = 1

        # Handle funky embed connecting
        if message.guild not in bot.vc_clients:
            np_embed = discord.Embed(title='Connecting...', colour=0xffffff)
            np_embed.set_thumbnail(url='https://i.imgur.com/DQrQwZH.png')
            trying_msg = await message.channel.send(embed=np_embed)

            # Error if you're trying to listen music out of thin air/not in a voice channel
            if message.author.voice is None:
                np_embed = discord.Embed(title='Error', description='You are not in a voice channel', colour=0xffffff)
                np_embed.set_thumbnail(url='https://imgur.com/B9YlwWt.png')
                await trying_msg.edit(embed=np_embed)
                return

            # This timeout never triggers, not sure
            try:
                vc = await message.author.voice.channel.connect(timeout=6.0, reconnect=True)
            except asyncio.TimeoutError:
                np_embed = discord.Embed(title='Error', description="Wasn't able to connect, please try again!",
                                         colour=0xffffff)
                np_embed.set_thumbnail(url='https://imgur.com/B9YlwWt.png')
                await trying_msg.edit(embed=np_embed)
                return
            bot.vc_clients[message.guild] = vc
            np_embed = discord.Embed(title='Bound to ' + message.author.voice.channel.name,
                                     description='summoned by **%s**' % message.author.mention, colour=0xffffff)
            np_embed.set_thumbnail(url='https://imgur.com/F95gtPV.png')
            await trying_msg.edit(embed=np_embed)

        # Smart way to go through the message and find out what's a flag and where our song name starts from
        for n, item in enumerate(message.content.split()[1:], 1):
            if not item.startswith('-'):
                break

        song_name = ' '.join(message.content.split()[n:])

        # If we already have a player for this server, use it
        if message.guild in bot.players:
            vc = bot.vc_clients[message.guild]
            mplayer = bot.players[message.guild]
        # Make a player object if we don't
        else:
            vc = bot.vc_clients[message.guild]
            pl = playlist.Playlist(bot)
            print(dir(vc.ws))
            mplayer = player.Player(bot, vc, pl)
            bot.players[message.guild] = mplayer

        # Using the player's qlock, ensuring that always the first received request is queued
        with await mplayer.qlock, message.channel.typing():
            print('\nplay got Q lock\n')

            # If it's a link
            if 'watch?' in song_name:
                info = await bot.downloader.extract_info(bot.loop, song_name, download=False, process=False,
                                                         retry_on_error=True)
                entry, position = mplayer.playlist.add(info['webpage_url'], message.author, message.channel,
                                                       info['title'], info['duration'], effect, info['thumbnail'])
                await message.channel.send("**%s** was added to the queue at position %s, %s" % (
                    entry['title'], position, mplayer.playlist.estimate_time(position, mplayer)))

            # If it's a playlist
            elif 'list' in song_name:
                info = await bot.downloader.extract_info(bot.loop, song_name, download=False, process=False,
                                                         retry_on_error=True)
                preparing_msg = await message.channel.send("Processing playlist...")
                position = await mplayer.playlist.async_pl(info['webpage_url'], message.author, message.channel)
                await preparing_msg.edit("Your playlist was added!")

            # Plain text
            else:
                # If search flag was provided, use ytsearch
                if not searchmode:
                    info = await bot.downloader.extract_info(bot.loop, 'ytsearch1:'+song_name, download=False,
                                                             process=True, retry_on_error=True)
                    entry, position = mplayer.playlist.add(info['entries'][0]['webpage_url'], message.author,
                                                           message.channel, info['entries'][0]['title'],
                                                           info['entries'][0]['duration'], effect,
                                                           info['entries'][0]['thumbnails'][0]['url'], song_name)
                # If not, we're passing it up to extract_info
                else:
                    song = await ytsearch(bot, message, song_name)
                    info = await bot.downloader.extract_info(bot.loop, song[1], download=False, process=False,
                                                             retry_on_error=True)
                    entry, position = mplayer.playlist.add(info['webpage_url'], message.author, message.channel,
                                                           info['title'], info['duration'], effect, info['thumbnail'],
                                                           song_name)
                await message.channel.send("**%s** was added to the queue at position %s, %s" % (
                    entry['title'], position, mplayer.playlist.estimate_time(position, mplayer)))

            # Prepare the entry, music player, its time
            bot.loop.create_task(mplayer.prepare_entry(position - 1))

    @commands.command(aliases=['nowplaying', 'player'])
    async def np(self, ctx):
        """ Display Currently Playing Entry and Progress """
        filled = "▰"
        unfilled = "▱"
        player = self.bot.players[ctx.message.guild]
        if not player.state == 'stopped':
            ps = player.progress
            pt = player.current_entry['duration']
            # Bring the fraction of progress/duration to x/10, to use with progress bars
            filled_bars = round((ps * 10) / pt)
            pstr = str()

            # Populate bars, get it? 'bars' haha kill me
            for i in range(10):
                if (i + 1) > filled_bars:
                    pstr += unfilled
                else:
                    pstr += filled
            song_progress = str(timedelta(seconds=ps)).lstrip('0').lstrip(':')
            song_total = str(timedelta(seconds=pt)).lstrip('0').lstrip(':')
            prog_str = pstr + '  %s / %s' % (song_progress, song_total)

            # Create Embed Response
            np_embed = discord.Embed(title=player.current_entry['title'],
                                     description='added by **%s**' % player.current_entry['author'].name,
                                     url=player.current_entry['url'], colour=0xffffff)
            np_embed.add_field(name='Progress', value=prog_str)
            np_embed.set_image(url=player.current_entry['thumb'])
            np_embed.set_author(name='Now Playing', icon_url=player.current_entry['author'].avatar_url)

            await ctx.message.channel.send(embed=np_embed, delete_after=None)
        else:
            await ctx.message.channel.send("Nothing is playing!")

    @commands.command(aliases=['list', 'q'])
    async def q(self, ctx, *, index: int=None):
        """ List the Current Queue """
        if index:
            index -= 1

        player = self.bot.players[ctx.message.guild]
        printlines = {0: []}
        current_page = 0
        for i, item in enumerate(player.playlist, 1):
            nextline = '{}. {} added by {}\n'.format(i, item['title'], item['author'].name).strip()
            if item == player.current_entry:
                ps = player.progress
                pt = player.current_entry['duration']
                song_progress = str(timedelta(seconds=ps)).lstrip('0').lstrip(':')
                song_total = str(timedelta(seconds=pt)).lstrip('0').lstrip(':')
                prog_str = '[ %s / %s ]' % (song_progress, song_total)
                nextline = "@" + nextline + ' - Currently Playing - ' + prog_str
                if index is None:
                    index = current_page

            currentpagesum = sum(len(x) + 1 for x in printlines[current_page])

            if currentpagesum + len(nextline) + 20 > 2000:
                printlines[current_page].append('```')
                current_page += 1
                printlines[current_page] = []
                printlines[current_page].append('```py')

            printlines[current_page].append(nextline)
        printlines[current_page].append('```')
        if not printlines[0]:
            return await ctx.error('Empty queue! Queue something with `play`')

        if len(printlines.keys()) == 1:
            await ctx.send(''.join(printlines[0]))
            return

        if index not in printlines.keys():
            return await ctx.error(f"The current queue only has pages 1-{len(printlines.keys())}")

        q_msg = await ctx.send(''.join(printlines[index]))
        for emoji in self.reaction_emojis:
            await q_msg.add_reaction(emoji)

        while 1:
            def check(reaction, user):
                return reaction.message.id == q_msg.id and user == ctx.author and \
                       str(reaction.emoji) in self.reaction_emojis
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            except asyncio.TimeoutError:
                await q_msg.delete()
                return

            for emoji in self.reaction_emojis:
                await q_msg.remove_reaction(emoji, ctx.author)

            if str(reaction.emoji) == self.reaction_emojis[0]:
                index = max(0, index-1)
                await q_msg.edit(''.join(printlines[index]))
            elif str(reaction.emoji) == self.reaction_emojis[1]:
                index = min(len(printlines.keys())-1, index+1)
                await q_msg.edit(''.join(printlines[index]))


def setup(bot):
    bot.add_cog(Music(bot))

