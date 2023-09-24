import discord
from discord import SelectOption
from discord.ui import Select
from yandex_music import Client

from global_variables import settings_onyourwave, data_servers, tokens, ru_settings_onyourwave
from command_processing.play_yandex_music_radio import play_yandex_music_radio


class OnyourwaveSettingDiversity(Select):
    def __init__(self):
        super().__init__(placeholder='По характеру...', min_values=1, max_values=1, options=[
            SelectOption(label='Любимое', value='favorite', emoji='💖'),
            SelectOption(label='Незнакомое', value='discover', emoji='✨'),
            SelectOption(label='Популярное', value='popular', emoji='⚡'),
            SelectOption(label='По умолчанию', value='default', emoji='♦️')
        ])

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            settings_onyourwave[str(data_servers[interaction.guild.name]['user_discord_play'])]['diversity'] = self.values[0]

            client_ym = Client(tokens[str(data_servers[interaction.guild.name]['user_discord_play'])]).init()

            client_ym.rotor_station_settings2(
                station=data_servers[interaction.guild.name]['radio_check']['station'],
                mood_energy=settings_onyourwave[str(data_servers[interaction.guild.name]['user_discord_play'])]['mood_energy'],
                diversity=settings_onyourwave[str(data_servers[interaction.guild.name]['user_discord_play'])]['diversity'],
                language=settings_onyourwave[str(data_servers[interaction.guild.name]['user_discord_play'])]['language']
            )
            voice_client = interaction.guild.voice_client
            if voice_client.is_playing() or voice_client.is_paused():
                voice_client.stop()
                data_servers[interaction.guild.name]['task'].cancel()
            await interaction.edit_original_response(content='Изменение настроек радио. Подождите')
            await play_yandex_music_radio(
                interaction=interaction,
                station_id=data_servers[interaction.guild.name]["radio_check"]["station"],
                station_from=data_servers[interaction.guild.name]["radio_check"]["station_from"],
                first_track=True,
                new_task=True
            )
            embed = discord.Embed(
                title=f'Настройки радио: {data_servers[interaction.guild.name]["radio_check"]["name"]}',
                color=0xf1ca0d,
                description=f'Характер: {ru_settings_onyourwave[settings_onyourwave[str(data_servers[interaction.guild.name]["user_discord_play"])]["diversity"]]}\n'
                            f'Настроение: {ru_settings_onyourwave[settings_onyourwave[str(data_servers[interaction.guild.name]["user_discord_play"])]["mood_energy"]]}\n'
                            f'Язык: {ru_settings_onyourwave[settings_onyourwave[str(data_servers[interaction.guild.name]["user_discord_play"])]["language"]]}'
            )
            await interaction.edit_original_response(content='', embed=embed)
        except Exception as e:
            await interaction.edit_original_response(
                content=f'Произошла ошибка {e}.\n'
                        f'Попробуйте ещё раз.'
            )
