import asyncio

import discord
from yandex_music import Client, exceptions

from global_variables import tokens, data_servers, output_path


async def send_search_request(interaction: discord.Interaction, query):
    error_count = 0
    while error_count < 3:
        try:
            client_ym = Client(tokens[str(data_servers[interaction.guild.name]['user_discord_play'])]).init()

            search_result = client_ym.search(query)

            type_ = search_result.best.type
            best = search_result.best.result
            if type_ in ['track', 'podcast_episode']:
                track = client_ym.tracks(best.track_id)[0]
                data_servers[interaction.guild.name]['track_id_play_now'] = track.id
                data_servers[interaction.guild.name]['duration'] = track.duration_ms
                artists = track.artists
                if not artists:
                    artist_all = ""
                else:
                    artist_names = [artist.name for artist in artists]  # получаем список имен артистов
                    artist_all = ", ".join(artist_names)  # объединяем их через запятую
                play_now = ''
                if data_servers[interaction.guild.name]['radio_check']:
                    play_now += f"\nРадио: {data_servers[interaction.guild.name]['radio_check']['name']}"
                elif data_servers[interaction.guild.name]['stream_by_track_check']:
                    play_now += f'\nРадио: Моя волна по треку "{data_servers[interaction.guild.name]["stream_by_track_check"]["name"]}"'
                play_now += f"\nТрек: {track.title}\nИсполнители: {artist_all}"

                track.download(f'{output_path}\\{data_servers[interaction.guild.name]["user_discord_play"]}.mp3')

                try:
                    data_servers[interaction.guild.name]['lyrics'] = track.get_lyrics().fetch_lyrics()
                except exceptions.NotFoundError:
                    data_servers[interaction.guild.name]['lyrics'] = None

                if track.desired_visibility:
                    data_servers[interaction.guild.name]['track_url'] = None
                else:
                    base_url = 'https://music.yandex.ru/track/'
                    if ":" in track.track_id:
                        data_servers[interaction.guild.name]['track_url'] = base_url + str(track.track_id).split(":")[0]
                    else:
                        data_servers[interaction.guild.name]['track_url'] = base_url + str(track.track_id)

                if track.cover_uri:
                    data_servers[interaction.guild.name]['cover_url'] = f"https://{track.cover_uri.replace('%%', '200x200')}"
                else:
                    data_servers[interaction.guild.name]['cover_url'] = None

                return play_now
            else:
                data_servers[interaction.guild.name]['track_id_play_now'] = None
                await interaction.edit_original_response(content="Не удалось найти трек с таким названием")
                return False
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
