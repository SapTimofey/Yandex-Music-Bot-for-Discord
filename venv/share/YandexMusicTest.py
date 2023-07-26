import yandex_music
from yandex_music import Client, Track

import discord
from discord import Embed, SelectOption, ButtonStyle, app_commands
from discord.ext import commands
from discord.ui import Button, View, Select

import asyncio
import os
import datetime
import textwrap
import re
from pytube import YouTube
from googleapiclient.discovery import build
from random import random
import copy


# Инициализируем Discord клиент
intents = discord.Intents.all()
intents.members = True
intents.messages = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
bot = commands.Bot(command_prefix='!', intents=intents)


'''
Глобальные переменные
'''
tokens = {}
birthdays = {}
google_token = None
YM_token = None
settings_onyourwave = {}
ru_settings_onyourwave = {
    'favorite': 'Любимое',
    'discover': 'Незнакомое',
    'popular': 'Популярное',
    'default': 'По умолчанию',
    'active': 'Бодрое',
    'fun': 'Весёлое',
    'calm': 'Спокойное',
    'sad': 'Грустное',
    'all': 'Любое',
    'russian': 'Русский',
    'not-russian': 'Иностранный',
    'without-words': 'Без слов',
    'any': 'Любой'
}
user = os.environ.get('USERNAME')
output_path = f'C:\\Users\\{user}\\Music'  # Путь к папке, где будет сохранен аудиофайл
data_server = {
    'playlist': [],
    'album': False,
    'album_list': [],
    'album_list_page_index': 0,
    'track_names_from_the_playlist': [],
    'track_list_page_index': 0,
    'mood_and_genre_page_index': 0,
    'repeat_flag': False,
    'queue_repeat': None,
    'index_play_now': 0,
    'task': None,
    'task_check_inactivity': None,
    'lyrics': None,
    'track_url': None,
    'cover_url': None,
    'track_id_play_now': None,
    'radio_client': None,
    'user_discord_play': None,
    'radio_check': False,
    'stream_by_track_check': False,
    'last_activity_time': datetime.datetime.now(),
    'message_check': None,
    'command_now': 0,
    'duration': 0,
    'can_edit_message': True,
    'mood_and_genre': []
}
data_servers = {}


# Загрузка токенов пользователей
if os.path.exists("tokens.txt") and os.path.getsize("tokens.txt") > 0:
    # загружаем данные из файла в глобальный словарь
    with open("tokens.txt", "r") as f:
        # читаем строки из файла
        lines = f.readlines()
        # перебираем строки и добавляем каждую пару ключ-значение в глобальный словарь
        for line in lines:
            # удаляем символы переноса строки и разделяем данные по пробелу
            user_discord, token = line.strip().rsplit(maxsplit=1)
            if user_discord == 'google':
                google_token = token
            elif user_discord == 'YandexMusicTest':
                YM_token = token
            else:
                # добавляем пару ключ-значение в глобальный словарь
                tokens[user_discord] = token
                birthdays[user_discord] = False


'''
Функции для обработки команд
'''
async def milliseconds_to_time(milliseconds):
    seconds, milliseconds = divmod(milliseconds, 1000)
    minutes, seconds = divmod(seconds, 60)
    return f"{minutes:02d}:{seconds:02d}"
async def birthday_send(interaction: discord.Interaction):
    global birthdays
    if str(interaction.user) in tokens:
        birthdays[str(interaction.user)] = True
        client_ym = Client(tokens[str(interaction.user)]).init()
        if client_ym.me.account.now.split('T')[0].split('-', maxsplit=1)[1] == \
                client_ym.me.account.birthday.split('-', maxsplit=1)[1]:
            await interaction.response.send_message(
                content=f"С Днём Рождения {client_ym.me.account.first_name} 🎉🎊",
                ephemeral=True
            )
async def remove_last_playing_message(interaction: discord.Interaction):
    async for message in interaction.channel.history():
        if message.author == client.user and \
                (message.content.startswith('Текст') or
                 message.content.startswith('Треки в очереди') or
                 message.content.startswith('Не удалось') or
                 message.content.startswith('Произошла ошибка') or
                 len(message.embeds) > 0):
            try:
                await message.delete()
            except Exception:
                pass
async def check_inactivity(interaction: discord.Interaction):
    global data_servers
    voice_client = interaction.guild.voice_client
    while True:
        try:
            if (datetime.datetime.now() - data_servers[interaction.guild.name]['last_activity_time'] > \
                    datetime.timedelta(minutes=5) and not voice_client.is_playing()) or \
                    (voice_client and not any(member != client.user for member in voice_client.channel.members)):
                await disconnect(interaction)
                break
            await asyncio.sleep(1)
        except asyncio.CancelledError:
            break
async def disconnect(interaction: discord.Interaction):
    global data_servers
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
async def check_audio_file(path):
    audio = AudioSegment.from_file(path)
    bitrate = audio.frame_rate * audio.channels * audio.sample_width * 8
    # print("bitrate = ", bitrate, "\nframe_rate = ", audio.frame_rate, "\nChannels = ", audio.channels, "\nsample_width = ", audio.sample_width)
    if (500 < bitrate < 512000):
        return True
    return False
