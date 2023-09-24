import discord
import copy

from .remove_last_playing_message import remove_last_playing_message
from global_variables import data_server, data_servers


async def disconnect(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    try:
        voice_client.stop()
        data_servers[interaction.guild.name]['task'].cancel()
        await remove_last_playing_message(interaction)

        await voice_client.disconnect()
        data_servers[interaction.guild.name]['task_check_inactivity'].cancel()
        data_servers[interaction.guild.name] = copy.deepcopy(data_server)
    except Exception:
        pass