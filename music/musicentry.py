class MusicEntry:

    __slots__ = ['title', 'duration', 'url', 'author', 'channel',
                 'lock', 'effect', 'thumb', 'search_query', 'is_live', 'filename', 'status']

    def __init__(self, url, author, channel, title, duration,
                 lock, effect, thumb, is_live, search_query=None):
        self.title = title
        self.duration = duration
        self.url = url
        self.author = author
        self.channel = channel
        self.lock = lock
        self.effect = effect
        self.thumb = thumb
        self.search_query = title if search_query is None else search_query
        self.filename = None
        self.status = None
        self.is_live = is_live

    def __repr__(self):
        return self.title, self.filename
