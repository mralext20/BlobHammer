# -*- coding: utf-8 -*-
import asyncio
import datetime
from typing import Union

import discord
from discord.ext import commands

import config


class Bans:
    """Cog to sync bans across multiple guilds."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def on_ready(self):
        self.extra_guilds = [self.bot.get_guild(x) for x in config.EXTRA_GUILDS]

    async def on_member_ban(self, guild: discord.Guild, user: Union[discord.Member, discord.User]):
        if guild.id != config.BLOB_GUILD:
            return

        reason = await self.get_reason(guild, discord.AuditLogAction.ban, user)

        for guild in self.extra_guilds:
            await guild.ban(user, reason=reason)

        mod_log = self.bot.get_channel(config.MOD_LOG)
        await mod_log.send(f'{config.BLOB_HAMMER} {user} (`{user.id}`) cross banned.')

    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        if guild.id != config.BLOB_GUILD:
            return

        reason = await self.get_reason(guild, discord.AuditLogAction.unban, user)

        for guild in self.extra_guilds:
            await guild.unban(user, reason=reason)

        mod_log = self.bot.get_channel(config.MOD_LOG)
        await mod_log.send(f'{config.BOLB} {user} (`{user.id}`) cross unbanned.')

    async def sync(self):
        """Sync all bans from the main guild."""
        blob_guild = self.bot.get_guild(config.BLOB_GUILD)
        blob_bans = set(x.user for x in await blob_guild.bans())

        for guild in self.extra_guilds:
            bans = set(x.user for x in await guild.bans())
            diff = blob_bans.symmetric_difference(bans)

            for ban in diff:
                if ban in bans:
                    await guild.unban(ban, reason='sync - user not banned on main guild')
                else:
                    await guild.ban(ban, reason='sync - user banned on main guild')

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


def setup(bot: commands.Bot):
    bot.add_cog(Bans(bot))
