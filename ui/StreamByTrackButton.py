import discord
from discord import ButtonStyle
from discord.ui import Button
from yandex_music import Client

from global_variables import tokens, data_servers
from command_processing.play_yandex_music_radio import play_yandex_music_radio


class StreamByTrackButton(Button):
    def __init__(self, interaction: discord.Interaction):
        if not data_servers[interaction.guild.name]['track_url'] or \
                'youtube.com' in data_servers[interaction.guild.name]['track_url']:
            disabled = True
        else:
            disabled = False
        super().__init__(
            style=ButtonStyle.primary,
            label="Моя волна по треку",
            emoji="💫",
            row=3,
            disabled=disabled
        )

    async def callback(self, interaction: discord.Interaction):
        client_ym = Client(tokens[str(data_servers[interaction.guild.name]['user_discord_play'])]).init()
        track = client_ym.tracks(data_servers[interaction.guild.name]['track_id_play_now'])[0]

        data_servers[interaction.guild.name]['radio_check'] = False
        data_servers[interaction.guild.name]['album'] = False
        data_servers[interaction.guild.name]['stream_by_track_check'] = {
            "name": 'Моя волна по треку ' + track.title,
            "station": 'track:' + data_servers[interaction.guild.name]['track_id_play_now'],
            "station_from": 'track'
        }
        data_servers[interaction.guild.name]['playlist'] = []
        data_servers[interaction.guild.name]['track_list'] = []
        data_servers[interaction.guild.name]['index_play_now'] = 0

        voice_client = interaction.guild.voice_client
        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()
            data_servers[interaction.guild.name]['task'].cancel()
        await play_yandex_music_radio(
            interaction=interaction,
            station_id=data_servers[interaction.guild.name]['stream_by_track_check']['station'],
            station_from=data_servers[interaction.guild.name]['stream_by_track_check']['station_from'],
            first_track=True,
            new_task=True
        )
