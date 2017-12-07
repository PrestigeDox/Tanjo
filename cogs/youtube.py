import discord
from bs4 import BeautifulSoup
from discord.ext import commands


class YouTube:
    def __init__(self, bot):
        self.bot = bot
        self.session = bot.session
        # This header makes the youtube page easier to scrape w/ less data
        self.headers = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 4.01; Windows CE; Sprint:SCH-i320; '
                                      'Smartphone; 176x220)'}
        self.uri = 'https://m.youtube.com/results'

    @staticmethod
    def get_yt_items(html: str, limit: int = 1) -> list:
        """ Small wrapper for yt scraping """ 
        soup = BeautifulSoup(html, 'lxml')

        # Some people might call this unforgivable, but I think it's neat
        # This finds only YT videos, not channels etc.
        # It will return list of tuples as  [(Video Name, link), ...]
        links = [(x.text.strip(), f"https://youtube.com{x.a['href'].strip().split('&')[0]}")
                 for x in soup.find_all('div', attrs={'dir': 'ltr'})
                 # This bit ensure's we only capture video links
                 if x.a is not None and x.a['href'].strip().startswith('/watch?')]

        return links[:limit]

    @commands.group(name='youtube', aliases=['yt'], invoke_without_command=True)
    async def _youtube(self, ctx, *, query: str):
        """ Return a youtube URL for your query """
        async with self.session.get(self.uri,
                                    headers=self.headers,
                                    params={'search_query': query}) as r:
            html = await r.text()

        items = self.get_yt_items(html)

        if len(items) == 0:
            return await ctx.error(f'No YouTube videos found for `{query}`.')

        # Send the first video URL
        await ctx.send(items[0][1])

    @_youtube.command(aliases=['-s'])
    async def search(self, ctx, *, query: str):
        """ Search for a list of youtube videos for your query """
        async with self.session.get(self.uri,
                                    headers=self.headers,
                                    params={'search_query': query}) as r:
            html = await r.text()

        items = self.get_yt_items(html, limit=5)

        if len(items) == 0:
            return await ctx.error(f'No YouTube videos found for `{query}`.')

        em = discord.Embed(color=discord.Color.dark_red())
        em.set_author(name="YouTube Search",
                      icon_url="https://www.seeklogo.net/wp-content/uploads/2016/06/YouTube-icon.png")

        em.add_field(name='Results', value='\n'.join(f'{idx + 1}. [{x[0]}]({x[1]})' for idx, x in enumerate(items)))

        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(YouTube(bot))
