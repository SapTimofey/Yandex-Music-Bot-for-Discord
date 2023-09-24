import asyncio
import datetime

import discord

from .disconnect import disconnect
from global_variables import data_servers, client


async def check_inactivity(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    while True:
        try:
            if (datetime.datetime.now() - data_servers[interaction.guild.name]['last_activity_time'] >
                datetime.timedelta(minutes=5) and not voice_client.is_playing()) or \
                    (voice_client and not any(member != client.user for member in voice_client.channel.members)):
                await disconnect(interaction)
            await asyncio.sleep(1)
        except asyncio.CancelledError:
            break
