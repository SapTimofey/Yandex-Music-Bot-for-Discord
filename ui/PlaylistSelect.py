import asyncio

import discord
from discord import SelectOption
from discord.ui import Select
from yandex_music import Client

from .AlbumListSelect import AlbumListSelect
from .MoodAndGenreSelect import MoodAndGenreSelect
from .NextPageButton import NextPageButton
from .PrevPageButton import PrevPageButton

from global_variables import tokens, data_servers


class PlaylistSelect(Select):
    def __init__(self, interaction: discord.Interaction):
        options = []
        client_ym = Client(tokens[str(data_servers[interaction.guild.name]['user_discord_play'])]).init()

        options.append(SelectOption(
            label="Продолжить слушать",
            value="1",
            description="Запустить трек, на котором вы остановились",
            emoji='🪄'
        ))
        options.append(SelectOption(
            label="Радио по жанру",
            value="4",
            description="Радио",
            emoji='📻'
        ))
        options.append(SelectOption(
            label="Моя волна",
            value="2",
            description="Радио",
            emoji='✨'
        ))
        checking_for_albums = False
        for item in client_ym.users_likes_albums():
            if item.album.type not in ['podcast', 'audiobook']:
                checking_for_albums = True
                break
        if checking_for_albums:
            options.append(SelectOption(
                label="Альбомы",
                value="5",
                description="Ваши любимые альбомы",
                emoji='💿'
            ))
        options.append(SelectOption(
            label="Мне нравится",
            value="3",
            description=f"Количество треков: {len(client_ym.users_likes_tracks())}",
            emoji='❤️'
        ))

        playlists_ym = client_ym.users_playlists_list()
        for playlist_ym in playlists_ym:
            playlist_ym_id = playlist_ym.playlist_id.split(':')[1]
            options.append(SelectOption(
                label=str(playlist_ym.title),
                value=str(playlist_ym_id),
                description=f"Количество треков: {client_ym.users_playlists(int(playlist_ym_id)).track_count}",
                emoji='🎶'
            ))

        super().__init__(placeholder='Что послушаем?...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        from command_processing.play import play
        from command_processing.play_yandex_music_radio import play_yandex_music_radio

        await interaction.response.defer()
        client_ym = Client(tokens[str(data_servers[interaction.guild.name]['user_discord_play'])]).init()
        error_count = 0
        while error_count < 3:
            try:
                if self.values[0] == "1":
                    await interaction.edit_original_response(
                        content='Загрузка трека, на котором Вы остановились. Подождите',
                        view=None
                    )
                    context = client_ym.queues_list()[0].context
                    type_of_playlist = context.type
                    if type_of_playlist == 'playlist':
                        data_servers[interaction.guild.name]['task'] = asyncio.create_task(play(
                            interaction=interaction,
                            url_or_trackname_or_filepath=f"{context.id.split(':')[1]},{int(client_ym.queue(client_ym.queues_list()[0].id).current_index) + 1}"
                        ))
                        data_servers[interaction.guild.name]['index_play_now'] = \
                            client_ym.queue(client_ym.queues_list()[0].id).current_index
                    elif type_of_playlist == 'my_music':
                        find = False
                        playlist_id = 0
                        for playlist in client_ym.users_playlists_list():
                            playlist_id = playlist.playlist_id.split(':')[1]
                            if str(client_ym.users_playlists(playlist_id).tracks[0].id) == str(client_ym.queue(client_ym.queues_list()[0].id).tracks[0].track_id):
                                find = True
                                break
                        if not find:
                            if str(client_ym.users_likes_tracks()[0].id) == str(client_ym.queue(client_ym.queues_list()[0].id).tracks[0].track_id):
                                playlist_id = 3
                            else:
                                await interaction.edit_original_response(
                                    content='Не удалось определить трек, на котором Вы остановились'
                                )
                                break
                        data_servers[interaction.guild.name]['task'] = asyncio.create_task(play(interaction, f"{playlist_id},{int(client_ym.queue(client_ym.queues_list()[0].id).current_index) + 1}"))
                        data_servers[interaction.guild.name]['index_play_now'] = int(client_ym.queue(client_ym.queues_list()[0].id).current_index)
                    elif type_of_playlist == 'radio':
                        check_mood_and_genre = False
                        for item in client_ym.rotor_stations_list():
                            if context.description == item.station.name:
                                check_mood_and_genre = True
                                data_servers[interaction.guild.name]['radio_check'] = {
                                    "name": context.description,
                                    "station": context.id,
                                    "station_from": context.id.split(':')[0]
                                }
                                break
                        if not check_mood_and_genre:
                            data_servers[interaction.guild.name]['stream_by_track_check'] = {
                                "name": context.description,
                                "station": context.id,
                                "station_from": context.id.split(':')[0]
                            }
                        await play_yandex_music_radio(
                            interaction=interaction,
                            station_id=context.id,
                            station_from=context.id.split(':')[0],
                            first_track=True,
                            new_task=True
                        )
                    elif type_of_playlist == 'album':
                        data_servers[interaction.guild.name]['album'] = True
                        data_servers[interaction.guild.name]['task'] = asyncio.create_task(play(
                            interaction=interaction,
                            url_or_trackname_or_filepath=f"{context.id},{int(client_ym.queue(client_ym.queues_list()[0].id).current_index) + 1}"
                        ))
                        data_servers[interaction.guild.name]['index_play_now'] = \
                            client_ym.queue(client_ym.queues_list()[0].id).current_index
                    break
                elif self.values[0] == "2":
                    await interaction.edit_original_response(
                        content='Загрузка радио "Моя волна". Подождите',
                        view=None
                    )
                    data_servers[interaction.guild.name]['radio_check'] = {
                        "name": "Моя волна",
                        "station": "user:onyourwave",
                        "station_from": 'user-onyourwave'
                    }
                    await play_yandex_music_radio(
                        interaction=interaction,
                        station_id=data_servers[interaction.guild.name]["radio_check"]["station"],
                        station_from=data_servers[interaction.guild.name]["radio_check"]["station_from"],
                        first_track=True,
                        new_task=True
                    )
                    break
                elif self.values[0] == "4":
                    await interaction.edit_original_response(
                        content='Загрузка жанров. Подождите',
                        view=None
                    )
                    j = 0
                    list_for_page = []
                    for item in client_ym.rotor_stations_list():
                        if j < 24:
                            list_for_page.append(
                                f"{item.station.id.type}:{item.station.id.tag},"
                                f"{item.station.id_for_from},"
                                f"{item.station.name}"
                            )
                            j += 1
                        else:
                            list_for_page.append(
                                f"{item.station.id.type}:{item.station.id.tag},"
                                f"{item.station.id_for_from},"
                                f"{item.station.name}"
                            )
                            data_servers[interaction.guild.name]['mood_and_genre'].append(list_for_page)
                            j = 0
                            list_for_page = []
                    if j > 0:
                        data_servers[interaction.guild.name]['mood_and_genre'].append(list_for_page)

                    self.view.clear_items()

                    self.view.add_item(MoodAndGenreSelect(interaction))
                    self.view.add_item(PrevPageButton(interaction, 'MoodAndGenreSelect', 'mood_and_genre'))
                    self.view.add_item(NextPageButton(interaction, 'MoodAndGenreSelect', 'mood_and_genre'))

                    await interaction.edit_original_response(
                        content=f"Страница {data_servers[interaction.guild.name]['mood_and_genre_page_index'] + 1} из "
                                f"{len(data_servers[interaction.guild.name]['mood_and_genre'])}",
                        view=self.view
                    )
                    break
                elif self.values[0] == "5":
                    await interaction.edit_original_response(
                        content='Загрузка альбомов. Подождите',
                        view=None
                    )
                    data_servers[interaction.guild.name]['album'] = True
                    j = 0
                    list_for_page = []
                    for item in client_ym.users_likes_albums():
                        if item.album.type not in ['podcast', 'audiobook']:
                            if j < 24:
                                list_for_page.append(
                                    f"{item.album.id},"
                                    f"{item.album.title},"
                                    f"{item.album.track_count},"
                                    f"{item.album.type}"
                                )
                                j += 1
                            else:
                                list_for_page.append(
                                    f"{item.album.id},"
                                    f"{item.album.title},"
                                    f"{item.album.track_count},"
                                    f"{item.album.type}"
                                )
                                data_servers[interaction.guild.name]['album_list'].append(list_for_page)
                                j = 0
                                list_for_page = []
                    if j > 0:
                        data_servers[interaction.guild.name]['album_list'].append(list_for_page)

                    self.view.clear_items()

                    self.view.add_item(AlbumListSelect(interaction))
                    self.view.add_item(PrevPageButton(interaction, 'AlbumListSelect', 'album_list'))
                    self.view.add_item(NextPageButton(interaction, 'AlbumListSelect', 'album_list'))

                    await interaction.edit_original_response(
                        content=f"Страница {data_servers[interaction.guild.name]['album_list_page_index'] + 1} из "
                                f"{len(data_servers[interaction.guild.name]['album_list'])}",
                        view=self.view
                    )
                    break
                else:
                    if self.values[0] == "3":
                        await interaction.edit_original_response(
                            content='Загрузка плейлиста "Мне нравится". Подождите',
                            view=None
                        )
                    else:
                        await interaction.edit_original_response(
                            content=f'Загрузка плейлиста "{client_ym.users_playlists(self.values[0]).title}". Подождите',
                            view=None
                        )
                    data_servers[interaction.guild.name]['task'] = asyncio.create_task(play(interaction, self.values[0]))
                    break
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
