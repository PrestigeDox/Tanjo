import json
from datetime import datetime
from pathlib import Path
import aiohttp
import discord
from discord.ext import commands
from utils.custom_context import TanjoContext


class Tanjo(commands.Bot):
    def __init__(self, *args, **kwargs):
        self.description = 'To be continued'

        # Configs & token
        with open('data/config.json') as f:
            self.config = json.load(f)


        # TODO:
        # - Dynamic prefixes (per guild)
        # - Migrate help command from Watashi
        super().__init__(command_prefix=commands.when_mentioned_or(None), description=self.description, pm_help=None, *args, **kwargs)

        # Startup extensions (none yet)
        self.startup_ext = [x.stem for x in Path('cogs').glob('*.py')]

        # aiohttp session
        self.session = aiohttp.ClientSession(loop=self.loop)

        # Make room for the help command
        self.remove_command('help')

        # Embed color
        # Keeping with user_color convention to make migration from Watashi easier
        self.user_color = discord.Color.dark_orange()

    def run(self):
        super().run(self.config['token'])

    # Utilise custom context for error messaging etc.
    async def on_message(self, message):
        ctx = await self.get_context(message, cls=TanjoContext)
        await self.invoke(ctx)

    async def on_ready(self):
        if not hasattr(self, 'start_time'):
            self.start_time = datetime.now()

        for ext in self.startup_ext:
            try:
                self.load_extension(f'cogs.{ext}')
            except Exception as e:
                print(f'Failed to load extension: {ext}\n{e}')
            else:
                print(f'Loaded extension: {ext}')

        print(f'Client logged in at {self.start_time}.\n'
              f'{self.user.name}\n'
              f'{self.user.id}\n'
              '--------------------------')
