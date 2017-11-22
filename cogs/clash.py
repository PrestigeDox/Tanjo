import asyncio
import columnize
import discord
import json

from discord.ext import commands
from urllib.parse import quote_plus
from utils.leagues import Leagues
from utils import db as tanjo


class ClashOfClans:
    def __init__(self, bot):
        self.bot = bot
        self.session = bot.session
        self.key = bot.config['clash_key']
        self.leagues = Leagues()
        self.player = "https://api.clashofclans.com/v1/players/"

    @commands.command()
    async def clash(self, ctx, *, tag: str=None):
        """ Fetch Clash of Clans player details """
        async def _verify_tag(ans_tag):
            if not len(ans_tag) == 10 and not ans_tag.startswith('#'):
                await ctx.error("A player tag starts with '#' and has a total length of 10!\nPlease try again.")
                return False
            else:
                return True

        if tag is None:
            # Determine the player tag of this person
            async with self.bot.conn_pool.acquire() as conn:
                user = await tanjo.fetch_user(conn, ctx.author.id)
                if user['clash_tag'] is None:
                    def check(m):
                        return m.author == ctx.author and m.channel == ctx.channel
                    await ctx.send("Please provide your Clash of Clans player tag or type `exit` to leave\n"
                                   "Hint: This can be found on your user profile")
                    while 1:
                        response = await self.bot.wait_for('message', check=check)
                        if response.content == 'exit':
                            return
                        elif not await _verify_tag(response.content):
                            continue
                        else:
                            tag = response.content
                            await conn.execute('UPDATE users SET clash_tag=$1 WHERE id=$2', tag, ctx.author.id)
                            break
                else:
                    tag = user['clash_tag']
        else:
            if not await _verify_tag(tag):
                return

        headers = {'Accept': 'application/json',
                   'Authorization': f'Bearer {self.key}'}

        async with self.session.get(f"{self.player}{quote_plus(tag)}", headers=headers) as resp:
            if resp.status != 200:
                return await ctx.error("An error has occurred, please check your provided tag")
            player_data = await resp.json()

        player_league = self.leagues.get_league(player_data['trophies'])
        player_bestleague = self.leagues.get_league(player_data['bestTrophies'])

        heroes = '\n'.join([f"*{x['name']}*: Lv. {x['level']}" for x in player_data['heroes']])

        home_trps_raw = [f"*{x['name']}*: Lv. {x['level']}" for x in player_data['troops'] if x['village'] == 'home']

        bldr_trps_raw = [f"*{x['name']}*: Lv. {x['level']}" for x in player_data['troops']
                         if x['village'] == 'builderBase']

        donations = f'Donated: {player_data["donations"]}\nReceived: {player_data["donationsReceived"]}'
        defense_attack = f'Defense Wins: {player_data["defenseWins"]}\nAttack Wins: {player_data["attackWins"]}'

        em = discord.Embed(title=player_data['name'], description=player_data['tag'])

        em.add_field(name="Trophies :trophy:", value=f"{player_data['trophies']}", inline=True)
        em.add_field(name="Current League", value=player_league["name"], inline=True)
        em.add_field(name="Townhall Level", value=player_data["townHallLevel"], inline=True)
        em.add_field(name="Experience Level", value=player_data["expLevel"])
        em.add_field(name="Best Trophies :trophy:",
                     value=f'{player_data["bestTrophies"]}: {player_bestleague["name"]}', inline=True)

        em.add_field(name="Best Versus Trophies :trophy:",
                     value=f'{player_data["bestVersusTrophies"]}', inline=True)

        em.add_field(name="Recent Donations", value=donations)

        em.add_field(name="Current Versus Trophies :trophy:",
                     value=f'{player_data["versusTrophies"]}', inline=True)

        em.add_field(name="Heroes", value=heroes, inline=True)
        em.add_field(name="Recent Attacks", value=defense_attack, inline=True)

        em.add_field(name="Home Troops", value=columnize.columnize(home_trps_raw, displaywidth=20), inline=True)
        em.add_field(name="Builder Base Troops", value=columnize.columnize(bldr_trps_raw, displaywidth=20), inline=True)

        em.set_thumbnail(url=player_league['url'])

        em.set_footer(text=f"{player_data['clan']['tag']}  |  Clan Name: {player_data['clan']['name']}",
                      icon_url=player_data['clan']['badgeUrls']['small'])

        await ctx.send(embed=em)

    # @google.command(name="images", aliases=['img', 'image'])
    # async def images(self, ctx, *, query: str=None):
    #     """ Search Google for Images """
    #     # Handle empty query
    #     if query is None:
    #         return await ctx.error('Please provide a query!')
    #
    #     # Using these specific headers and "lnms" as source, will provide divs with "rg_meta" classes,
    #     # The modern image search page being JS rendered, data in these divs are jsons with raw image URLs
    #     # Old image search pages, only have thumbnails and a direct link to websites
    #     params = {'q': quote_plus(query), 'source': 'lmns', 'tbm': 'isch'}
    #     async with self.session.get(self.url, params=params, headers=self.image_headers) as r:
    #         html = await r.text()
    #
    #     # Healthy
    #     soup = BeautifulSoup(html, 'lxml')
    #
    #     # Go over 4 items, json.loads the item text, and grab "ou" probably stands for "original url"
    #     images = []
    #     for item in soup.select('div.rg_meta')[:4]:
    #         images.append({'url': json.loads(item.text)["ou"], 'title': json.loads(item.text)["pt"],
    #                        'page_link': json.loads(item.text)["ru"]})
    #
    #     # Setup a base embed
    #     em = discord.Embed(title=images[0]['title'], url=images[0]['page_link'])
    #     em.set_author(name=f"Image results for {query}")
    #     em.set_image(url=images[0]['url'])
    #
    #     # Save the sent image as image_result for further manipulation
    #     image_result = await ctx.send(embed=em)
    #
    #     # reaction_emojis has 1,2,3,4 in a sequence, so 1,2,3,4 reactions get added
    #     for emoji in self.reaction_emojis:
    #         await image_result.add_reaction(emoji)
    #
    #     while 1:
    #         # Make sure the reaction is where we wanted it to be
    #         def check(reaction, user):
    #             return user == ctx.author and str(reaction.emoji) in self.reaction_emojis and reaction.message.id == image_result.id
    #
    #         # If someone doesn't react for 30 secs, just die :<
    #         try:
    #             reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
    #         except asyncio.TimeoutError:
    #             await image_result.delete()
    #             break
    #
    #         # Remove the user's reactions for a 'button' like experience
    #         for emoji in self.reaction_emojis:
    #             await image_result.remove_reaction(emoji, ctx.author)
    #
    #         # Now, if they reacted with say '2', the index of '2' in reaction_emojis will be 1
    #         # This corresponds to the item in our images list, so we grab the index and without any hassle
    #         # update the embed with a new image and link
    #         selected_item = self.reaction_emojis.index(str(reaction.emoji))
    #         em.set_image(url=images[selected_item]['url'])
    #         em.url = images[selected_item]['page_link']
    #         em.title = images[selected_item]['title']
    #         await image_result.edit(embed=em)


def setup(bot):
    bot.add_cog(ClashOfClans(bot))
