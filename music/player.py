import asyncio
import bs4
import collections
import datetime
import discord
import time
import os
import subprocess
import win_unicode_console

from datetime import timedelta
from itertools import islice
from music.musicstate import MusicState
from music.playlist import Playlist
from utils.votes import ActionVotes

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
        self.current_process = None
        self.start_time = None
        self.votes = ActionVotes()
        self.lock = asyncio.Lock()
        self.qlock = asyncio.Lock()
        self.volume = 1.0
        self.download_lock = asyncio.Lock()
        self.state = MusicState.STOPPED
        self.current_time = None
        self.index = 0
        self.repeat = 0

        self.jump_event = asyncio.Event()
        self.jump_return = None
        self.volume_event = asyncio.Event()
        self.seek_event = asyncio.Event()
        self.timeout_handle = None

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
                          'easy': ' -af earwax',
                          'live': ' -af extrastereo'
                          }

        self.effects = {'pop': 'Pop', 'classic': 'Classic', 'jazz': 'Jazz', 'rock': 'Rock', 'bb': 'Bass Boost',
                        'normal': 'Normal', 'vocals': 'Vocals', 'balanced': 'Balanced', 'easy': 'Easy Listening',
                        'live': 'Live'}

    async def reset(self, seektime=None, prog=None):
        """ Nasty function that makes a player that will play from exactly when it was stopped , this allows us to
        change effects on the fly """

        self.voice_client.stop()
        if prog is None:
                prog = self.accu_progress

        if self.volume_event.is_set():
            await self.volume_event.wait()
        if self.seek_event.is_set():
            await self.seek_event.wait()

        if seektime is None:
            seektime = datetime.datetime.utcfromtimestamp(prog)

        self.bot.loop.create_task(self.play(str(seektime.strftime('%H:%M:%S.%f')), prog))

    async def play(self, seek=None, seeksec=0):
        """
        Manage Effects, Volume and Seeking,
        makes the voice_client play an FFmpeg AudioSource
        'next' is provided as the functon to be called when
        the source is done playing
        """
        if self.state == MusicState.DEAD or self.voice_client.is_playing():
            return
        if self.timeout_handle is not None:
            self.timeout_handle.cancel()
        # Make a volume string to feed to ffmpeg
        volumestr = ' -filter:a "volume=%s"' % self.volume

        # This lock is the key to having only one entry being played at once
        with await self.lock:
            now = self.playlist.entries[self.index]
            with await now.lock:
                self.state = MusicState.PLAYING

                if now.effect == 'None':
                    addon = ""
                    i_addon = ""

                # If karaoke mode
                if now.effect == 'k':
                    # Youtube-DL pipes download to ffmpeg#1, ffmpeg #1 outputs data with phase cancellation
                    # and in opus format to pipe, this is piped into our normal FFmpegPCMAudio
                    # Why not just use the -af filter and output one channel in the main ffmpeg?
                    # d.py has channels set to 2 as default on player/voice_client, so from ffmpeg#1
                    # data goes out as one channel, now this is interpreted as two channels and split equally
                    # by ffmpeg#2, if this method isnt used, a phase cancellation will occur, but with a tempo
                    # and pitch increase

                    # if karaoke was asked for on a livestream, not sure why but uhm its just here
                    if now.is_live:
                        stream_process = subprocess.Popen(["livestreamer", "-Q", "-O", now.url, "360p"],
                                                          stdout=subprocess.PIPE
                                                          )
                    # Normal karaoke, no live
                    else:
                        stream_process = subprocess.Popen(["youtube-dl", now.url, "--quiet", "--no-warnings",
                                                          "--no-check-certificate", "-f", "bestaudio/best", "-o", "-"],
                                                          stdout=subprocess.PIPE
                                                          )

                    ff2_process = subprocess.Popen(['ffmpeg', '-i', '-', '-nostdin', '-f', 'opus', '-af',
                                                   'pan=stereo|c0=c0|c1=-1*c1', '-ac', '1', '-'],
                                                   stdout=subprocess.PIPE, stdin=stream_process.stdout
                                                   )
                    self.current_process = ff2_process
                    await asyncio.sleep(1.5)
                    ytdl_player = discord.FFmpegPCMAudio(
                        ff2_process.stdout,
                        before_options=f"-nostdin{' -ss '+seek if seek is not None else ''}",
                        options="-acodec pcm_s16le" + volumestr + self.EQEffects[self.EQ],
                        pipe=True)

                # Normal track no live
                elif not now.is_live:
                    # Have youtube-dl handle downloading rather than ffmpeg , again cause ffmpeg is just bad at it
                    stream_process = subprocess.Popen(["youtube-dl", now.url, "--quiet", "--no-warnings",
                                                       "--no-check-certificate", "-f", "bestaudio/best", "-o", "-"],
                                                      stdout=subprocess.PIPE)
                    self.current_process = stream_process
                    await asyncio.sleep(1.5)
                    ytdl_player = discord.FFmpegPCMAudio(
                        stream_process.stdout,
                        before_options=f"-nostdin{' -ss '+seek if seek is not None else ''}",
                        options="-acodec pcm_s16le -vn -b:a 128k" + addon + volumestr + self.EQEffects[self.EQ],
                        pipe=True)

                # Livestream
                else:
                    # Also no -ss here, seeking doesn't work on livestreams
                    # Handle downloading through livestreamer for multithreaded downloading, manual pipe to source
                    livestreamer = subprocess.Popen(["livestreamer", "-Q", "-O", now.url, "360p"], stdout=subprocess.PIPE)
                    self.current_process = livestreamer

                    ytdl_player = discord.FFmpegPCMAudio(
                        livestreamer.stdout,
                        before_options="-nostdin -nostats -loglevel 0 ",
                        options="-acodec pcm_s16le -vn -b:a 128k" + addon + volumestr + self.EQEffects[self.EQ],
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

                if seek is None and not self.volume_event.is_set():
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
                                 url=self.current_entry.webpage_url, colour=0xffffff)
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

            if self.current_process is not None:
                # RIP
                self.current_process.kill()
                if self.current_process.poll() is None:
                    # Murder
                    self.current_process.communicate()

                self.current_process = None
            return
        self.bot.loop.create_task(self.real_next())

    # Checks if there are more entries after our current index, if yes, increase index
    # and call prepare_entry, but if repeat is set to True, the index won't change
    # autoplay is always the last condition to be checked, so manually queued songs
    # will be served before autoplay_manager is called
    def _jump_check(self):
        if self.jump_event.is_set():
            self.jump_event.clear()
            try:
                self.index = self.jump_event.index
                print('setting')
            except AttributeError:
                pass
            if self.jump_return is not None:
                self.jump_return.set()
                self.jump_return = None

    def _timeout_dc(self):
        self.bot.loop.create_task(self._dc())

    async def _dc(self):
        if self.state == MusicState.DEAD:
            return
        await self.current_entry.channel.send("The bot has been inactive for 10 minutes, it will now disconnect.")
        self.state = MusicState.DEAD
        self.bot.players.pop(self.voice_client.guild)
        await self.bot.vc_clients.pop(self.voice_client.guild).disconnect(force=True)

    async def real_next(self):
        self.state = MusicState.SWITCHING
        if len(collections.deque(islice(self.playlist.entries, self.index, len(self.playlist.entries) - 1))) > 0:
            if not self.repeat and not self.jump_event.is_set():
                self.index += 1
            self._jump_check()
            with await self.playlist.entries[self.index].lock:
                self.bot.loop.create_task(self.play())

        elif self.repeat:
            self.bot.loop.create_task(self.play())

        elif self.autoplay:
            if not self.repeat:
                self.index += 1
                self._jump_check()
            self.bot.loop.create_task(self.autoplay_manager())

        else:
            if self.jump_event.is_set():
                self._jump_check()
                self.bot.loop.create_task(self.play())
            else:
                self.index += 1
                self.state = MusicState.STOPPED
                self.timeout_handle = self.bot.loop.call_later(600, self._timeout_dc)

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
            async with self.bot.session.get(self.current_entry.webpage_url) as resp:
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
                        if entry.webpage_url.split('/')[3] == \
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
            entry, position = self.playlist.add(info['url'], song_url, self.bot.user, self.current_entry.channel, info['title'],
                                                info['duration'], 'None', info['thumbnail'], info['is_live'])

            ap_msg = await self.current_entry.channel.send(
                '**:musical_score: Autoplay:** **%s** has been queued to be played.' % entry.title)
            await asyncio.sleep(7)
            await ap_msg.delete()

        await self.play()

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
