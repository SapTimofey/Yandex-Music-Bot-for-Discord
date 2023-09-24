import asyncio

import discord
from yandex_music import Client

from global_variables import tokens, data_servers


async def play_yandex_music_radio(
        interaction: discord.Interaction,
        station_id: str,
        station_from: str,
        first_track: bool = False,
        new_task: bool = False
):
    from .Radio import Radio
    from .play import play

    error_count = 0
    while error_count < 3:
        try:
            if first_track:
                client_ym = Client(tokens[str(data_servers[interaction.guild.name]['user_discord_play'])]).init()
                data_servers[interaction.guild.name]['radio_client'] = Radio(client_ym)
                track = data_servers[interaction.guild.name]['radio_client'].start_radio(station_id, station_from)
            else:
                track = data_servers[interaction.guild.name]['radio_client'].play_next()

            data_servers[interaction.guild.name]['track_id_play_now'] = track.id
            data_servers[interaction.guild.name]['duration'] = track.duration_ms
            base_url = 'https://music.yandex.ru/track/'
            if ":" in track.track_id:
                data_servers[interaction.guild.name]['track_url'] = base_url + str(track.track_id).split(":")[0]
            else:
                data_servers[interaction.guild.name]['track_url'] = base_url + str(track.track_id)

            if new_task:
                data_servers[interaction.guild.name]['task'] = \
                    asyncio.create_task(play(interaction, data_servers[interaction.guild.name]['track_url']))
                break
            else:
                return data_servers[interaction.guild.name]['track_url']
        except Exception as e:
            if error_count < 2:
                await interaction.channel.send(f'Произошла ошибка: {e}. Подождите')
                await asyncio.sleep(1)
                error_count += 1
            else:
                try:
                    await interaction.delete_original_response()
                except:
                    pass
                await interaction.channel.send(f"Не удалось устранить ошибку {e}")
                return False
