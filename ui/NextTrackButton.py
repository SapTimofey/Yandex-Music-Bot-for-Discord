import discord
from discord import ButtonStyle
from discord.ui import Button

from global_variables import data_servers


class NextTrackButton(Button):
    def __init__(self, interaction: discord.Interaction):
        super().__init__(
            style=ButtonStyle.primary,
            label="К следующему",
            emoji="⏭️",
            row=1,
            disabled=(not data_servers[interaction.guild.name]['random']) and (data_servers[interaction.guild.name]['index_play_now'] + 1 >= len(
                data_servers[interaction.guild.name]['playlist']) and not data_servers[
                interaction.guild.name]['radio_check'] and not data_servers[
                interaction.guild.name]['stream_by_track_check'])
        )

    async def callback(self, interaction: discord.Interaction):
        data_servers[interaction.guild.name]['repeat_flag'] = False
        voice_client = interaction.guild.voice_client
        voice_client.stop()