async def play_YouTube(interaction: discord.Interaction, url_or_trackname_or_filepath):
    global data_servers
    error_count = 0
    while error_count < 3:
        try:
            data_servers[interaction.guild.name]['track_url'] = url_or_trackname_or_filepath

            # Извлеките идентификатор видео из ссылки
            video_id = re.findall(r'v=(\w+)', url_or_trackname_or_filepath)[0]

            # Создайте объект YouTube API
            youtube = build('youtube', 'v3', developerKey=google_token)

            # Получите информацию о видео
            video_info = youtube.videos().list(part='snippet,contentDetails', id=video_id).execute()

            # Извлеките продолжительность видео
            duration = video_info['items'][0]['contentDetails']['duration']
            # Удалите префикс "PT" из строки продолжительности
            duration = duration[2:]

            # Разделите строку на минуты и секунды
            minutes_pos = duration.find('M')
            seconds_pos = duration.find('S')
            minutes = int(duration[:minutes_pos])
            seconds = int(duration[minutes_pos + 1:seconds_pos])

            # Преобразуйте общее количество секунд в миллисекунды
            data_servers[interaction.guild.name]['duration'] = (minutes * 60 + seconds) * 1000

            # Извлеките название видео из полученных данных
            play_now = f"Название видео: {video_info['items'][0]['snippet']['title']}\n" \
                       f"Автор: {video_info['items'][0]['snippet']['channelTitle']}"

            # Извлеките URL превью из полученных данных
            data_servers[interaction.guild.name]['cover_url'] = video_info['items'][0]['snippet']['thumbnails']['high']['url']

            yt = YouTube(url_or_trackname_or_filepath)

            # Выбираем аудио поток с максимальным битрейтом
            audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()

            # Скачиваем аудио
            audio_stream.download(
                output_path=output_path,
                filename=f'{data_servers[interaction.guild.name]["user_discord_play"]}.mp3'
            )

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
async def play_Yandex_Music_url(interaction: discord.Interaction, url_or_trackname_or_filepath):
    global data_servers
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
            except yandex_music.exceptions.NotFoundError:
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
async def play_Yandex_Music_playlist(interaction: discord.Interaction, url_or_trackname_or_filepath):
    global data_servers
    error_count = 0
    playlist_ym = url_or_trackname_or_filepath.split(',')
    playlist_id = playlist_ym[0]
    index_track = None

    while error_count < 3:
        try:
            client_ym = Client(tokens[str(data_servers[interaction.guild.name]['user_discord_play'])]).init()
            if not data_servers[interaction.guild.name]['album']:
                if playlist_id == "3":
                    playlist_new = client_ym.users_likes_tracks().tracks
                    playlist_title = "Мне нравится"
                else:
                    try:
                        playlist_new = client_ym.users_playlists(playlist_id).tracks
                        playlist_title = client_ym.users_playlists(playlist_id).title
                    except yandex_music.exceptions.NotFoundError:
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
                album_title = client_ym.albums_with_tracks(playlist_id).title

            if not data_servers[interaction.guild.name]['playlist']:
                j = 0
                list = []
                service_index = 0
                for i in range(len(playlist_new)):
                    track_short = playlist_new[i]
                    track = client_ym.tracks(track_short.track_id)[0]
                    if track.available:
                        if index_track is None:
                            index_track = i + 1
                        data_servers[interaction.guild.name]['playlist'].append(f"{playlist_id},{i + 1}")
                        artists = track.artists
                        if not artists:
                            artist_all = ""
                        else:
                            artist_names = [artist.name for artist in artists]  # получаем список имен артистов
                            artist_all = ", ".join(artist_names)  # объединяем их через запятую
                        if j < 24:
                            if len(track.title) > 90:
                                track_title = track.title[:90]
                                list.append([service_index, i + 1, track_title, artist_all])
                            else:
                                list.append([service_index, i + 1, track.title, artist_all])
                            j += 1
                        else:
                            if len(track.title) > 90:
                                track_title = track.title[:90]
                                list.append([service_index, i + 1, track_title, artist_all])
                            else:
                                list.append([service_index, i + 1, track.title, artist_all])
                            data_servers[interaction.guild.name]['track_names_from_the_playlist'].append(list)
                            list = []
                            j = 0
                        service_index += 1
                if j > 0:
                    data_servers[interaction.guild.name]['track_names_from_the_playlist'].append(list)

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
                artist_names = [artist.name for artist in artists]  # получаем список имен артистов
                artist_all = ", ".join(artist_names)  # объединяем их через запятую
            if not data_servers[interaction.guild.name]['album']:
                if playlist_id == "3":
                    play_now = "\nПлейлист: Мне нравится"
                else:
                    play_now = f"\nПлейлист: {playlist_title}"
            else:
                play_now = f"\nАльбом: {album_title}"
            play_now += f"\nТрек: {track.title}" + \
                        f"\nИсполнители: {artist_all}" + \
                        f"\nНомер трека: {index_track} / {len(playlist_new)}"

            track.download(f'{output_path}\\{data_servers[interaction.guild.name]["user_discord_play"]}.mp3')

            try:
                data_servers[interaction.guild.name]['lyrics'] = track.get_lyrics().fetch_lyrics()
            except yandex_music.exceptions.NotFoundError:
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
                except:
                    pass
                await interaction.channel.send(f"Не удалось устранить ошибку {e}")
                return False
async def send_search_request(interaction: discord.Interaction, query):
    global data_servers
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
                except yandex_music.exceptions.NotFoundError:
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
async def play_radio(interaction: discord.Interaction, station_id: str, station_from: str, first_track: bool = False, new_task: bool=False):
    global data_servers
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


'''
Класс реализации радио
'''
class Radio:
    def __init__(self, client):
        self.client = client
        self.station_id = None
        self.station_from = None

        self.play_id = None
        self.index = 0
        self.current_track = None
        self.station_tracks = None

    def start_radio(self, station_id, station_from) -> Track:
        self.station_id = station_id
        self.station_from = station_from

        # get first 5 tracks
        self.__update_radio_batch(None)

        # setup current track
        self.current_track = self.__update_current_track()
        return self.current_track

    def play_next(self) -> Track:
        # send prev track finalize info
        self.__send_play_end_track(self.current_track, self.play_id)
        self.__send_play_end_radio(self.current_track, self.station_tracks.batch_id)

        # get next index
        self.index += 1
        if self.index >= len(self.station_tracks.sequence):
            # get next 5 tracks. Set index to 0
            self.__update_radio_batch(self.current_track.track_id)

        # setup next track
        self.current_track = self.__update_current_track()
        return self.current_track

    def __update_radio_batch(self, queue=None):
        self.index = 0
        self.station_tracks = self.client.rotor_station_tracks(self.station_id, queue=queue)
        self.__send_start_radio(self.station_tracks.batch_id)

    def __update_current_track(self):
        self.play_id = self.__generate_play_id()
        track = self.client.tracks([self.station_tracks.sequence[self.index].track.track_id])[0]
        self.__send_play_start_track(track, self.play_id)
        self.__send_play_start_radio(track, self.station_tracks.batch_id)
        return track

    def __send_start_radio(self, batch_id):
        self.client.rotor_station_feedback_radio_started(
            station=self.station_id, from_=self.station_from, batch_id=batch_id
        )

    def __send_play_start_track(self, track, play_id):
        total_seconds = track.duration_ms / 1000
        self.client.play_audio(
            from_="desktop_win-home-playlist_of_the_day-playlist-default",
            track_id=track.id,
            album_id=track.albums[0].id,
            play_id=play_id,
            track_length_seconds=0,
            total_played_seconds=0,
            end_position_seconds=total_seconds,
        )

    def __send_play_start_radio(self, track, batch_id):
        self.client.rotor_station_feedback_track_started(station=self.station_id, track_id=track.id, batch_id=batch_id)

    def __send_play_end_track(self, track, play_id):
        # played_seconds = 5.0
        played_seconds = track.duration_ms / 1000
        total_seconds = track.duration_ms / 1000
        self.client.play_audio(
            from_="desktop_win-home-playlist_of_the_day-playlist-default",
            track_id=track.id,
            album_id=track.albums[0].id,
            play_id=play_id,
            track_length_seconds=int(total_seconds),
            total_played_seconds=played_seconds,
            end_position_seconds=total_seconds,
        )

    def __send_play_end_radio(self, track, batch_id):
        played_seconds = track.duration_ms / 1000
        self.client.rotor_station_feedback_track_finished(
            station=self.station_id, track_id=track.id, total_played_seconds=played_seconds, batch_id=batch_id
        )
        pass

    @staticmethod
    def __generate_play_id():
        return "%s-%s-%s" % (int(random() * 1000), int(random() * 1000), int(random() * 1000))


