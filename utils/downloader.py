import os
import functools
import youtube_dl
from concurrent.futures import ThreadPoolExecutor
ytdl_format_options = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True
}
youtube_dl.utils.bug_reports_message = lambda: ''


class Downloader:
    def __init__(self, download_folder=None):
        self.thread_pool = ThreadPoolExecutor()
        self.ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
        self.download_folder = download_folder
        self.ytdl.params['outtmpl'] = os.path.join(download_folder, self.ytdl.params['outtmpl'])

    async def extract_info(self, loop, *args, on_error=None, retry_on_error=False, **kwargs):
        return await loop.run_in_executor(self.thread_pool, functools.partial(self.ytdl.extract_info, *args, **kwargs))
