import asyncio

import discord
from yandex_music import Client, exceptions

from .send_search_request import send_search_request
from global_variables import tokens, data_servers, output_path


async def play_yandex_music_playlist(interaction: discord.Interaction, url_or_trackname_or_filepath):
    error_count = 0
    playlist_ym = url_or_trackname_or_filepath.split(',')
    playlist_id = playlist_ym[0]
    index_track = None

    while error_count < 3:
        try:
            client_ym = Client(tokens[str(data_servers[interaction.guild.name]['user_discord_play'])]).init()

            if not data_servers[interaction.guild.name]['playlist']:
                if not data_servers[interaction.guild.name]['album']:
                    if playlist_id == "3":
                        playlist_new = client_ym.users_likes_tracks().tracks
                        data_servers[interaction.guild.name]['playlist_title'] = title = "Мне нравится"
                    else:
                        try:
                            playlist_new = client_ym.users_playlists(playlist_id).tracks
                            data_servers[interaction.guild.name]['playlist_title'] = title = client_ym.users_playlists(
                                playlist_id).title
                        except exceptions.NotFoundError:
                            play_now = await send_search_request(interaction, url_or_trackname_or_filepath)
                            if not play_now:
                                return False

                            return play_now
                else:
                    playlist_new = []
                    playlist_album = client_ym.albums_with_tracks(playlist_id).volumes
                    if len(playlist_album) > 1:
                        for item in playlist_album:
                            playlist_new += item
                    else:
                        playlist_new = playlist_album[0]
                    data_servers[interaction.guild.name]['playlist_title'] = title = client_ym.albums_with_tracks(
                        playlist_id).title

                j = 0
                list_for_page = []
                index_in_array = 0

                for index_in_playlist in range(len(playlist_new)):
                    track_short = playlist_new[index_in_playlist]
                    track = client_ym.tracks(track_short.track_id)[0]
                    if track.available:
                        if index_track is None:
                            index_track = index_in_playlist + 1
                        data_servers[interaction.guild.name]['playlist'].append(f"{playlist_id},{index_in_playlist + 1}")
                        data_servers[interaction.guild.name]['playlist_reserve'].append(f"{playlist_id},{index_in_playlist + 1}")
                        artists = track.artists
                        if not artists:
                            artist_all = ""
                        else:
                            artist_names = [artist.name for artist in artists]
                            artist_all = ", ".join(artist_names)
                        if j < 24:
                            if len(track.title) > 90:
                                track_title = track.title[:90]
                                list_for_page.append([index_in_array, index_in_playlist + 1, track_title, artist_all])
                            else:
                                list_for_page.append([index_in_array, index_in_playlist + 1, track.title, artist_all])
                            j += 1
                        else:
                            if len(track.title) > 90:
                                track_title = track.title[:90]
                                list_for_page.append([index_in_array, index_in_playlist + 1, track_title, artist_all])
                            else:
                                list_for_page.append([index_in_array, index_in_playlist + 1, track.title, artist_all])
                            data_servers[interaction.guild.name]['track_list'].append(list_for_page)
                            list_for_page = []
                            j = 0
                        try:
                            if not data_servers[interaction.guild.name]['album']:
                                await interaction.edit_original_response(
                                    content=f'Загрузка плейлиста "{title}". ({index_in_playlist + 1}/{len(playlist_new)})'
                                )
                            else:
                                await interaction.edit_original_response(
                                    content=f'Загрузка альбома "{title}". ({index_in_playlist + 1}/{len(playlist_new)})'
                                )
                        except (discord.HTTPException, discord.NotFound, discord.Forbidden):
                            pass
                        index_in_array += 1
                if j > 0:
                    data_servers[interaction.guild.name]['track_list'].append(list_for_page)
            else:
                if data_servers[interaction.guild.name]['album']:
                    playlist_new = []
                    playlist_album = client_ym.albums_with_tracks(playlist_id).volumes
                    if len(playlist_album) > 1:
                        for item in playlist_album:
                            playlist_new += item
                    else:
                        playlist_new = playlist_album[0]
                elif playlist_id == "3":
                    playlist_new = client_ym.users_likes_tracks().tracks
                else:
                    playlist_new = client_ym.users_playlists(playlist_id).tracks
            try:
                track_short = playlist_new[int(playlist_ym[1]) - 1]
                index_track = int(playlist_ym[1])
            except IndexError:
                if not index_track:
                    index_track = int(data_servers[interaction.guild.name]['playlist'][0].split(',')[1])
                track_short = playlist_new[index_track - 1]

            track = client_ym.tracks(track_short.track_id)[0]

            data_servers[interaction.guild.name]['track_id_play_now'] = track.id
            data_servers[interaction.guild.name]['duration'] = track.duration_ms
            artists = track.artists
            if not artists:
                artist_all = ""
            else:
                artist_names = [artist.name for artist in artists]
                artist_all = ", ".join(artist_names)
            if not data_servers[interaction.guild.name]['album']:
                play_now = f"\nПлейлист: {data_servers[interaction.guild.name]['playlist_title']}"
            else:
                play_now = f"\nАльбом: {data_servers[interaction.guild.name]['playlist_title']}"
            play_now += f"\nТрек: {track.title}" + \
                        f"\nИсполнители: {artist_all}" + \
                        f"\nНомер трека: {index_track} / {len(playlist_new)}"

            track.download(f'{output_path}\\{data_servers[interaction.guild.name]["user_discord_play"]}.mp3')

            try:
                data_servers[interaction.guild.name]['lyrics'] = track.get_lyrics().fetch_lyrics()
            except exceptions.NotFoundError:
                data_servers[interaction.guild.name]['lyrics'] = None
            except ValueError:
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
                data_servers[interaction.guild.name]['cover_url'] = \
                    f"https://{track.cover_uri.replace('%%', '200x200')}"
            else:
                data_servers[interaction.guild.name]['cover_url'] = None

            return play_now
        except Exception as e:
            if error_count < 2:
                await interaction.channel.send(f'Произошла ошибка: {e}. Подождите')
                await asyncio.sleep(1)
                error_count += 1
            else:
                try:
                    await interaction.delete_original_response()
                except (discord.HTTPException, discord.NotFound, discord.Forbidden):
                    pass
                await interaction.channel.send(f"Не удалось устранить ошибку {e}")
                return False