'''
Классы реализации кнопок
'''
class repeat_button(Button):
    def __init__(self):
        super().__init__(style=ButtonStyle.primary, label="Повтор", emoji="🔂", row=2)

    async def callback(self, interaction: discord.Interaction):
        global data_servers
        data_servers[interaction.guild.name]['can_edit_message'] = False
        if self.style == ButtonStyle.green:
            self.style = ButtonStyle.primary  # изменяем стиль кнопки на primary
            data_servers[interaction.guild.name]['repeat_flag'] = False  # устанавливаем repeat_flag в False
        else:
            self.style = ButtonStyle.green  # изменяем стиль кнопки на зеленый
            data_servers[interaction.guild.name]['repeat_flag'] = True  # устанавливаем repeat_flag в True
        while True:
            try:
                await interaction.response.edit_message(view=self.view)  # обновляем стиль кнопки
                break
            except Exception:
                await asyncio.sleep(0.1)
        data_servers[interaction.guild.name]['can_edit_message'] = True
class next_button(Button):
    def __init__(self, interaction: discord.Interaction):
        super().__init__(
            style=ButtonStyle.primary,
            label="К следующему",
            emoji="⏭️",
            row=1,
            disabled=data_servers[interaction.guild.name]['index_play_now'] + 1 >=
                     len(data_servers[interaction.guild.name]['playlist']) and not
                     data_servers[interaction.guild.name]['radio_check'] and not
                     data_servers[interaction.guild.name]['stream_by_track_check']
        )

    async def callback(self, interaction: discord.Interaction):
        global data_servers
        data_servers[interaction.guild.name]['repeat_flag'] = False
        voice_client = interaction.guild.voice_client
        voice_client.stop()
class prev_button(Button):
    def __init__(self, interaction: discord.Interaction):
        super().__init__(
            style=ButtonStyle.primary,
            label="К предыдущему",
            emoji="⏮️",
            row=1,
            disabled=data_servers[interaction.guild.name]['index_play_now'] - 1 < 0 or
                     data_servers[interaction.guild.name]['radio_check'] or
                     data_servers[interaction.guild.name]['stream_by_track_check']
        )

    async def callback(self, interaction: discord.Interaction):
        global data_servers
        data_servers[interaction.guild.name]['repeat_flag'] = False
        voice_client = interaction.guild.voice_client
        voice_client.stop()
        data_servers[interaction.guild.name]['index_play_now'] -= 2
class pause_resume_button(Button):
    def __init__(self):
        super().__init__(style=ButtonStyle.primary, label="Пауза/Продолжить", emoji="⏯️", row=1)

    async def callback(self, interaction: discord.Interaction):
        global data_servers
        data_servers[interaction.guild.name]['can_edit_message'] = False
        voice_client = interaction.guild.voice_client  # use the attribute
        if self.style == ButtonStyle.green:
            self.style = ButtonStyle.primary  # изменяем стиль кнопки на primary
            voice_client.resume()
        else:
            self.style = ButtonStyle.green  # изменяем стиль кнопки на зеленый
            voice_client.pause()
        while True:
            try:
                await interaction.response.edit_message(view=self.view)  # обновляем стиль кнопки
                break
            except Exception:
                await asyncio.sleep(0.1)
        data_servers[interaction.guild.name]['can_edit_message'] = True
class disconnect_button(Button):
    def __init__(self):
        super().__init__(style=ButtonStyle.red, label="Отключить", emoji="📛", row=3)

    async def callback(self, interaction: discord.Interaction):
        await disconnect(interaction)
class lyrics_button(Button):
    def __init__(self, interaction: discord.Interaction):
        super().__init__(
            style=ButtonStyle.primary,
            label="Текст",
            emoji="🗒️",
            row=2,
            disabled=data_servers[interaction.guild.name]['lyrics'] is None
        )

    async def callback(self, interaction: discord.Interaction):
        global data_servers
        data_servers[interaction.guild.name]['can_edit_message'] = False
        await asyncio.sleep(1)
        if self.style == ButtonStyle.success:
            self.style = ButtonStyle.primary  # изменяем стиль кнопки на primary
            async for message in interaction.channel.history():
                if message.author == client.user and message.content.startswith('Текст'):
                    await message.delete()
        else:
            self.style = ButtonStyle.success  # изменяем стиль кнопки на зеленый
            if len(data_servers[interaction.guild.name]['lyrics']) > 2000:
                parts = textwrap.wrap(
                    data_servers[interaction.guild.name]['lyrics'],
                    width=1800,
                    break_long_words=False,
                    replace_whitespace=False
                )
                await interaction.channel.send(f"Текст трека (часть 1):\n{parts[0]}")
                await interaction.channel.send(f"Текст трека (часть 2):\n{parts[1]}")
            else:
                await interaction.channel.send(f"Текст трека:\n{data_servers[interaction.guild.name]['lyrics']}")
        while True:
            try:
                await interaction.response.edit_message(view=self.view)  # обновляем стиль кнопки
                break
            except Exception:
                await asyncio.sleep(0.1)
        data_servers[interaction.guild.name]['can_edit_message'] = True
class track_url_button(Button):
    def __init__(self, interaction: discord.Interaction):
        if data_servers[interaction.guild.name]['track_url']:
            super().__init__(
                style=ButtonStyle.url,
                label="Ссылка",
                emoji="🌐",
                url=data_servers[interaction.guild.name]['track_url'],
                row=2
            )
        else:
            super().__init__(
                style=ButtonStyle.grey,
                label="Ссылка",
                emoji="🌐",
                disabled=True,
                row=2
            )
