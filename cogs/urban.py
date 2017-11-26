import discord
from discord.ext import commands


class UrbanDictionary:
    def __init__(self, bot):
        self.bot = bot
        self.session = bot.session
        self.uri = 'http://api.urbandictionary.com/v0/define'
        self.icon_uri = 'http://www.packal.org/sites/default/files/public/styles/icon_large/public/workflow-files' \
                        '/florianurban/icon/icon.png '
        self.color = bot.user_color

    async def get_definitions(self, term: str, limit: int = 1) -> dict:
        """ Helper func to get definitions """
        params = {'term': term}
        async with self.session.get(self.uri, params=params) as r:
            resp = await r.json()

        return resp['list'][:limit]

    @commands.group(invoke_without_command=True, aliases=['ud', 'urban'])
    async def urbandictionary(self, ctx, *, query: str):
        """ Search for a word from UrbanDictionary """
        word = await self.get_definitions(query)

        if not word:
            return await ctx.error(f"Sorry, couldn't find a definition for `{query}`.")

        # Create embed
        em = discord.Embed(description=word['definition'], color=self.color)
        em.set_author(name=word['word'], icon_url=self.icon_uri)
        em.add_field(name='Example(s)', value=word['example'])

        await ctx.send(embed=em)

    @urbandictionary.command(aliases=['-s'])
    async def search(self, ctx, *, query: str):
        """ Search for a few definitions from UrbanDictionary """
        words = await self.get_definitions(query, limit=3)

        if not words:
            return await ctx.error(f"Sorry, couldn't find anything for `{query}`.")

        # Create embed
        em = discord.Embed(color=self.color)
        em.set_author(name='Search results', icon_url=self.icon_uri)
        for item in words:
            em.add_field(name=item['word'], value=f"{item['definition'][:50]}...")

        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(UrbanDictionary(bot))
