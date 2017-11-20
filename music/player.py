import asyncio
import bs4
import collections
import datetime
import discord
import time

from datetime import timedelta
from itertools import islice
from music.musicstate import MusicState
from music.musicstate import EntryState
from music.playlist import Playlist

import os
from os import listdir
from os.path import isfile, join

import subprocess

import win_unicode_console

win_unicode_console.enable()


class Player:
    def __init__(self, bot, voice_client):
        self.bot = bot
        self.voice_client = voice_client

        if os.name == 'nt':
            self.slash = '\\'
        else:
            self.slash = '/'

        self.playlist = Playlist(bot)
        self.current_player = None
        self.current_entry = None
        self.current_livestream = None
        self.start_time = None
        self.skip_votes = []
        self.lock = asyncio.Lock()
        self.qlock = asyncio.Lock()
        self.volume = 1.0
        self.download_lock = asyncio.Lock()
        self.state = MusicState.STOPPED
        self.current_time = None
        self.index = 0
        self.repeat = 0

        self.jump_event = asyncio.Event()
        self.volume_event = asyncio.Event()
        self.seek_event = asyncio.Event()
        # This is just original start time
        self.autoplay = False
        self.EQ = 'normal'

        # This used to heck PEP8, but as a devoted follower of PEP8, i have taken effort to bring this in line with PEP8
        self.EQEffects = {'normal': "",
                          'pop': ' -af equalizer=f=500:width_type=h:w=300:g=2,equalizer=f=1000:width_type=h:w=100:g=3,'
                                 'equalizer=f=2000:width_type=h:w=100:g=-2,equalizer=f=4000:width_type=h:w=100:g=-4,'
                                 'equalizer=f=8000:width_type=h:w=100:g=-4,equalizer=f=16000:width_type=h:w=100:g=-4',
                          'classic': ' -af equalizer=f=250:width_type=h:w=100:g=-6,'
                                     'equalizer=f=1000:width_type=h:w=100:g=1,'
                                     'equalizer=f=4000:width_type=h:w=100:g=6,'
                                     'equalizer=f=8000:width_type=h:w=100:g=6,'
                                     'equalizer=f=16000:width_type=h:w=100:g=6',
                          'jazz': ' -af equalizer=f=250:width_type=h:w=100:g=5,'
                                  'equalizer=f=500:width_type=h:w=100:g=-5,equalizer=f=1000:width_type=h:w=100:g=-2,'
                                  'equalizer=f=2000:width_type=h:w=100:g=2,equalizer=f=4000:width_type=h:w=100:g=-1,'
                                  'equalizer=f=8000:width_type=h:w=100:g=-1,equalizer=f=16000:width_type=h:w=100:g=-1',
                          'rock': ' -af equalizer=f=250:width_type=h:w=100:g=3,'
                                  'equalizer=f=500:width_type=h:w=100:g=-9,equalizer=f=1000:width_type=h:w=100:g=-1,'
                                  'equalizer=f=2000:width_type=h:w=100:g=3,equalizer=f=4000:width_type=h:w=100:g=3,'
                                  'equalizer=f=8000:width_type=h:w=100:g=3,equalizer=f=16000:width_type=h:w=100:g=3',
                          'balanced': ' -af equalizer=f=32:width_type=h:w=100:g=3,'
                                  'equalizer=f=64:width_type=h:w=100:g=2,equalizer=f=500:width_type=h:w=100:g=-1,'
                                  'equalizer=f=1000:width_type=h:w=100:g=-2,equalizer=f=4000:width_type=h:w=100:g=1,'
                                  'equalizer=f=8000:width_type=h:w=100:g=3,equalizer=f=16000:width_type=h:w=100:g=3',
                          'bb': ' -af bass=g=8',
                          'vocals': ' -af compand=.3|.3:1|1:-90/-60|-60/-40|-40/-30|-20/-20:6:0:-90:0.2',
                          'easy': ' -af earwax'
                          }

        self.effects = {'pop': 'Pop', 'classic': 'Classic', 'jazz': 'Jazz', 'rock': 'Rock', 'bb': 'Bass Boost',
                        'normal': 'Normal', 'vocals': 'Vocals', 'balanced': 'Balanced', 'easy': 'Easy Listening'}

    async def reset(self, seektime=None):
        """ Nasty function that makes a player that will play from exactly when it was stopped , this allows us to
        change effects on the fly """

        self.voice_client.stop()
        prog = self.accu_progress

        if self.volume_event.is_set():
            await self.volume_event.wait()
        if self.seek_event.is_set():
            await self.seek_event.wait()

        if seektime is None:
            seektime = datetime.datetime.utcfromtimestamp(prog)

        self.bot.loop.create_task(self.play(str(seektime.strftime('%H:%M:%S.%f')), prog))

    async def prepare_entry(self, ind=None):
        """
        Download/Prepare/Play entries while maintaining sync between the queue,
        a lock is requested before adding play to the loop, so that in
        no case will the voice client be requested to play two AudioSources
        at once. 'ind' is the index of the entry to be prepared/played
        """
        if self.state == MusicState.DEAD:
            return

        with await self.download_lock:

            test_entry = self.playlist.entries[self.index]
            if not self.repeat and not test_entry.is_live:
                if ind is None:
                    if self.state in [MusicState.STOPPED, MusicState.SWITCHING]:
                        if self.current_player is not None and self.voice_client.is_playing():
                            return

                    with await self.lock:
                        self.bot.loop.create_task(self.play())
                        return

                entry = self.playlist.entries[ind]
                with await entry.lock:

                    if entry.status is not None:

                        # If an entry is currently being downloaded, the status is 'processing', so we don't bother
                        # with it and return
                        if entry.status == EntryState.PROCESSING:
                            return
                        elif entry.status == EntryState.DOWNLOADED:
                            with await self.lock:
                                self.bot.loop.create_task(self.play())
                                return
                        else:
                            pass

                    # The filename key isn't added unless an entry passes through this code, so if it doesn't exist, 
                    # download and add the key, this prevents downloading of any entry more than once
                    if entry.filename is None:

                        entry.status = EntryState.PROCESSING
                        result = await self.bot.downloader.extract_info(self.bot.loop, entry.url, download=False)
                        entry.status = EntryState.DOWNLOADED
                        fn = self.bot.downloader.ytdl.prepare_filename(result)
                        onlyfiles = [f for f in listdir(self.bot.downloader.download_folder)
                                     if isfile(join(self.bot.downloader.download_folder, f))]

                        # Check if this has been previously downloaded, why waste bandwidth
                        if not fn.split(self.bot.downloader.download_folder + self.slash)[1] in onlyfiles:
                            x = await entry.channel.send("Caching **%s** :arrow_double_down:" % entry.title,
                                                         delete_after=None)

                            try:
                                await self.bot.downloader.extract_info(self.bot.loop, entry.url, download=True)

                            # If caching does error out, go to a previous index position
                            except:
                                await x.edit(":negative_squared_cross_mark: Error caching **%s**" % entry.title)
                                self.playlist.entries.remove(entry)
                                return
                            await x.edit(content="Done :white_check_mark:", delete_after=2.0)

                        entry.filename = fn

                    # This has some leftover part from async, but basically, only if we're stopped or
                    # switching tracks, latter being the only reason we are in prepare_entry through 
                    # the player, also makes sure to keep the queue in sync by requesting for player's
                    # lock before queueing play to the loop
                    try:
                        if self.state in [MusicState.STOPPED, MusicState.SWITCHING] and not self.voice_client.is_playing():
                            print('\nwas stopped\n')
                            self.bot.loop.create_task(self.play())
                        else:
                            return
                    except AttributeError:
                        if not self.voice_client.is_playing():
                            self.bot.loop.create_task(self.play())

            # We'll be here only when repeat is set to True, just skip everything and queue the same song
            else:
                with await self.lock:
                    self.bot.loop.create_task(self.play())

    async def play(self, seek="00:00:00", seeksec=0):
        """
        Manage Effects, Volume and Seeking,
        makes the voice_client play an FFmpeg AudioSource
        'next' is provided as the functon to be called when
        the source is done playing
        """
        print('lock', self.lock.locked())
        if self.state == MusicState.DEAD or self.voice_client.is_playing():
            return

        # Make a volume string to feed to ffmpeg 
        volumestr = ' -filter:a "volume=%s"' % self.volume

        # This lock is the key to having only one entry being played at once
        #await self.lock.acquire()
        with await self.lock:
            now = self.playlist.entries[self.index]
            with await now.lock:
                print(str(now.is_live))
                # If somehow because of some magical occurences, there's no filename before play is called
                if not now.is_live and now.filename is None:
                    print(now)
                    return

                self.state = MusicState.PLAYING

                if now.effect == 'None':
                    addon = ""
                elif now.effect == 'rape':
                    addon = ""
                    volumestr = ' -filter:a "volume=+36dB"'
                elif now.effect == 'c':
                    addon = ' -af pan="stereo|c0=c0|c1=-1*c1" -ac 1'

                # The biggest problem for me in d.py rewrite, it has no encoder_options that let me set 
                # output channels to 1, allowing this phase cancellation karaoke to work, to remedy this,
                # this now processes a karoke_filename after processing the cancellation and it is saved
                # as a mono track, later when its loaded up into an AudioSource and played, the layout
                # is guessed as mono and Voila! Karaoke
                elif now.effect == 'k':
                    addon = ""
                    onlyfiles = [f for f in listdir(self.bot.downloader.download_folder) if isfile(join(self.bot.downloader.download_folder, f))]
                    if not 'karaoke_' + now.filename.split(self.slash)[1] in onlyfiles:
                        procm = await now.channel.send("Processing karaoke! :microphone:")
                        p1 = subprocess.Popen(
                            ['ffmpeg', '-i', now.filename, '-af', 'pan=stereo|c0=c0|c1=-1*c1', '-ac', '1',
                             now.filename.split(self.slash)[0] + self.slash + 'karaoke_' +
                             now.filename.split(self.slash)[1].split('.')[0] + '.wav'])
                        p1.wait()
                        procm.edit(content="Done! :white_check_mark:")
                    now.filename = now.filename.split(self.slash)[0] + self.slash + 'karaoke_' + \
                        now.filename.split(self.slash)[1].split('.')[0] + '.wav'

                if not now.is_live:
                    ytdl_player = discord.FFmpegPCMAudio(
                        now.filename,
                        before_options="-nostdin -ss %s" % seek,
                        options="-vn -b:a 128k" + addon + volumestr + self.EQEffects[self.EQ])
                else:
                    # The mess here fixes an FFMpeg heck up, they don't send trailing CLRFs with their http requests
                    # So i've manually added a trailing CLRF here
                    # Also no -ss here, seeking doesn't work on livestreams
                    livestreamer = subprocess.Popen(["livestreamer", "-Q", "-O", now.url, "360p"], stdout=subprocess.PIPE)
                    self.current_livestream = livestreamer
                    # '-headers "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/534.24'
                    # '(KHTML, like Gecko) Chrome/11.0.696.3 Safari/534.24"'
                    # "$'\r\n'" + '''"X-Forwarded-For: 0.0.0.0"''' + "$'\r\n'"
                    ytdl_player = discord.FFmpegPCMAudio(
                        livestreamer.stdout,
                        before_options="-nostdin -nostats -loglevel 0 ",
                        options="-vn -b:a 128k" + addon + volumestr + self.EQEffects[self.EQ],
                        pipe=True)

                # So it might seem like you can only set Equalizer and Volume once,
                # the code below facilitates changes at runtime all thanks to FFmpeg,
                # by keeping track of the original start time down to microseconds
                # The Volume,EQ and Seek commands, all stop the player and set a flag
                # for their respective effect to True, telling the player to not move 
                # to the next track when the player is stopped. 'play' is then called
                # again with altered player attributes
                self.current_player = ytdl_player
                self.current_entry = now

                self.voice_client.play(ytdl_player, after=self.next)

                if not self.volume_event.is_set():
                    if seeksec == 0:
                        self.start_time = time.time()
                    else:
                        self.start_time = time.time() - seeksec

                    self.skip_votes = []
                if seek == "00:00:00" and not self.volume_event.is_set():
                    self.bot.loop.create_task(self.manage_nowplaying())

    # Both 'pause' and 'resume' will set current_time so that using the
    # NowPlaying command doesn't change time when the song isn't even playing
    async def pause(self):
        self.state = MusicState.PAUSED
        self.current_time = time.time()
        self.voice_client.pause()

    async def resume(self):
        self.state = MusicState.PLAYING
        self.current_time = time.time()
        self.voice_client.resume()

    async def manage_nowplaying(self):
        if self.state == MusicState.DEAD:
            return

        song_total = str(timedelta(seconds=self.current_entry.duration)).lstrip('0').lstrip(':')
        prog_str = '%s' % song_total
        np_embed = discord.Embed(title=self.current_entry.title,
                                 description='added by **%s**' % self.current_entry.author.name,
                                 url=self.current_entry.url, colour=0xffffff)
        if not self.current_entry.is_live:
            np_embed.add_field(name='Duration', value=prog_str)
        np_embed.add_field(name='Autoplay', value='On' if self.autoplay else 'Off')
        np_embed.add_field(name='Equalizer', value=self.effects[self.EQ])
        if self.current_entry.is_live:
            tm = str(timedelta(seconds=self.current_entry.duration)).lstrip('0').lstrip(':')
            np_embed.add_field(name='Progress', value=("▰"*10)+f" {tm}/ Live :red_circle:", inline=False)
        np_embed.set_image(url=self.current_entry.thumb)
        np_embed.set_author(name='Now Playing', icon_url=self.current_entry.author.avatar_url)

        # Check when the last now playing message was sent, so we can
        # delete it if its older than the last message in that channel,
        # if its the last message on that channel, we just edit it to 
        # display new info
        if self.current_entry.channel.guild in self.bot.np_msgs:
            np_msg = self.bot.np_msgs[self.current_entry.channel.guild]
            async for msg in self.current_entry.channel.history(limit=1):
                if msg != np_msg:
                    try:
                        await np_msg.delete()
                    except discord.Forbidden:
                        pass
                    self.bot.np_msgs[self.current_entry.channel.guild] = None
        try:
            if self.bot.np_msgs[self.current_entry.channel.guild]:
                self.bot.np_msgs[self.current_entry.channel.guild] = await self.bot.np_msgs[
                    self.current_entry.channel.guild].edit(embed=np_embed)
            else:
                self.bot.np_msgs[self.current_entry.channel.guild] = await self.current_entry.channel.send(
                    embed=np_embed, delete_after=None)
        except KeyError:
            self.bot.np_msgs[self.current_entry.channel.guild] = await self.current_entry.channel.send(
                embed=np_embed, delete_after=None)

    # Having a normal function that adds an async function to the loop
    # was my solution to not being able to pass an awaitable to 'after'
    # in 'play', also returns when volume was changed of seeking was done.
    def next(self, error):
        print('in normal next')
        if self.state == MusicState.DEAD or self.volume_event.is_set() or self.seek_event.is_set():
            print('normal next returned')

            if self.volume_event.is_set():
                self.volume_event.clear()

            if self.seek_event.is_set():
                self.seek_event.clear()

            if self.current_livestream is not None:
                self.current_livestream.close()
                self.current_livestream = None
            return
        self.bot.loop.create_task(self.real_next())

    # Checks if there are more entries after our current index, if yes, increase index
    # and call prepare_entry, but if repeat is set to True, the index won't change
    # autoplay is always the last condition to be checked, so manually queued songs
    # will be served before autoplay_manager is called
    async def real_next(self):
        self.state = MusicState.SWITCHING
        if len(collections.deque(islice(self.playlist.entries, self.index, len(self.playlist.entries) - 1))) > 0:
            if not self.repeat and not self.jump_event.is_set():
                self.index += 1
            if self.jump_event.is_set():
                self.jump_event.clear()
            with await self.playlist.entries[self.index].lock:
                self.bot.loop.create_task(self.prepare_entry(self.index))

        elif self.repeat:
            self.bot.loop.create_task(self.prepare_entry(self.index))

        elif self.autoplay:
            if not self.repeat:
                self.index += 1
            self.bot.loop.create_task(self.autoplay_manager())

        else:
            self.index += 1
            self.state = MusicState.STOPPED

    # Following some minimal scraping, autoplay links are pulled
    # at times this might be empty so we just get the other entries below it,
    # Livestreams haven't been implemented yet and i wouldn't want a livestream
    # to interrupt anyone's exploration of youtube either way, so a quick check
    # if the live label on the item exists or not, the entry to be queued
    # is determined.
    async def autoplay_manager(self):
        if self.state == MusicState.DEAD:
            return

        with await self.download_lock:
            async with self.bot.session.get(self.current_entry.url) as resp:
                response = await resp.text()
            soup = bs4.BeautifulSoup(response, "lxml")
            autoplayitems = [a for a in
                             soup.select('div.autoplay-bar div.content-wrapper')]  # a[href^=/watch] a[title^=]
            altitems = [a for a in soup.select('ul#watch-related li div.content-wrapper')]
            altitems.insert(0, autoplayitems[0])
            song_choice = 0

            while 1:
                test = False

                try:
                    for entry in self.playlist.entries:
                        if entry.url.split('/')[3] == \
                                altitems[song_choice].select('a[href^=/watch]')[0].attrs.get('href').split('/')[1]:
                            test = True
                            break
                except (IndexError, KeyError):
                    pass

                if len(altitems[song_choice].select('.yt-badge-live')) or test:
                    song_choice += 1
                else:
                    song_url = 'http://www.youtube.com' + altitems[song_choice].select('a[href^=/watch]')[0].attrs.get(
                        'href')
                    break

            info = await self.bot.downloader.extract_info(self.bot.loop, song_url, download=False, process=True,
                                                          retry_on_error=True)
            entry, position = self.playlist.add(song_url, self.bot.user, self.current_entry.channel, info['title'],
                                                info['duration'], 'None', info['thumbnail'], info['is_live'])

            ap_msg = await self.current_entry.channel.send(
                '**:musical_score: Autoplay:** **%s** has been queued to be played.' % entry.title)
            await asyncio.sleep(7)
            await ap_msg.delete()

        await self.prepare_entry(position - 1)

    # Some redundant stuff below here, accu_progress is only used by
    # effects that need to keep exact track of time, checks if we're paused
    # if not then the real current_time is used.
    @property
    def progress(self):
        if not self.state == MusicState.PAUSED:
            self.current_time = time.time()
        if not self.current_entry.is_live:
            return round(self.current_time - self.start_time)
        else:
            return self.current_entry.duration + round(self.current_time - self.start_time)

    @property
    def accu_progress(self):
        if not self.state == MusicState.PAUSED:
            self.current_time = time.time()
        return self.current_time - self.start_time
