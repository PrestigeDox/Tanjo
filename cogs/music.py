#!/bin/env python3

import asyncio
import discord

from collections import defaultdict
from datetime import timedelta
from discord.ext import commands
from music.musicstate import MusicState
from music.player import Player
from music.ytsearch import ytsearch


class Music:

    def __init__(self, bot):
        self.bot = bot
        self.reaction_emojis = ['⬅', '➡']
        self.color = bot.user_color

    async def _queue(self, ctx, song_name, effect, searchmode=0):
        """ Exists separately solely to be able to use subcommands """
        message = ctx.message
        bot = self.bot

        # Handle funky embed connecting
        if message.guild not in bot.vc_clients:
            np_embed = discord.Embed(title='Connecting...', colour=self.color)
            np_embed.set_thumbnail(url='https://imgur.com/3QIBGl3.png')
            trying_msg = await ctx.send(embed=np_embed)

            # Error if you're trying to listen music out of thin air/not in a voice channel
            if message.author.voice is None:
                np_embed = discord.Embed(title='Error', description='You are not in a voice channel', colour=self.color)
                np_embed.set_thumbnail(url='https://imgur.com/B9YlwWt.png')
                await trying_msg.edit(embed=np_embed)
                return

            # This timeout never triggers, not sure
            try:
                vc = await message.author.voice.channel.connect(timeout=6.0, reconnect=True)
            except asyncio.TimeoutError:
                np_embed = discord.Embed(title='Error', description="Wasn't able to connect, please try again!",
                                         colour=self.color)
                np_embed.set_thumbnail(url='https://imgur.com/KQp2PUQ.png')
                await trying_msg.edit(embed=np_embed)
                return
            bot.vc_clients[message.guild] = vc
            np_embed = discord.Embed(title='Bound to ' + message.author.voice.channel.name,
                                     description='summoned by **%s**' % message.author.mention, colour=self.color)
            np_embed.set_thumbnail(url='https://imgur.com/kVlJSXg.png')
            await trying_msg.edit(embed=np_embed)

        # Smart way to go through the message and find out what's a flag and where our song name starts from
        # for n, item in enumerate(message.content.split()[1:], 1):
        #     if not item.startswith('-'):
        #         break
        #
        # song_name = ' '.join(message.content.split()[n+1:])

        # If we already have a player for this server, use it
        if message.guild in bot.players:
            vc = bot.vc_clients[message.guild]
            mplayer = bot.players[message.guild]
        # Make a player object if we don't
        else:
            vc = bot.vc_clients[message.guild]
            print(dir(vc.ws))
            mplayer = Player(bot, vc)
            bot.players[message.guild] = mplayer

        # Using the player's qlock, ensuring that always the first received request is queued
        with await mplayer.qlock, ctx.channel.typing():
            print('\nplay got Q lock\n')

            # If it's a link
            if 'watch?' in song_name:
                info = await bot.downloader.extract_info(bot.loop, song_name, download=False, process=False,
                                                         retry_on_error=True)
                if info['is_live']:
                    url = info['webpage_url']
                else:
                    url = info['url']

                entry, position = mplayer.playlist.add(url, info['webpage_url'], message.author, message.channel,
                                                       info['title'], info['duration'], effect, info['thumbnail'],
                                                       info['is_live'])
                await ctx.send("**%s** was added to the queue at position %s, %s" % (
                    entry.title, position, mplayer.playlist.estimate_time(position, mplayer)))

            # If it's a playlist
            elif 'list' in song_name:
                info = await bot.downloader.extract_info(bot.loop, song_name, download=False, process=False,
                                                         retry_on_error=True)
                preparing_msg = await ctx.send("Processing playlist...")
                entries, bad_entries = await mplayer.playlist.async_pl(info['webpage_url'], message.author,
                                                                       message.channel)
                lst_bad = '\n'.join(bad_entries)

                # 1-1=0, not 0 = 1, so, that means its one entry, so, entr'y', if not, entr'ies'
                base_pl = f"{entries} entr{'y' if not entries-1 else 'ies'} added!"

                if bad_entries:
                    bad_pl = f"\nEntr{'y' if not len(bad_entries)-1 else 'ies'} that couldn't be added:\n{lst_bad}"

                await preparing_msg.edit(base_pl + bad_pl if bad_entries else base_pl)

            # Plain text
            else:
                # If search flag was provided, use ytsearch
                if not searchmode:
                    info = await bot.downloader.extract_info(bot.loop, 'ytsearch1:'+song_name, download=False,
                                                             process=True, retry_on_error=True)
                    if info['entries'][0]['is_live']:
                        url = info['entries'][0]['webpage_url']
                    else:
                        url = info['entries'][0]['url']
                    entry, position = mplayer.playlist.add(url,info['entries'][0]['webpage_url'], message.author,
                                                           message.channel, info['entries'][0]['title'],
                                                           info['entries'][0]['duration'], effect,
                                                           info['entries'][0]['thumbnails'][0]['url'],
                                                           info['entries'][0]['is_live'], song_name)
                # If not, we're passing it up to extract_info
                else:
                    song = await ytsearch(bot, message, song_name)
                    info = await bot.downloader.extract_info(bot.loop, song[1], download=False, process=False,
                                                             retry_on_error=True)
                    if info['is_live']:
                        url = info['webpage_url']
                    else:
                        url = info['url']

                    entry, position = mplayer.playlist.add(url, info['webpage_url'], message.author, message.channel,
                                                           info['title'], info['duration'], effect, info['thumbnail'],
                                                           info['is_live'], song_name)
                await ctx.send("**%s** was added to the queue at position %s, %s" % (
                    entry.title, position, mplayer.playlist.estimate_time(position, mplayer)))

            # Prepare the entry, music player, its time
            bot.loop.create_task(mplayer.play())

    @commands.group(invoke_without_command=True)
    async def play(self, ctx, *, song_name):
        """ Add a song to the playlist """
        await self._queue(ctx, song_name, 'None')

    @play.command(aliases=['-k'])
    async def karaoke(self, ctx, *, song_name):
        """ Add a song to the playlist in karaoke mode """
        await self._queue(ctx, song_name, 'k')

    @play.command(aliases=['-s'])
    async def search(self, ctx, *, song_name):
        """ Search for a song on YouTube """
        await self._queue(ctx, song_name, 'None', 1)

    @commands.command(aliases=['nowplaying', 'player'])
    async def np(self, ctx):
        """ Display currently playing track and progress """
        filled = "▰"
        unfilled = "▱"
        player = self.bot.players[ctx.message.guild]
        if not player.state == MusicState.STOPPED:
            ps = player.progress
            pt = player.current_entry.duration
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
            np_embed = discord.Embed(title=player.current_entry.title,
                                     description='added by **%s**' % player.current_entry.author.name,
                                     url=player.current_entry.webpage_url, colour=self.color)
            np_embed.add_field(name='Autoplay', value='On' if player.autoplay else 'Off')
            np_embed.add_field(name='Equalizer', value=player.effects[player.EQ])
            if not player.current_entry.is_live:
                np_embed.add_field(name='Progress', value=prog_str)
            else:
                np_embed.add_field(name='Progress', value=(filled * 10) + f" {song_progress}/ Live :red_circle:")
            np_embed.set_image(url=player.current_entry.thumb)
            np_embed.set_author(name='Now Playing', icon_url=player.current_entry.author.avatar_url)

            await ctx.send(embed=np_embed, delete_after=None)
        else:
            await ctx.send("Nothing is playing!")

    @commands.command(aliases=['list', 'q'])
    async def queue(self, ctx, *, index: int=None):
        """ List the current queue """
        if index:
            index -= 1

        player = self.bot.players[ctx.message.guild]
        printlines = defaultdict(list)
        printlines[0].append('```py')
        current_page = 0
        for i, item in enumerate(player.playlist, 1):
            nextline = '{}. {} added by {}\n'.format(i, item.title, item.author.name).strip()
            if item == player.current_entry:
                ps = player.progress
                pt = player.current_entry.duration
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
                printlines[current_page].append('```py')

            printlines[current_page].append(nextline)
        printlines[current_page].append('```')
        if not printlines[0]:
            return await ctx.error('Empty queue! Queue something with `play`')

        if len(printlines.keys()) == 1:
            print(printlines)
            await ctx.send('\n'.join(printlines[0]))
            return

        if index not in printlines.keys():
            return await ctx.error(f"The current queue only has pages 1-{len(printlines.keys())}")

        printlines[index].insert(len(printlines[index]) - 1, f'\nPage: {index+1}/{len(printlines.keys())}')
        q_msg = await ctx.send('\n'.join(printlines[index]))
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
                await q_msg.edit(content=''.join(printlines[index]))
            elif str(reaction.emoji) == self.reaction_emojis[1]:
                index = min(len(printlines.keys())-1, index+1)
                await q_msg.edit(content=''.join(printlines[index]))

    @commands.command(aliases=['leave', 'destroy', 'dc'])
    async def disconnect(self, ctx):
        """ Make the bot leave your voice channel """
        try:
            player = self.bot.players[ctx.message.guild]
            player.state = MusicState.DEAD
            self.bot.players.pop(ctx.message.guild)
        except KeyError:
            return

        await self.bot.vc_clients.pop(ctx.message.guild).disconnect()

        em = discord.Embed(title="Disconnected", description="by " + ctx.message.author.mention, colour=self.color)
        em.set_thumbnail(url="https://imgur.com/4me8pGr.png")
        await ctx.send(embed=em)

    @commands.command(aliases=['equalizer'])
    async def eq(self, ctx, *, eq: str=None):
        """ Choose from a multitude of equalizer effects to enhance your music """
        player = self.bot.players[ctx.message.guild]

        if eq is None:
            eq_list = '\n'.join([f"`{effect}` - {full_name}" for effect, full_name in player.effects.items()])
            return await ctx.send(f'Available EQ Effects are:\n{eq_list}')

        eq = 'normal' if eq.lower() == 'reset' else eq

        if not eq.lower() in player.effects.keys():
            return await ctx.error(f"{eq}, is not a valid EQ effect.")

        player.EQ = eq.lower()
        if player.voice_client.is_playing():
            player.volume_event.set()
            await player.reset()
        em = discord.Embed(title="Equalizer",
                           description=f":loud_sound: Equalizer has been set to {player.effects[eq.lower()]}.",
                           color=self.color)
        await ctx.send(embed=em)

    @commands.command(aliases=['auto'])
    async def autoplay(self, ctx):
        """ Enable the autoplay feature to queue songs based on your queue """
        player = self.bot.players[ctx.message.guild]
        if player.autoplay:
            player.autoplay = False
            await ctx.send("**:musical_score: Autoplay:** Stopped")
        else:
            player.autoplay = True
            await ctx.send("**:musical_score: Autoplay:** Started")

    @commands.command(aliases=['pick'])
    async def jump(self, ctx, *, pickno: int=None):
        """ Jump to any index in the queue """
        player = self.bot.players[ctx.message.guild]

        if pickno is None:
            return await ctx.error("Invalid Input!")

        if pickno - 1 < 0 or pickno > len(player.playlist.entries):
            return await ctx.error(f"Value can only be between 1 and {len(player.playlist.entries)}")

        player.index = pickno - 1
        if not player.voice_client.is_playing() and not player.state == MusicState.PAUSED:
            self.bot.loop.create_task(player.play())
            await ctx.send(f"Jumping to **{pickno}**!")
        else:
            player.jump_event.set()
            await ctx.send(f"Will jump to **{pickno}** after the current track finishes playing!")

    @commands.command(aliases=['remove', 'rm'])
    async def rmsong(self, ctx, *, index: int=None):
        """ Remove a song from the queue """
        player = self.bot.players[ctx.message.guild]
        if index is None:
            return await ctx.error(f"Please provide a valid index number between 1 and {len(player.playlist.entries)}")
        track = player.playlist.get_track(index)
        player.playlist.remove(index)
        await ctx.send(f"**{track.title}** was removed from your playlist!")

    @commands.command()
    async def pause(self, ctx):
        """ Pause the player if it's playing """
        player = self.bot.players[ctx.message.guild]
        if player.state == MusicState.PLAYING:
            await player.pause()

    @commands.command()
    async def resume(self, ctx):
        """ Resume the player if it's paused """
        player = self.bot.players[ctx.message.guild]
        if player.state == MusicState.PAUSED:
            await player.resume()

    @commands.command()
    async def seek(self, ctx, *, seektime: str=None):
        """ Seek to a certain point in a track """
        if seektime is None:
            return await ctx.error("Please provide time to seek to in the format, `hh:mm:ss``!")

        player = self.bot.players[ctx.message.guild]

        if player.current_entry.is_live:
            return await ctx.error("Can't seek on a livestream!")

        duration = player.current_entry.duration
        timelist = seektime.split(':')

        if not len(timelist) == 3:
            return await ctx.error("Please provide time to seek to in the format, `hh:mm:ss``!")

        seek_seconds = int(timelist[0])*60*60 + int(timelist[1])*60 + int(timelist[2])
        if int(seek_seconds) > duration:
            return await ctx.error(f"Value can only be between 00:00:00 and {str(timedelta(seconds=duration))}")

        player.seek_event.set()
        player.reset(seektime, seek_seconds)
        await ctx.send(f"Seeking to {seektime}")
    
    @commands.command()
    async def skip(self, ctx):
        """ Add votes to skip a track """
        player = self.bot.players[ctx.message.guild]
        if not player.voice_client.is_playing():
            return await ctx.error("Nothing is playing to skip!")
        else:
            if player.current_entry.author == ctx.message.author:
                await ctx.send(f"**{player.current_entry.title}**"
                               f"was skipped by it's author, {player.current_entry.author}!"
                               )
                player.voice_client.stop()
            else:
                if ctx.message.author not in player.skip_votes:
                    num_voice = sum(1 for m in ctx.message.author.voice.channel.members if not (
                        m.voice.deaf or m.voice.self_deaf or m.id == self.bot.user.id))
                    player.skip_votes.append(ctx.message.author)
                    current_votes = len(player.skip_votes)
                    required_votes = round(num_voice * (2 / 3))
                    await ctx.send(
                        f"Your vote was added!\n**{current_votes}/{required_votes}**" 
                        "skip votes recieved, song will be skipped upon meeting requirements")
                    if current_votes >= required_votes:
                        await ctx.send(
                            f"**{player.current_entry.title}** was skipped upon meeting skip vote requirements!")
                        player.voice_client.stop()
                    else:
                        await ctx.send(
                            f"You have already voted to skip **{player.current_entry.title}**,"
                            "wait till more votes arrive!"
                            )

    @commands.command()
    async def volume(self, ctx, *, volume: float=None):
        """ Set the player's volume between 0.0 and 2.0 """
        if volume is None:
            return await ctx.error("Please provide volume between 0.0 and 2.0")

        player = self.bot.players[ctx.message.guild]
        if 0 <= volume <= 2.0:
            player.volume = volume
            em = discord.Embed(title="Volume changed!", description=f":loud_sound: New volume is {volume}")
            await ctx.send(embed=em)
            if player.voice_client.is_playing():
                player.volume_event.set()
                await player.reset()
        else:
            return await ctx.error("Volume value can only range from 0.0-2.0")

    @commands.command()
    async def repeat(self, ctx):
        """ Put a track from the queue on repeat """
        player = self.bot.players[ctx.message.guild]
        if not player.voice_client.is_playing():
            await ctx.send("Nothing is playing to repeat!")
        else:
            if player.repeat:
                player.repeat = 0
                await ctx.send(f":negative_squared_cross_mark: **{player.current_entry.title}**,"
                               "has been taken off repeat.")
            else:
                player.repeat = 1
                await ctx.send(f":arrows_counterclockwise: **{player.current_entry.title}**, has been set to repeat,"
                               "till the end of time itself!\nUse this command again to interrupt the repetition."
                               )


def setup(bot):
    bot.add_cog(Music(bot))

