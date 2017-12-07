#!/bin/env python3

import asyncio
import discord
import json

from collections import defaultdict
from datetime import timedelta
from discord.ext import commands
from itertools import chain
from music.musicstate import MusicState
from music.player import Player
from music.ytsearch import ytsearch
from utils.votes import Votes
from utils import db as tanjo


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
                vc = await message.author.voice.channel.connect(timeout=6.0)
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
                    info = await bot.downloader.extract_info(bot.loop, song[1], download=False, process=True,
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

    @commands.command(aliases=['summon', 'listen'])
    async def join(self, ctx):
        """ Call the bot to your voice channel """

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
        if not player.playlist.entries:
            return await ctx.error('Empty queue! Queue something with `play`')

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
                await q_msg.edit(content='\n'.join(printlines[index]))
            elif str(reaction.emoji) == self.reaction_emojis[1]:
                index = min(len(printlines.keys())-1, index+1)
                await q_msg.edit(content='\n'.join(printlines[index]))

    @commands.command(aliases=['leave', 'destroy', 'dc'])
    async def disconnect(self, ctx):
        """ Make the bot leave your voice channel """
        player = self.bot.players.get(ctx.message.guild)
        if player is None:
            return await ctx.error('A player for this guild does not exist')

        users = sum(1 for m in ctx.author.voice.channel.members if not (
                    m.voice.deaf or m.voice.self_deaf or m.id == self.bot.user.id))

        if users == 2:
            req = 2
        else:
            req = round((2/3)*users)

        if users == 1:
            pass
        elif discord.utils.get(ctx.author.roles, name='DJ'):
            pass
        else:
            votes = player.votes.disconnect
            if votes.add_vote(ctx.author.id):
                await ctx.send(f"Your vote to disconnect was added!\n*{votes.total_votes}/{req} votes received.*")
            else:
                return await ctx.send("You have already voted for the bot to disconnect.\n"
                                      f"*{votes.total_votes}/{req} votes received.*")
            if votes.is_passed(req):
                await ctx.send("Vote requirements were fulfilled, the bot will now disconnect.")
                pass
            else:
                return

        try:
            player.state = MusicState.DEAD
            self.bot.players.pop(ctx.message.guild)
        except KeyError:
            return

        await self.bot.vc_clients.pop(ctx.message.guild).disconnect()

        em = discord.Embed(title="Disconnected", colour=self.color)
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

    async def _jump(self, ctx, player, index: int=None):
        if player is None:
            await ctx.error('A player for this guild does not exist')
            return False

        if index - 1 < 0 or index > len(player.playlist.entries):
            await ctx.error(f"Value can only be between 1 and {len(player.playlist.entries)}")
            return False

        if index is None:
            await ctx.error("Please provide the position you want to jump to")
            return False
        else:
            index = index-1

        try:
            entry = player.playlist.entries[index]
        except IndexError:
            await ctx.error(f"No entry was found at position {index}")
            return False

        users = sum(1 for m in ctx.author.voice.channel.members if not (
                    m.voice.deaf or m.voice.self_deaf or m.id == self.bot.user.id))

        if users == 2:
            req = 2
        else:
            req = round((2/3)*users)

        if users == 1:
            pass
        elif discord.utils.get(ctx.author.roles, name='DJ'):
            pass
        else:
            votes = player.votes.jump
            if votes is None:
                votes = player.votes.jump = Votes(index)
            elif votes.for_item == index:
                pass
            else:
                await ctx.error(f"A vote to jump to {votes.for_item+1} is already active")
                return False

            if votes.add_vote(ctx.author.id):
                await ctx.send(f"Your vote to skip **{entry.title}** was added!\n"
                               f"*{votes.total_votes}/{req} votes received.*")
            else:
                await ctx.send(f"You have already voted to jump **{entry.title}**.\n"
                               f"*{votes.total_votes}/{req} votes received.*")
                return False
            if votes.is_passed(req):
                await ctx.send(f"Vote requirements were fulfilled, **{entry.name}** will be skipped.")
                player.votes.skip.remove(votes)
                pass
            else:
                return

        if not player.voice_client.is_playing() and not player.state == MusicState.PAUSED:
            player.index = index
            player.jump_event.set()
            self.bot.loop.create_task(player.play())
            await ctx.send(f"Jumping to **{index+1}**!")
        else:
            player.jump_event.set()
            player.jump_event.index = index
            await ctx.send(f"Will jump to **{index+1}** after the current track finishes playing!")

    @commands.group(invoke_without_command=True, aliases=['pick'])
    async def jump(self, ctx, *, index: int=None):
        """ Jump to any index in the queue """
        player = self.bot.players.get(ctx.message.guild)
        await self._jump(ctx, player, index)

    @staticmethod
    async def _wait_player(player):
        return_event = asyncio.Event()
        player.jump_return = return_event
        player.jump_event.set()
        await return_event.wait()

    @jump.command(name='return')
    async def jump_return(self, ctx, *, index: int=None):
        player = self.bot.players.get(ctx.message.guild)
        if not player.voice_client.is_playing() and not player.state == MusicState.PAUSED:
            return await ctx.error("Cant use `return` on a finished queue, use `jump` instead.")
        current_index = player.index
        await self._jump(ctx, player, index)
        await self._wait_player(player)
        print('return event awoken')

        player.jump_event.set()
        player.jump_event.index = current_index

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
    
    @commands.command(aliases=['remove', 'rm'])
    async def skip(self, ctx, *, index: int=None):
        """ Add votes to skip a track """
        player = self.bot.players.get(ctx.message.guild)
        if player is None:
            return await ctx.error('A player for this guild does not exist')

        if not player.voice_client.is_playing():
            return await ctx.error("Nothing is playing to skip!")

        if index is None:
            index = player.index

        try:
            entry = player.playlist.entries[index]
        except IndexError:
            return await ctx.error(f"No entry was found at position {index}")

        users = sum(1 for m in ctx.author.voice.channel.members if not (
                    m.voice.deaf or m.voice.self_deaf or m.id == self.bot.user.id))

        if users == 2:
            req = 2
        else:
            req = round((2/3)*users)

        if users == 1:
            pass
        elif discord.utils.get(ctx.author.roles, name='DJ'):
            pass
        else:
            votes = discord.utils.get(player.votes.skip, for_item=index)
            if votes is None:
                votes = Votes(index)
                player.votes.skip.append(votes)
            if votes.add_vote(ctx.author.id):
                await ctx.send(f"Your vote to skip **{entry.name}** was added!\n"
                               f"*{votes.total_votes}/{req} votes received.*")
            else:
                return await ctx.send(f"You have already voted to skip **{entry.title}**.\n"
                                      f"*{votes.total_votes}/{req} votes received.*")
            if votes.is_passed(req):
                await ctx.send(f"Vote requirements were fulfilled, **{entry.title}** will be skipped.")
                player.votes.skip.remove(votes)
                pass
            else:
                return

        if entry == player.current_entry:
            player.voice_client.stop()
        else:
            player.playlist.entries.remove(index)

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

    @commands.group()
    async def playlist(self, ctx):
        pass

    async def _update(self, author_id, entries: list):
        async with self.bot.conn_pool.acquire() as conn:
            user = await tanjo.fetch_user(conn, author_id)
            if user['playlist'] is not None:
                user_pl = json.loads(user['playlist'])
            else:
                user_pl = []

            for entry in entries:
                user_pl.append({"title": entry.title, "url": entry.url})

            await conn.execute('UPDATE users SET playlist=$1 WHERE id=$2', json.dumps(user_pl), author_id)

    async def _get_pl(self, author_id):
        async with self.bot.conn_pool.acquire() as conn:
            user = await tanjo.fetch_user(conn, author_id)
            if user['playlist'] is not None:
                user_pl = json.loads(user['playlist'])
            else:
                user_pl = []
            return user_pl

    @staticmethod
    def _numparse(nums):
        def parse_range(num):
            # Split into start and end if its a range
            # '7' = ['7'] but '7-9' = ['7','9'].
            parts = num.split('-')
            parts = [int(i) for i in parts]
            start = parts[0]

            # If its not a range, it starts and ends on itself, so its parsed as a single number in the chain.
            end = start if len(parts) == 1 else parts[1]

            # re-assign to support reverse ranges cause why not.
            if start > end:
                end, start = start, end

            # return as a range to feed to chain.
            return range(start, end + 1)

        # Chain iters over the range()s parse_range returns, set excludes repeated nums and sorted is QoL.
        return sorted(set(chain(*[parse_range(num) for num in nums.split(',')])))

    @playlist.command()
    async def add(self, ctx, *, index: str=None):
        """Add a song to your personal playlist"""
        player = self.bot.players.get(ctx.guild)
        if player is None:
            return await ctx.error("There is no active player to add tracks from.")

        if index is None:
            return await ctx.error("The argument passed should be an index and/or ranges separated by commas "
                                   "from the current queue\nExample:\n"f"{ctx.prefix}add 1,2,7-9")
        try:
            indexes = self._numparse(index)
        except ValueError:
            return await ctx.error("An invalid range was supplied")
        for entry_inx in indexes:
            try:
                entry = player.playlist.entries[entry_inx-1]
                await self._update(ctx.author.id, [entry])
            except IndexError:
                indexes.remove(entry_inx)

        em = discord.Embed(title="Personal Playlist", color=discord.Color.dark_orange())
        em.add_field(name="Successfully added", value='\n'.join([f"{ind}. {player.playlist.entries[ind-1].title}"
                                                                 for ind in indexes]))
        await ctx.send(embed=em)

    @playlist.command(name="play")
    async def pl_play(self, ctx, *, index: str=None):
        player = self.bot.players.get(ctx.guild)
        if player is None:
            return await ctx.error("There is no active player to add tracks from.")

        if index is None:
            return await ctx.error("The argument passed should be an index and/or ranges separated by commas "
                                   "from the current queue\nExample:\n"f"{ctx.prefix}add 1,2,7-9")
        try:
            indexes = self._numparse(index)
        except ValueError:
            return await ctx.error("An invalid range was supplied")

        pl = await self._get_pl(ctx.author.id)
        if not pl:
            return await ctx.error("That's an empty playlist, add tracks to your playlist, then try this again.")

        for entry_inx in indexes:
            try:
                entry = pl[entry_inx-1]
                await self._queue(ctx, entry['url'], 'None')
            except IndexError:
                indexes.remove(entry_inx)


def setup(bot):
    bot.add_cog(Music(bot))

