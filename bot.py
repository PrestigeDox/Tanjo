import aiohttp
import json
import discord
from custom_context import TanjoContext
from datetime import datetime
from pathlib import Path
from discord.ext import commands


class Tanjo(commands.Bot):
    def __init__(self, *args, **kwargs):
        self.description = 'To be continued'

        # aiohttp session
        self.session = aiohttp.ClientSession(loop=self.loop)

        # Configs & token
        with open('data/config.json') as f:
            self.config = json.load(f)

        # Startup extensions (none yet)
        startup_ext = [x.stem for x in Path('cogs').glob('*.py')]

        # TODO:
        # - Dynamic prefixes (per guild)
        # - Migrate help command from Watashi
        super().__init__(command_prefix='t.', description=self.description, pm_help=None, *args, **kwargs)

    def run(self):
        super().run(self.config['token'])

    # Utilise custom context for error messaging
    async def on_message(self, message):
        ctx = await self.get_context(message, cls=TanjoContext)
        await self.invoke(ctx)

    async def on_ready(self):
        if not hasattr(self, 'start_time'):
            self.start_time = datetime.now()

        for ext in self.startup_ext:
            try:
                self.load_extension(f'cogs.{ext}')
            except:
                print(f'Failed to load extension: {ext}')
            else:
                print(f'Loaded extension: {ext}')

        print(f'Client logged in at {self.start_time}.'
              f'{self.user.name}'
              f'{self.user.id}'
              '--------------------------')
