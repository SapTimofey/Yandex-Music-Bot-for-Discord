import asyncio

import discord
from yandex_music import Client, exceptions

from global_variables import tokens, data_servers, output_path


async def play_yandex_music_playlist(interaction: discord.Interaction, track=None, playlist_id=None):
    error_count = 0
    track_id = None
    track_index = None

    while error_count < 3:
        try:
            client_ym = Client(tokens[str(data_servers[interaction.guild.name]['user_discord_play'])]).init()

            if playlist_id:
                if not data_servers[interaction.guild.name]['album']:
                    if playlist_id == "3":
                        all_tracks = client_ym.tracks(client_ym.users_likes_tracks().tracksIds)
                        playlist_title = "Мне нравится"
                    else:
                        try:
                            all_tracks = [track.__getitem__('track') for track in client_ym.users_playlists(playlist_id).tracks]
                            playlist_title = client_ym.users_playlists(playlist_id).title
                        except exceptions.NotFoundError:
                            return False
                else:
                    all_tracks = []
                    playlist_album = client_ym.albums_with_tracks(playlist_id).volumes
                    if len(playlist_album) > 1:
                        for item in playlist_album:
                            all_tracks += item
                    else:
                        all_tracks = playlist_album[0]
                    playlist_title = client_ym.albums_with_tracks(playlist_id).title

                data_servers[interaction.guild.name]['track_count'] = len(all_tracks)
                j = 0
                list_for_page = []
                index_in_array = 0

                for index_in_playlist in range(len(all_tracks)):
                    track = all_tracks[index_in_playlist]
                    if track.available:
                        if not track_id:
                            track_id = track.id
                            track_index = index_in_playlist + 1
                        data_servers[interaction.guild.name]['playlist'].append([track.id, index_in_playlist+1, playlist_title])
                        data_servers[interaction.guild.name]['playlist_reserve'].append([track.id, index_in_playlist+1, playlist_title])
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
                        # if index_in_playlist % 20 == 0:
                        #     try:
                        #         if not data_servers[interaction.guild.name]['album']:
                        #             await interaction.edit_original_response(
                        #                 content=f'Загрузка плейлиста "{playlist_title}". ({index_in_playlist + 1}/{len(all_tracks)})'
                        #             )
                        #         else:
                        #             await interaction.edit_original_response(
                        #                 content=f'Загрузка альбома "{playlist_title}". ({index_in_playlist + 1}/{len(all_tracks)})'
                        #             )
                        #     except (discord.HTTPException, discord.NotFound, discord.Forbidden):
                        #         pass
                        index_in_array += 1
                if j > 0:
                    data_servers[interaction.guild.name]['track_list'].append(list_for_page)
            else:
                track_id = track[0]
                track_index = track[1]
                playlist_title = track[2]

            track = client_ym.tracks(track_id)[0]

            data_servers[interaction.guild.name]['track_id_play_now'] = track_id
            data_servers[interaction.guild.name]['duration'] = track.duration_ms
            artists = track.artists
            if not artists:
                artist_all = ""
            else:
                artist_names = [artist.name for artist in artists]
                artist_all = ", ".join(artist_names)
            if not data_servers[interaction.guild.name]['album']:
                play_now = f"\nПлейлист: {playlist_title}"
            else:
                play_now = f"\nАльбом: {playlist_title}"
            play_now += f"\nТрек: {track.title}" + \
                        f"\nИсполнители: {artist_all}" + \
                        f"\nНомер трека: {track_index} / {data_servers[interaction.guild.name]['track_count']}"

            track.download(f'{output_path}\\{data_servers[interaction.guild.name]["user_discord_play"]}.mp3')

            try:
                data_servers[interaction.guild.name]['lyrics'] = track.get_lyrics().fetch_lyrics()
            except (exceptions.NotFoundError, ValueError):
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
