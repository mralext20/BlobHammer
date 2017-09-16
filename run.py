# -*- coding: utf-8 -*-
import asyncio
import datetime
import logging
import time
from typing import Union

import discord
from discord.ext import commands

from config import token


MOD_LOG = 289494042000228352
BLOB_GUILD = 272885620769161216
EXTRA_GUILDS = [
    356869031870988309,  # blob emoji 2
    356876866952364032,  # blob emoji 3
    356876897403011072,  # blob emoji 4
]

# emoji
BLOB_HAMMER = '<:blobhammer:357765371769651201>'
BOLB = '<:bolb:357767364118315008>'


logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='hammer.log', encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


class BlobHammerBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.extra_guilds = []
        self.add_command(self.sync)
        self.add_command(self.ping)
        # help is not very useful as there's only two commands, it would just disrupt chat
        self.remove_command('help')

    async def on_ready(self):
        self.extra_guilds = [self.get_guild(x) for x in EXTRA_GUILDS]

    async def on_member_ban(self, guild: discord.Guild, user: Union[discord.Member, discord.User]):
        if guild.id != BLOB_GUILD:
            return

        reason = await self.get_reason(guild, discord.AuditLogAction.ban, user)

        for guild in self.extra_guilds:
            await guild.ban(user, reason=reason)

        mod_log = self.get_channel(MOD_LOG)
        await mod_log.send(f'{BLOB_HAMMER} {user} (`{user.id}`) cross banned.')

    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        if guild.id != BLOB_GUILD:
            return

        reason = await self.get_reason(guild, discord.AuditLogAction.unban, user)

        for guild in self.extra_guilds:
            await guild.unban(user, reason=reason)

        mod_log = self.get_channel(MOD_LOG)
        await mod_log.send(f'{BOLB} {user} (`{user.id}`) cross unbanned.')

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def sync(self, ctx: commands.Context):
        """Sync bans."""
        async with ctx.typing():
            blob_guild = self.get_guild(BLOB_GUILD)
            blob_bans = set(x.user for x in await blob_guild.bans())

            for guild in self.extra_guilds:
                bans = set(x.user for x in await guild.bans())
                diff = blob_bans.difference(bans)

                for ban in diff:
                    if ban in bans:
                        await guild.unban(ban, reason='sync - user not banned on main guild')
                    else:
                        await guild.ban(ban, reason='sync - user banned on main guild')

        await ctx.send('Successfully synced bans.')

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ping(self, ctx: commands.Context):
        """Pong!"""
        before = time.perf_counter()
        msg = await ctx.send('Pon..')
        after = time.perf_counter()

        ws = self.latency * 1000
        rtt = (after - before) * 1000

        await msg.edit(content=f'Pong! rtt {rtt:.3f}ms, ws: {ws:.3f}ms')

    async def get_reason(self, guild: discord.Guild, action: discord.AuditLogAction, target) -> str:
        """Get the reason an action was performed on something."""
        # since the audit log is slow sometimes
        await asyncio.sleep(4)

        before_sleep = datetime.datetime.utcnow() - datetime.timedelta(seconds=15)
        async for entry in guild.audit_logs(limit=20, after=before_sleep, action=action):
            if entry.target != target:
                continue

            return entry.reason if entry.reason is not None else 'no reason specified'
        return 'no reason found'


bot = BlobHammerBot(command_prefix='!')
bot.run(token)