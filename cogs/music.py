#!/bin/env python3

import asyncio
import discord

from discord.ext import commands
from utils import playlist
from utils import player
from utils.ytsearch import ytsearch


class Music:

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def play(self, ctx):
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


def setup(bot):
    bot.add_cog(Music(bot))

