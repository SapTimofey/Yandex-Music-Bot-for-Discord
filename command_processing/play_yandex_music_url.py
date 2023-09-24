import asyncio

import discord
from yandex_music import Client, exceptions

from global_variables import data_servers, tokens, output_path


async def play_yandex_music_url(interaction: discord.Interaction, url_or_trackname_or_filepath):
    if 'track' in url_or_trackname_or_filepath:
        track_id = url_or_trackname_or_filepath.rsplit('/', maxsplit=1)[1]
        if '?' in track_id:
            track_id = track_id.split('?')[0]
    else:
        data_servers[interaction.guild.name]['task'].cancel()
        data_servers[interaction.guild.name]['album'] = True
        album_id = url_or_trackname_or_filepath.rsplit('/', maxsplit=1)[1]
        data_servers[interaction.guild.name]['task'] = \
            asyncio.create_task(play(
                interaction=interaction,
                url_or_trackname_or_filepath=album_id
            ))
        return

    error_count = 0
    while error_count < 3:
        try:
            client_ym = Client(tokens[str(data_servers[interaction.guild.name]['user_discord_play'])]).init()

            track = client_ym.tracks(track_id)[0]

            track.download(f'{output_path}\\{data_servers[interaction.guild.name]["user_discord_play"]}.mp3')
            data_servers[interaction.guild.name]['track_id_play_now'] = track.id
            data_servers[interaction.guild.name]['duration'] = track.duration_ms

            try:
                data_servers[interaction.guild.name]['lyrics'] = track.get_lyrics().fetch_lyrics()
            except exceptions.NotFoundError:
                data_servers[interaction.guild.name]['lyrics'] = None

            base_url = 'https://music.yandex.ru/track/'
            data_servers[interaction.guild.name]['track_url'] = base_url + str(track_id)

            if track.cover_uri:
                data_servers[interaction.guild.name]['cover_url'] = \
                    f"https://{track.cover_uri.replace('%%', '200x200')}"
            else:
                data_servers[interaction.guild.name]['cover_url'] = None

            artists = track.artists
            if not artists:
                artist_all = ""
            else:
                artist_names = [artist.name for artist in artists]  # получаем список имен артистов
                artist_all = ", ".join(artist_names)  # объединяем их через запятую
            play_now = ""
            if data_servers[interaction.guild.name]['radio_check']:
                play_now += f"\nРадио: {data_servers[interaction.guild.name]['radio_check']['name']}"
            elif data_servers[interaction.guild.name]['stream_by_track_check']:
                play_now += f'\nРадио: Моя волна по треку "{data_servers[interaction.guild.name]["stream_by_track_check"]["name"]}"'
            play_now += f"\nТрек: {track.title}" + \
                        f"\nИсполнители: {artist_all}"

            return play_now
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