class stream_by_track_button(Button):
    def __init__(self, interaction: discord.Interaction):
        if not data_servers[interaction.guild.name]['track_url'] or 'youtube.com' in data_servers[interaction.guild.name]['track_url']:
            disabled = True
        else:
            disabled = False
        super().__init__(
            style=ButtonStyle.primary,
            label="Моя волна по треку",
            emoji="💫",
            row=2,
            disabled=disabled
        )

    async def callback(self, interaction: discord.Interaction):
        global data_servers
        client_ym = Client(tokens[str(data_servers[interaction.guild.name]['user_discord_play'])]).init()
        track  = client_ym.tracks(data_servers[interaction.guild.name]['track_id_play_now'])[0]

        data_servers[interaction.guild.name]['radio_check'] = False
        data_servers[interaction.guild.name]['album'] = False
        data_servers[interaction.guild.name]['stream_by_track_check'] = {
            "name": 'Моя волна по треку ' + track.title,
            "station": 'track:' + data_servers[interaction.guild.name]['track_id_play_now'],
            "station_from": 'track'
        }
        data_servers[interaction.guild.name]['playlist'] = []
        data_servers[interaction.guild.name]['track_names_from_the_playlist'] = []
        data_servers[interaction.guild.name]['index_play_now'] = 0

        voice_client = interaction.guild.voice_client
        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()
            data_servers[interaction.guild.name]['task'].cancel()
        await play_radio(
            interaction=interaction,
            station_id=data_servers[interaction.guild.name]['stream_by_track_check']['station'],
            station_from=data_servers[interaction.guild.name]['stream_by_track_check']['station_from'],
            first_track=True,
            new_task=True
        )
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
        global data_servers
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
                    type = context.type
                    if type == 'playlist':
                        data_servers[interaction.guild.name]['task'] = asyncio.create_task(play(
                            interaction=interaction,
                            url_or_trackname_or_filepath=f"{context.id.split(':')[1]},{int(client_ym.queue(client_ym.queues_list()[0].id).current_index) + 1}"
                        ))
                        data_servers[interaction.guild.name]['index_play_now'] = \
                            client_ym.queue(client_ym.queues_list()[0].id).current_index
                    elif type == 'my_music':
                        find = False
                        for playlist in client_ym.users_playlists_list():
                            playlist_id = playlist.playlist_id.split(':')[1]
                            if str(client_ym.users_playlists(playlist_id).tracks[0].id) == str(client_ym.queue(client_ym.queues_list()[0].id).tracks[0].track_id):
                                find = True
                                break
                        if not find:
                            if str(client_ym.users_likes_tracks()[0].id) == str(client_ym.queue(client_ym.queues_list()[0].id).tracks[0].track_id):
                                playlist_id = 3
                        data_servers[interaction.guild.name]['task'] = asyncio.create_task(play(interaction, f"{playlist_id},{int(client_ym.queue(client_ym.queues_list()[0].id).current_index) + 1}"))
                        data_servers[interaction.guild.name]['index_play_now'] = int(client_ym.queue(client_ym.queues_list()[0].id).current_index)
                    elif type == 'radio':
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
                        await play_radio(
                            interaction=interaction,
                            station_id=context.id,
                            station_from=context.id.split(':')[0],
                            first_track=True,
                            new_task=True
                        )
                    elif type == 'album':
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
                    await play_radio(
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
                    list = []
                    for item in client_ym.rotor_stations_list():
                        if j < 24:
                            list.append(
                                f"{item.station.id.type}:{item.station.id.tag},"
                                f"{item.station.id_for_from},"
                                f"{item.station.name}"
                            )
                            j += 1
                        else:
                            list.append(
                                f"{item.station.id.type}:{item.station.id.tag},"
                                f"{item.station.id_for_from},"
                                f"{item.station.name}"
                            )
                            data_servers[interaction.guild.name]['mood_and_genre'].append(list)
                            j = 0
                            list = []
                    if j > 0:
                        data_servers[interaction.guild.name]['mood_and_genre'].append(list)

                    self.view.clear_items()

                    self.view.add_item(mood_and_genre_select(interaction))
                    self.view.add_item(mood_and_genre_prev_page(interaction))
                    self.view.add_item(mood_and_genre_next_page(interaction))

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
                    list = []
                    for item in client_ym.users_likes_albums():
                        if item.album.type not in ['podcast', 'audiobook']:
                            if j < 24:
                                list.append(
                                    f"{item.album.id},"
                                    f"{item.album.title},"
                                    f"{item.album.track_count},"
                                    f"{item.album.type}"
                                )
                                j += 1
                            else:
                                list.append(
                                    f"{item.album.id},"
                                    f"{item.album.title},"
                                    f"{item.album.track_count},"
                                    f"{item.album.type}"
                                )
                                data_servers[interaction.guild.name]['album_list'].append(list)
                                j = 0
                                list = []
                    if j > 0:
                        data_servers[interaction.guild.name]['album_list'].append(list)

                    self.view.clear_items()

                    self.view.add_item(selecting_an_album_from_the_list(interaction))
                    self.view.add_item(album_list_prev_page(interaction))
                    self.view.add_item(album_list_next_page(interaction))

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
            except Exception:
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
class onyourwave_setting_button(Button):
    def __init__(self):
        super().__init__(
            style=ButtonStyle.primary,
            label="Настроить радио",
            emoji="⚙️",
            row=3
        )

    async def callback(self, interaction: discord.Interaction):
        view = View(timeout=1200.0)
        view.add_item(onyourwave_setting_diversity())
        view.add_item(onyourwave_setting_mood_energy())
        view.add_item(onyourwave_setting_language())
        embed = discord.Embed(
            title=f'Настройки радио: {data_servers[interaction.guild.name]["radio_check"]["name"]}',
            color=0xf1ca0d,
            description=f'Характер: {ru_settings_onyourwave[settings_onyourwave[str(data_servers[interaction.guild.name]["user_discord_play"])]["diversity"]]}\n'
                        f'Настроение: {ru_settings_onyourwave[settings_onyourwave[str(data_servers[interaction.guild.name]["user_discord_play"])]["mood_energy"]]}\n'
                        f'Язык: {ru_settings_onyourwave[settings_onyourwave[str(data_servers[interaction.guild.name]["user_discord_play"])]["language"]]}'
        )
        await interaction.response.send_message(view=view, embed=embed, ephemeral=True)
class onyourwave_setting_diversity(Select):
    def __init__(self):
        super().__init__(placeholder='По характеру...', min_values=1, max_values=1, options=[
            SelectOption(label='Любимое', value='favorite', emoji='💖'),
            SelectOption(label='Незнакомое', value='discover', emoji='✨'),
            SelectOption(label='Популярное', value='popular', emoji='⚡'),
            SelectOption(label='По умолчанию', value='default', emoji='♦️')
        ])

    async def callback(self, interaction: discord.Interaction):
        global settings_onyourwave, data_servers
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
            await play_radio(
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
class onyourwave_setting_mood_energy(Select):
    def __init__(self):
        super().__init__(placeholder='Под настроение...', min_values=1, max_values=1, options=[
            SelectOption(label='Бодрое', value='active', emoji='🟠'),
            SelectOption(label='Весёлое', value='fun', emoji='🟢'),
            SelectOption(label='Спокойное', value='calm', emoji='🔵'),
            SelectOption(label='Грустное', value='sad', emoji='🟣'),
            SelectOption(label='Любое', value='all', emoji='🔘')
        ])

    async def callback(self, interaction: discord.Interaction):
        global settings_onyourwave, data_servers
        await interaction.response.defer()
        try:
            settings_onyourwave[str(data_servers[interaction.guild.name]['user_discord_play'])]['mood_energy'] = self.values[0]

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
            await play_radio(
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
class onyourwave_setting_language(Select):
    def __init__(self):
        super().__init__(placeholder='По языку...', min_values=1, max_values=1, options=[
            SelectOption(label='Русский', value='russian'),
            SelectOption(label='Иностранный', value='not-russian'),
            SelectOption(label='Без слов', value='without-words'),
            SelectOption(label='Любой', value='any')
        ])

    async def callback(self, interaction: discord.Interaction):
        global settings_onyourwave, data_servers
        await interaction.response.defer()
        try:
            settings_onyourwave[str(data_servers[interaction.guild.name]['user_discord_play'])]['language'] = self.values[0]

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
            await play_radio(
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
class selecting_a_track_from_a_playlist_button(Button):
    def __init__(self):
        super().__init__(
            style=ButtonStyle.primary,
            label="Выбор трека",
            row=3,
            emoji='🔎'
        )

    async def callback(self, interaction: discord.Interaction):
        view = View(timeout=1200)
        view.add_item(selecting_a_track_from_a_playlist(interaction))
        view.add_item(track_list_prev_page(interaction))
        view.add_item(track_list_next_page(interaction))
        await interaction.response.send_message(
            content=f"Страница {data_servers[interaction.guild.name]['track_list_page_index'] + 1} из "
                    f"{len(data_servers[interaction.guild.name]['track_names_from_the_playlist'])}",
            view=view,
            ephemeral=True
        )
class selecting_a_track_from_a_playlist(Select):
    def __init__(self, interaction: discord.Interaction):
        self.interaction = interaction
        options = []
        interval = data_servers[interaction.guild.name]['track_names_from_the_playlist'][data_servers[interaction.guild.name]['track_list_page_index']]
        for item in interval:
            options.append(SelectOption(
                label=f"{item[1]} - {item[2]}",
                value=item[0],
                description=item[3])
            )

        super().__init__(placeholder="Выберете трек...", min_values=1, max_values=1, options=options, row=1)

    async def callback(self, interaction: discord.Interaction):
        global data_servers
        await interaction.response.defer()
        await self.interaction.edit_original_response(
            content=f"Загрузка трека. Подождите\n"
                    f"Страница {data_servers[interaction.guild.name]['track_list_page_index'] + 1} из "
                    f"{len(data_servers[interaction.guild.name]['track_names_from_the_playlist'])}"
        )
        data_servers[interaction.guild.name]['index_play_now'] = int(self.values[0]) - 1
        voice_client = interaction.guild.voice_client
        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()
        await self.interaction.delete_original_response()
class track_list_next_page(Button):
    def __init__(self, interaction: discord.Interaction):
        super().__init__(
            style=ButtonStyle.primary,
            emoji="➡️",
            row=2,
            disabled=data_servers[interaction.guild.name]['track_list_page_index'] + 1 >=
                     len(data_servers[interaction.guild.name]['track_names_from_the_playlist'])
        )

    async def callback(self, interaction: discord.Interaction):
        global data_servers
        await interaction.response.defer()
        data_servers[interaction.guild.name]['track_list_page_index'] += 1
        self.view.clear_items()

        self.view.add_item(selecting_a_track_from_a_playlist(interaction))
        self.view.add_item(track_list_prev_page(interaction))
        self.view.add_item(track_list_next_page(interaction))
        await interaction.edit_original_response(
            content=f"Страница {data_servers[interaction.guild.name]['track_list_page_index'] + 1} из "
                    f"{len(data_servers[interaction.guild.name]['track_names_from_the_playlist'])}",
            view=self.view
        )
class track_list_prev_page(Button):
    def __init__(self, interaction: discord.Interaction):
        super().__init__(
            style=ButtonStyle.primary,
            emoji="⬅️",
            row=2,
            disabled=data_servers[interaction.guild.name]['track_list_page_index'] - 1 < 0
        )

    async def callback(self, interaction: discord.Interaction):
        global data_servers
        await interaction.response.defer()
        data_servers[interaction.guild.name]['track_list_page_index'] -= 1
        self.view.clear_items()

        self.view.add_item(selecting_a_track_from_a_playlist(interaction))
        self.view.add_item(track_list_prev_page(interaction))
        self.view.add_item(track_list_next_page(interaction))
        await interaction.edit_original_response(
            content=f"Страница {data_servers[interaction.guild.name]['track_list_page_index'] + 1} из "
                    f"{len(data_servers[interaction.guild.name]['track_names_from_the_playlist'])}",
            view=self.view
        )
class mood_and_genre_select(Select):
    def __init__(self, interaction: discord.Interaction):
        self.interaction = interaction
        options = []
        interval = data_servers[interaction.guild.name]['mood_and_genre'][data_servers[interaction.guild.name]['mood_and_genre_page_index']]
        for item in interval:
            options.append(SelectOption(
                label=item.split(',')[2],
                value=item
            ))

        super().__init__(placeholder="Выберете жанр...", min_values=1, max_values=1, options=options, row=1)

    async def callback(self, interaction: discord.Interaction):
        global data_servers
        await interaction.response.defer()
        await self.interaction.edit_original_response(
            content=f'Загрузка Радио "{self.values[0].split(",")[2]}". Подождите',
            view=None
        )
        data_servers[interaction.guild.name]['radio_check'] = {
            "name": self.values[0].split(",")[2],
            "station": self.values[0].split(",")[0],
            "station_from": self.values[0].split(',')[1]
        }
        data_servers[interaction.guild.name]['stream_by_track_check'] = False
        data_servers[interaction.guild.name]['mood_and_genre'] = []
        await play_radio(
            interaction=interaction,
            station_id=self.values[0].split(',')[0],
            station_from=self.values[0].split(',')[1],
            first_track=True,
            new_task=True
        )
class mood_and_genre_next_page(Button):
    def __init__(self, interaction: discord.Interaction):
        super().__init__(
            style=ButtonStyle.primary,
            emoji="➡️",
            row=2,
            disabled=data_servers[interaction.guild.name]['mood_and_genre_page_index'] + 1 >=
                     len(data_servers[interaction.guild.name]['mood_and_genre'])
        )

    async def callback(self, interaction: discord.Interaction):
        global data_servers
        await interaction.response.defer()
        data_servers[interaction.guild.name]['mood_and_genre_page_index'] += 1
        self.view.clear_items()

        self.view.add_item(mood_and_genre_select(interaction))
        self.view.add_item(mood_and_genre_prev_page(interaction))
        self.view.add_item(mood_and_genre_next_page(interaction))
        await interaction.edit_original_response(
            content=f"Страница {data_servers[interaction.guild.name]['mood_and_genre_page_index'] + 1} из "
                    f"{len(data_servers[interaction.guild.name]['mood_and_genre'])}",
            view=self.view
        )
class mood_and_genre_prev_page(Button):
    def __init__(self, interaction: discord.Interaction):
        super().__init__(
            style=ButtonStyle.primary,
            emoji="⬅️",
            row=2,
            disabled=data_servers[interaction.guild.name]['mood_and_genre_page_index'] - 1 < 0
        )

    async def callback(self, interaction: discord.Interaction):
        global data_servers
        await interaction.response.defer()
        data_servers[interaction.guild.name]['mood_and_genre_page_index'] -= 1
        self.view.clear_items()

        self.view.add_item(mood_and_genre_select(interaction))
        self.view.add_item(mood_and_genre_prev_page(interaction))
        self.view.add_item(mood_and_genre_next_page(interaction))
        await interaction.edit_original_response(
            content=f"Страница {data_servers[interaction.guild.name]['mood_and_genre_page_index'] + 1} из "
                    f"{len(data_servers[interaction.guild.name]['mood_and_genre'])}",
            view=self.view
        )
class selecting_an_album_from_the_list(Select):
    def __init__(self, interaction: discord.Interaction):
        self.interaction = interaction
        options = []
        interval = data_servers[interaction.guild.name]['album_list'][data_servers[interaction.guild.name]['album_list_page_index']]
        for item in interval:
            if item.split(',')[3] == 'single':
                options.append(SelectOption(
                    label=item.split(',')[1],
                    value=item,
                    description=f"Количество треков: {item.split(',')[2]} - сингл"
                ))
            else:
                options.append(SelectOption(
                    label=item.split(',')[1],
                    value=item,
                    description=f"Количество треков: {item.split(',')[2]}"
                ))

        super().__init__(placeholder="Выберете альбом...", min_values=1, max_values=1, options=options, row=1)

    async def callback(self, interaction: discord.Interaction):
        global data_servers
        await interaction.response.defer()
        await self.interaction.edit_original_response(
            content=f'Загрузка альбома "{self.values[0].split(",")[1]}". Подождите\n',
            view=None
        )
        data_servers[interaction.guild.name]['album_list'] = []
        data_servers[interaction.guild.name]['task'] = \
            asyncio.create_task(play(
                interaction=interaction,
                url_or_trackname_or_filepath=self.values[0].split(',')[0]
            ))
class album_list_next_page(Button):
    def __init__(self, interaction: discord.Interaction):
        super().__init__(
            style=ButtonStyle.primary,
            emoji="➡️",
            row=2,
            disabled=data_servers[interaction.guild.name]['album_list_page_index'] + 1 >=
                     len(data_servers[interaction.guild.name]['album_list'])
        )

    async def callback(self, interaction: discord.Interaction):
        global data_servers
        await interaction.response.defer()
        data_servers[interaction.guild.name]['album_list_page_index'] += 1
        self.view.clear_items()

        self.view.add_item(selecting_an_album_from_the_list(interaction))
        self.view.add_item(album_list_prev_page(interaction))
        self.view.add_item(album_list_prev_page(interaction))
        await interaction.edit_original_response(
            content=f"Страница {data_servers[interaction.guild.name]['album_list_page_index'] + 1} из "
                    f"{len(data_servers[interaction.guild.name]['album_list'])}",
            view=self.view
        )
class album_list_prev_page(Button):
    def __init__(self, interaction: discord.Interaction):
        super().__init__(
            style=ButtonStyle.primary,
            emoji="⬅️",
            row=2,
            disabled=data_servers[interaction.guild.name]['album_list_page_index'] - 1 < 0
        )

    async def callback(self, interaction: discord.Interaction):
        global data_servers
        await interaction.response.defer()
        data_servers[interaction.guild.name]['album_list_page_index'] -= 1
        self.view.clear_items()

        self.view.add_item(selecting_an_album_from_the_list(interaction))
        self.view.add_item(album_list_prev_page(interaction))
        self.view.add_item(album_list_next_page(interaction))
        await interaction.edit_original_response(
            content=f"Страница {data_servers[interaction.guild.name]['album_list_page_index'] + 1} из "
                    f"{len(data_servers[interaction.guild.name]['album_list'])}",
            view=self.view
        )


'''
Функции для реализации команд
'''
@tree.command(name='play', description="🎧Воспроизвести трек. При вызове без аргумента - воспроизвести плейлист из списка")
@app_commands.rename(url_or_trackname_or_filepath='ссылка_или_название')
@app_commands.describe(url_or_trackname_or_filepath='Ссылка на трек / альбом из Яндекс.Музыки; Ссылка на трек из YouTube; Название трека')
async def start_play(interaction: discord.Interaction, url_or_trackname_or_filepath: str = None):
    global data_servers, settings_onyourwave

    await remove_last_playing_message(interaction)
    await interaction.response.defer(ephemeral=True)

    author_voice_state = interaction.user.voice
    if author_voice_state is None:
        await interaction.edit_original_response(content="В ожидании, когда Вы подключитесь к голосовому каналу.")
        while not author_voice_state:
            await asyncio.sleep(0.1)
            author_voice_state = interaction.user.voice

    # Проверяем, подключен ли бот к голосовому каналу
    voice_client = interaction.guild.voice_client

    if not voice_client:
        voice_channel = interaction.user.voice.channel
        await voice_channel.connect()
        voice_client = interaction.guild.voice_client

    if interaction.guild.name not in data_servers:
        data_servers[interaction.guild.name] = copy.deepcopy(data_server)
    else:
        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()
            data_servers[interaction.guild.name]['task'].cancel()
            data_servers[interaction.guild.name]['task_check_inactivity'].cancel()

    if str(interaction.user) in tokens:
        client_ym = Client(tokens[str(interaction.user)]).init()
        settings2 = client_ym.rotor_station_info('user:onyourwave')[0]['settings2']
        settings_onyourwave[str(interaction.user)] = {
            'mood_energy': settings2['mood_energy'],
            'diversity': settings2['diversity'],
            'language': settings2['language']
        }

    data_servers[interaction.guild.name] = copy.deepcopy(data_server)
    data_servers[interaction.guild.name]['task_check_inactivity'] = \
        asyncio.create_task(check_inactivity(interaction))

    if (not url_or_trackname_or_filepath or "youtube.com" not in url_or_trackname_or_filepath) and \
            str(interaction.user) not in tokens:
            await interaction.edit_original_response(
                content="Вы не вошли в аккаунт Яндекс.Музыки. Для входа воспользуйтесь командой /authorize")
            return

    data_servers[interaction.guild.name]['user_discord_play'] = interaction.user

    await interaction.edit_original_response(content="Загрузка Вашей музыки. Подождите")

    data_servers[interaction.guild.name]['task'] = asyncio.create_task(play(
            interaction=interaction,
            url_or_trackname_or_filepath=url_or_trackname_or_filepath
        ))

    while not voice_client.is_playing():
        await asyncio.sleep(0.1)
    try:
        await interaction.delete_original_response()
    except:
        pass
async def play(interaction: discord.Interaction, url_or_trackname_or_filepath: str = None):
    try:
        global data_servers

        voice_client = interaction.guild.voice_client

        if not url_or_trackname_or_filepath:  # если не передан url
            view = View()
            view.add_item(PlaylistSelect(interaction))
            await interaction.edit_original_response(content='', view=view)
            return

        while True:
            if "youtube.com" in url_or_trackname_or_filepath:
                play_now = await play_YouTube(interaction, url_or_trackname_or_filepath)
                if not play_now:
                    return

            elif "music.yandex.ru" in url_or_trackname_or_filepath:
                play_now = await play_Yandex_Music_url(interaction, url_or_trackname_or_filepath)
                if not play_now:
                    return

            elif ":\\" in url_or_trackname_or_filepath:
                play_now = url_or_trackname_or_filepath
                audio_file_path = url_or_trackname_or_filepath

                # Проверяем, что файл существует
                if not os.path.isfile(audio_file_path):
                    await interaction.edit_original_response(
                        content=f"Файл `{url_or_trackname_or_filepath}` не найден.",
                    )
                    return

            else:
                play_now = await play_Yandex_Music_playlist(interaction, url_or_trackname_or_filepath)
                if not play_now:
                    return

            data_servers[interaction.guild.name]['queue_repeat'] = url_or_trackname_or_filepath
            options = '-loglevel panic'
            audio_source = await discord.FFmpegOpusAudio.from_probe(
                source=f'{output_path}\\{data_servers[interaction.guild.name]["user_discord_play"]}.mp3',
                options=options
            )

            # Проигрываем аудио
            voice_client.play(audio_source)

            duration_track = await milliseconds_to_time(data_servers[interaction.guild.name]['duration'])
            start_time = 0

            if not birthdays[str(data_servers[interaction.guild.name]['user_discord_play'])]:
                await birthday_send(interaction)

            if not data_servers[interaction.guild.name]['repeat_flag']:
                await remove_last_playing_message(interaction)
                view = View(timeout=1200.0)

                view.add_item(prev_button(interaction))
                view.add_item(pause_resume_button())
                view.add_item(next_button(interaction))
                view.add_item(repeat_button())
                view.add_item(lyrics_button(interaction))
                view.add_item(track_url_button(interaction))
                view.add_item(disconnect_button())
                view.add_item(stream_by_track_button(interaction))

                if data_servers[interaction.guild.name]['playlist']:
                    view.add_item(selecting_a_track_from_a_playlist_button())
                elif data_servers[interaction.guild.name]['radio_check']:
                    view.add_item(onyourwave_setting_button())

                embed = Embed(title="Сейчас играет", description=play_now, color=0xf1ca0d)
                embed.add_field(name=f'00:00 / {duration_track}', value='')

                text = f"{str(data_servers[interaction.guild.name]['user_discord_play']).split('#')[0]} запустил "

                if data_servers[interaction.guild.name]['radio_check'] or \
                        data_servers[interaction.guild.name]['stream_by_track_check']:
                    text += "радио"
                elif data_servers[interaction.guild.name]['playlist']:
                    if data_servers[interaction.guild.name]['album']:
                        text += "альбом"
                    else:
                        text += "плейлист"
                else:
                    text += "трек"

                embed.set_footer(
                    text=text,
                    icon_url=data_servers[interaction.guild.name]['user_discord_play'].avatar
                )
                embed.set_thumbnail(url=data_servers[interaction.guild.name]['cover_url'])

                message = await interaction.channel.send(embed=embed, view=view)
                data_servers[interaction.guild.name]['message_check'] = message
            else:
                embed.clear_fields()
                embed.add_field(name=f'00:00 / {duration_track}', value='')
                try:
                    await data_servers[interaction.guild.name]['message_check'].edit(embed=embed)
                except Exception:
                    pass

            while voice_client.is_playing() or voice_client.is_paused():
                if voice_client.is_playing():
                    start_time_inaccuracy = datetime.datetime.now()
                    start_time += 1000
                    if data_servers[interaction.guild.name]['can_edit_message']:
                        time_now = await milliseconds_to_time(start_time)
                        embed.clear_fields()
                        embed.add_field(name=f'{time_now} / {duration_track}', value='')
                        try:
                            await data_servers[interaction.guild.name]['message_check'].edit(embed=embed)
                        except Exception:
                            pass
                    data_servers[interaction.guild.name]['last_activity_time'] = datetime.datetime.now()
                    end_time_inaccuracy = datetime.datetime.now()
                await asyncio.sleep(1 - (end_time_inaccuracy - start_time_inaccuracy).microseconds / 1000000)

            if data_servers[interaction.guild.name]['repeat_flag']:
                url_or_trackname_or_filepath = data_servers[interaction.guild.name]['queue_repeat']

            elif data_servers[interaction.guild.name]['radio_check']:
                url_or_trackname_or_filepath = await play_radio(
                    interaction=interaction,
                    station_id=data_servers[interaction.guild.name]["radio_check"]["station"],
                    station_from=data_servers[interaction.guild.name]["radio_check"]["station_from"]
                )

            elif data_servers[interaction.guild.name]['stream_by_track_check']:
                url_or_trackname_or_filepath = await play_radio(
                    interaction=interaction,
                    station_id=data_servers[interaction.guild.name]['stream_by_track_check']["station"],
                    station_from=data_servers[interaction.guild.name]['stream_by_track_check']["station_from"]
                )

            else:
                if data_servers[interaction.guild.name]['index_play_now'] + 1 < len(
                        data_servers[interaction.guild.name]['playlist']):
                    data_servers[interaction.guild.name]['index_play_now'] += 1
                    url_or_trackname_or_filepath = \
                        data_servers[interaction.guild.name]['playlist'][data_servers[interaction.guild.name]['index_play_now']]
                else:
                    await interaction.channel.send("Треки в очереди закончились")
                    return

    except asyncio.CancelledError:
        pass
    except Exception as e:
        try:
            await interaction.delete_original_response()
        except:
            pass
        await interaction.channel.send(f"Произошла ошибка: {e}.")

@start_play.autocomplete('url_or_trackname_or_filepath')
async def search_yandex_music(interaction: discord.Interaction, search: str):
    global tokens
    user_discord = interaction.user
    url_or_trackname_or_filepath = []
    if ("youtube.com" or "music.yandex.ru") not in search:
        if str(user_discord) in tokens:
            client_ym = Client(tokens[str(user_discord)]).init()
            search_result = client_ym.search(search)
            if search_result.tracks.results:
                for item in search_result.tracks.results:
                    artists = ''
                    if item.artists:
                        artists = ' - ' + ', '.join(artist.name for artist in item.artists)
                    url_or_trackname_or_filepath.append(item.title + artists)
    return [app_commands.Choice(name=item, value=item) for item in url_or_trackname_or_filepath ]

@tree.command(name='authorize', description="🔑Авторизация для использования сервиса Яндекс.Музыка")
@app_commands.describe(token='Вам нужно указать свой токен от аккаунта Яндекс.Музыки')
async def authorize(interaction: discord.Interaction, token: str):
    global tokens, birthdays
    try:
        if str(interaction.user) in tokens:
            await interaction.response.send_message("Вы уже авторизованы 🥰", ephemeral=True)
            return

        client_check = Client(str(token)).init()
    except Exception:
        await interaction.response.send_message("К сожалению Ваш токен неправильный 😞", ephemeral=True)
    else:
        await interaction.response.send_message("Вы успешно авторизовались 😍", ephemeral=True)
        user_discord = str(interaction.user)
        tokens[user_discord] = str(token)
        birthdays[user_discord] = False

        # записываем данные в файл
        with open("tokens.txt", "a") as f:
            f.seek(0, 2)  # перемещаем курсор в конец файла
            f.write(user_discord + " " + str(token) + "\n")

@tree.command(name='log', description="Служебная команда")
@app_commands.describe(server_name='По умоляанию Ваш сервер.')
@app_commands.default_permissions()
async def log(interaction: discord.Interaction, server_name: str = None):
    global data_servers
    await interaction.response.defer(ephemeral=True)

    if not server_name:
        server_name = interaction.guild.name

    if server_name in data_servers:
        message = ''
        for item in data_servers[server_name]:
            if item == 'lyrics' and data_servers[server_name][item]:
                message += f'{item}: is present\n'
            else:
                message += f'{item}: {data_servers[server_name][item]}\n'

        filename = f'{server_name}_log.txt'
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(message)

        await interaction.edit_original_response(attachments=[discord.File(filename)])
    else:
        await interaction.edit_original_response(content="Такого сервера в логах нет")

@log.autocomplete('server_name')
async def autocomplete_log(interaction: discord.Interaction, search: str):
    global data_servers
    return [app_commands.Choice(name=item, value=item) for item in data_servers if search in item]

@tree.command(name='help', description="❓Справка по командам")
async def commands(interaction: discord.Interaction):
    global data_servers
    if interaction.guild.name not in data_servers:
        data_servers[interaction.guild.name] = copy.deepcopy(data_server)
    command = {'/play': 'Имеет необязательный аргумент \'ссылка_или_название\'\n\n'
                        'При вызове команды без аргумента - предложит выбрать плейлист / радио / альбом из списка и запустит его\n\n'
                        'В аргумент можно передать:\n'
                        '1. Ссылку на видео YouTube\n'
                        '2. Ссылку на трек / альбом из Яндекс.Музыки\n'
                        '3. Название трека (При вводе можно выбрать из выпадающего списка)\n',
               '/authorize': 'Имеет обязательный аргумент \'token\'\n\n'
                             'В аргумент нужно передать Ваш токен от аккаунта Яндекс.Музыки\n\n'
                             'Без авторизации Вы не сможете пользоваться Яндекс.Музыкой\n\n'
                             'С инструкцией по получению токена можно ознакимиться здесь:\nhttps://github.com/MarshalX/yandex-music-api/discussions/513\n\n'
                             'Также можно воспользоваться программой, через которую можно войти с помощью Авторизации Яндекса\n\n'
                             'Скачать можно здесь: https://disk.yandex.ru/d/zBhcTwiut1kxJw\n\n'
                             'Примечания для программы (Windows):\n'
                             '- Для работы программы необходимо наличие Goole Chrome на вашем устройстве\n'
                             '- Версия программы не финальная и будет дорабатываться\n\n'
                             'Примечания для программы (Android):\n'
                             '- Версия Android должна быть не ниже 5.0\n'
                             '- Версия программы не финальная и будет дорабатываться'
               }

    class next_command_button(Button):
        def __init__(self, interaction: discord.Interaction):
            super().__init__(
                style=ButtonStyle.primary,
                emoji="➡️",
                disabled=data_servers[interaction.guild.name]['command_now'] + 1 >= len(command)
            )

        async def callback(self, interaction: discord.Interaction):
            global data_servers
            data_servers[interaction.guild.name]['command_now'] += 1
            self.view.clear_items()
            self.view.add_item(prev_command_button(interaction))
            self.view.add_item(next_command_button(interaction))
            await interaction.response.edit_message(
                content=f'Команда {data_servers[interaction.guild.name]["command_now"]+1} из {len(command)}',
                embed=Embed(
                    title='/authorize',
                    description=command['/authorize'],
                    color=0xf1ca0d
                ),
                view=self.view
            )

    class prev_command_button(Button):
        def __init__(self, interaction: discord.Interaction):
            super().__init__(
                style=ButtonStyle.primary,
                emoji="⬅️",
                disabled=data_servers[interaction.guild.name]['command_now']-1<0
            )

        async def callback(self, interaction: discord.Interaction):
            global data_servers
            data_servers[interaction.guild.name]['command_now'] -= 1
            self.view.clear_items()
            self.view.add_item(prev_command_button(interaction))
            self.view.add_item(next_command_button(interaction))
            await interaction.response.edit_message(
                content=f'Команда {data_servers[interaction.guild.name]["command_now"]+1} из {len(command)}',
                embed=Embed(
                    title='/play',
                    description=command['/play'],
                    color=0xf1ca0d
                ),
                view=self.view
            )

    view = View(timeout=1200.0)

    view.add_item(prev_command_button(interaction))
    view.add_item(next_command_button(interaction))

    embed = Embed(title='/play', description=command['/play'], color=0xf1ca0d)

    await interaction.response.send_message(
        content=f'Команда {data_servers[interaction.guild.name]["command_now"]+1} из {len(command)}',
        embed=embed,
        view=view
    )

@tree.command(name='about_me', description='🪪Обо мне')
async def about_me(interaction: discord.Interaction):
    await interaction.response.send_message(
        embed=Embed(
            title='Обо мне',
            description='Автором бота является пользователь 𝓽𝓲_𝓳𝓪𝓬𝓴\n\n'
                        'С открытым кодом можно ознакомиться тут:\n'
                        'https://github.com/SapTimofey/YandexMusic\n\n'
                        'С открытым кодом библиотеки yandex_music можно ознакомиться тут:\n'
                        'https://github.com/MarshalX/yandex-music-api\n\n'
                        'Версия бота: 0.8.2',
            color=0xf1ca0d
        ),
        ephemeral=True
    )

@client.event
async def on_ready():
    await tree.sync()
    await client.change_presence(activity=discord.Activity(name="/help", type=discord.ActivityType.playing))
    print("Ready!")

# Запускаем бота
client.run(YM_token)
