class MusicEntry:

    __slots__ = ['title', 'duration', 'url', 'author', 'channel',
                 'lock', 'karaoke', 'thumb', 'search_query', 'is_live', 'filename', 'status']

    def __init__(self, title, duration, url, author, channel,
                 lock, karaoke, thumb, is_live, search_query=None):
        self.title = title
        self.duration = duration
        self.url = url
        self.author = author
        self.channel = channel
        self.lock = lock
        self.karaoke = karaoke
        self.thumb = thumb
        self.search_query = title if search_query is None else search_query
        self.filename = None
        self.status = None
        self.is_live = is_live

