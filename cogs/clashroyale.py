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
        self.leagues = Leagues()
        self.player = "https://api.clashofclans.com/v1/players/"
        self.clans = "https://api.clashofclans.com/v1/clans/"
        self.reaction_emojis = ('⚔', '🛡')
        self.headers = {'Accept': 'application/json',
                        'Authorization': f"Bearer {bot.config['clash_key']}"}

    async def _clan_data(self, ctx, tag):
        async def _verify_tag(ans_tag):
            if not len(ans_tag) == 9 and not ans_tag.startswith('#'):
                await ctx.error("A clan tag starts with '#' and has a total length of 9!\nPlease try again.")
                return False
            else:
                return True

        if not await _verify_tag(tag):
            return None

        if not await self.bot.redis.execute('EXISTS', tag):
            async with self.session.get(f"{self.clans}{quote_plus(tag)}", headers=self.headers) as resp:
                if resp.status != 200:
                    await ctx.error("An error has occurred, please check your provided tag")
                    return None
                clan_data = await resp.json()
            await self.bot.redis.execute('SET', tag, str(json.dumps(clan_data)))
            await self.bot.redis.execute('EXPIRE', tag, 7200)
        else:
            print('redis exists')
            clan_data = json.loads(await self.bot.redis.execute('GET', tag))

        emb = discord.Embed(title=clan_data['name'], description=clan_data['tag'])

        emb.add_field(name="Required Trophies :trophy:", value=f"{clan_data['requiredTrophies']}", inline=True)

        emb.add_field(name="Location", value=clan_data['location']['name'])

        emb.add_field(name="Total Members", value=clan_data['members'], inline=True)
        emb.add_field(name="Type", value="Invite Only" if clan_data['type'] == "inviteOnly"
                      else clan_data['type'].capitalize())

        emb.add_field(name="Clan Level", value=clan_data['clanLevel'], inline=True)
        emb.add_field(name="Clan Points", value=clan_data['clanPoints'])
        emb.add_field(name="Clan Versus Points", value=clan_data['clanVersusPoints'], inline=True)
        emb.add_field(name="War Frequency", value=clan_data['warFrequency'].capitalize())
        emb.add_field(name="War Win Streak", value=clan_data['warWinStreak'], inline=True)
        emb.add_field(name="War Wins", value=clan_data['warWins'])
        emb.add_field(name="War Log", value="Public" if clan_data['isWarLogPublic'] else "Hidden", inline=True)
        emb.add_field(name="Description", value=clan_data['description'], inline=False)

        emb.set_thumbnail(url=clan_data['badgeUrls']['medium'])

        return emb

    @commands.group(invoke_without_command=True)
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
        if not await self.bot.redis.execute('EXISTS', tag):
            async with self.session.get(f"{self.player}{quote_plus(tag)}", headers=self.headers) as resp:
                if resp.status != 200:
                    return await ctx.error("An error has occurred, please check your provided tag")
                player_data = await resp.json()
            await self.bot.redis.execute('SET', tag, str(json.dumps(player_data)))
            await self.bot.redis.execute('EXPIRE', tag, 7200)
        else:
            print('redis exists')
            player_data = json.loads(await self.bot.redis.execute('GET', tag))

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

        em.add_field(name="Home Troops", value=columnize.columnize(home_trps_raw, displaywidth=50), inline=False)
        em.add_field(name="Builder Base Troops", value=columnize.columnize(bldr_trps_raw, displaywidth=50), inline=False)

        em.set_thumbnail(url=player_league['url'])

        if 'clan' in player_data.keys():
            em.set_footer(text=f"{player_data['clan']['tag']}  |  Clan Name: {player_data['clan']['name']}",
                          icon_url=player_data['clan']['badgeUrls']['small'])

        player_msg = await ctx.send(embed=em)

        if not 'clan' in player_data.keys():
            return

        def react_check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in self.reaction_emojis\
                   and player_msg.id == reaction.message.id

        await player_msg.add_reaction(self.reaction_emojis[1])

        while 1:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=react_check)
            except asyncio.TimeoutError:
                for emoji in self.reaction_emojis:
                    await player_msg.remove_reaction(emoji, self.bot.user)
                    await player_msg.remove_reaction(emoji, ctx.author)
                return

            if str(reaction.emoji) == self.reaction_emojis[1]:
                clan_embed = await self._clan_data(ctx, player_data['clan']['tag'])
                if clan_embed is None:
                    return
                await player_msg.edit(embed=clan_embed)
                await player_msg.remove_reaction(self.reaction_emojis[1], self.bot.user)
                await player_msg.remove_reaction(self.reaction_emojis[1], ctx.author)

                await player_msg.add_reaction(self.reaction_emojis[0])
            elif str(reaction.emoji) == self.reaction_emojis[0]:
                await player_msg.edit(embed=em)
                await player_msg.remove_reaction(self.reaction_emojis[0], self.bot.user)
                await player_msg.remove_reaction(self.reaction_emojis[0], ctx.author)

                await player_msg.add_reaction(self.reaction_emojis[1])

    @clash.command(name="clan")
    async def clan(self, ctx, *, tag: str=None):
        """ Get a clan's info by tag. """

        if tag is None:
            return await ctx.error("Please provide a clan tag.")

        clan_embed = await self._clan_data(ctx, tag)

        if clan_embed is None:
            return

        await ctx.send(embed=clan_embed)


def setup(bot):
    bot.add_cog(ClashOfClans(bot))
