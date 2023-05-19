from yandex_music import Client, Track
from yandex_music.exceptions import NotFoundError

import discord
from discord import Embed, SelectOption, ButtonStyle, app_commands
from discord.ext import commands
from discord.ui import Button, View, Select

import asyncio
import os
import datetime
import requests
import textwrap
import re
from pytube import YouTube
# from pydub import AudioSegment
from googleapiclient.discovery import build
from random import random


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
settings_onyourwave = {}
user = os.environ.get('USERNAME')
output_path = f'C:\\Users\\{user}\\Music'  # Путь к папке, где будет сохранен аудиофайл
data_server = {'playlist': [],
               'repeat_flag': False,
               'queue_repeat': '',
               'index_play_now': 0,
               'task': None,
               'task_reserv': None,
               'task_check_voice_clients': None,
               'task_check_inactivity': None,
               'lyrics': None,
               'track_url': None,
               'cover_url': None,
               'track_id_play_now': None,
               'index_play_now': 0,
               'radio': None,
               'user_discord_radio': None,
               'radio_check': False,
               'stream_by_track_check': False,
               'last_activity_time': datetime.datetime.now(),
               'message_check': '',
               'command_now': 0
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
            # добавляем пару ключ-значение в глобальный словарь
            tokens[user_discord] = token


'''
Функции для обработки команд
'''
async def remove_last_playing_message(interaction: discord.Interaction):
    async for message in interaction.channel.history():
        if message.author == client.user and \
                (message.content.startswith('Текст') or
                 message.content.startswith('Вы не подключены') or
                 message.content.startswith('Ещё увидемся') or
                 message.content.startswith('Треки в очереди') or
                 message.content.startswith('Все покинули') or
                 message.content.startswith('Не удалось') or
                 (isinstance(message.embeds, list) and len(message.embeds) > 0)):
            try:
                await message.delete()
            except Exception:
                pass
        elif message.content.startswith('!play'):
            try:
                await message.delete()
            except Exception:
                pass
async def check_voice_clients(interaction: discord.Interaction):
    global data_servers, data_servers_log

    voice_client = interaction.guild.voice_client
    while True:
        # now = datetime.datetime.now()
        # for name_server in data_servers:
        #     data_servers_log[name_server][str(now).split('.')[0]] = data_servers[name_server]
        # Проверка наличия пользователей в голосовом канале
        if voice_client and not any(member != client.user for member in voice_client.channel.members):
            if voice_client.is_playing():
                voice_client.stop()
            await voice_client.disconnect()
            data_servers[interaction.guild.name]['task'].cancel()
            await remove_last_playing_message(interaction)

            now = datetime.datetime.now()
            current_time = now.time()
            filename = "C:\\Users\\tima\\Documents\\Log YM\\" + f"log-{now:%Y-%m-%d}.txt"
            # with open(filename, "a") as f:
            #     f.seek(0, 2)  # перемещаем курсор в конец файла
            #     f.write(f"Время: {current_time}\n"
            #             f"Сервер: {interaction.guild.name}\n"
            #             f"Бот отключился от канала: {voice_client.channel}\n"
            #             "Бот отключился по причине отсутствия пользователей\n")
            return
        await asyncio.sleep(1)
async def check_inactivity(interaction: discord.Interaction):
    global data_servers

    voice_client = interaction.guild.voice_client
    while True:
        # проверяем, прошло ли более 20 минут с момента последней активности бота
        if datetime.datetime.now() - data_servers[interaction.guild.name]['last_activity_time'] > datetime.timedelta(
                minutes=5) and not voice_client.is_playing() and voice_client:
            await voice_client.disconnect()
            await remove_last_playing_message(interaction)
            data_servers[interaction.guild.name]['task'].cancel()
            data_servers[interaction.guild.name]['task_check_voice_clients'].cancel()
            now = datetime.datetime.now()
            current_time = now.time()
            filename = "C:\\Users\\tima\\Documents\\Log YM\\" + f"log-{now:%Y-%m-%d}.txt"
            # with open(filename, "a") as f:
            #     f.seek(0, 2)  # перемещаем курсор в конец файла
            #     f.write(f"Время: {current_time}\n"
            #             f"Сервер: {ctx.guild.name}\n"
            #             f"Бот отключился от канала: {voice_client.channel}\n"
            #             "Бот отключился по причине бездействия\n")
            return
        # ждем 1 минуту и повторяем проверку
        await asyncio.sleep(1)
async def disconnect(interaction: discord.Interaction):
    global data_servers
    voice_client = interaction.guild.voice_client
    try:
        if voice_client.is_connected():
            if voice_client.is_playing():
                voice_client.stop()
            await voice_client.disconnect()

            data_servers[interaction.guild.name]['playlist'] = []
            data_servers[interaction.guild.name]['index_play_now'] = 0

            data_servers[interaction.guild.name]['task'].cancel()
            data_servers[interaction.guild.name]['task_check_inactivity'].cancel()
            data_servers[interaction.guild.name]['task_check_voice_clients'].cancel()

            await remove_last_playing_message(interaction)

            now = datetime.datetime.now()
            current_time = now.time()
            filename = "C:\\Users\\tima\\Documents\\Log YM\\" + f"log-{now:%Y-%m-%d}.txt"
            # with open(filename, "a") as f:
            #     f.seek(0, 2)  # перемещаем курсор в конец файла
            #     f.write(f"Время: {current_time}\n"
            #             f"Сервер: {interaction.guild.name}\n"
            #             f"Бота отключил: {str(interaction.user)}\n"
            #             f"Бот отключился от канала: {voice_client.channel}\n\n")
    except Exception:
        pass
async def check_audio_file(path):
    audio = AudioSegment.from_file(path)
    bitrate = audio.frame_rate * audio.channels * audio.sample_width * 8
    # print("bitrate = ", bitrate, "\nframe_rate = ", audio.frame_rate, "\nChannels = ", audio.channels, "\nsample_width = ", audio.sample_width)
    if (500 < bitrate < 512000):
        return True
    return False
async def add_queue(ctx, url_or_trackname_or_filepath):
    global index_queue

    playlist_ym = url_or_trackname_or_filepath.split(',')
    playlist_id = playlist_ym[0]

    client_ym = Client(tokens[user_discord]).init()

    if playlist_id.isdigit():
        try:
            playlist_new = client_ym.users_playlists(playlist_id)
        except Exception:
            await ctx.send(content=f"Не удалось найти плейлист с ID {playlist_id}")
            return

        if len(playlist_ym) == 1:
            for i in range(len(playlist_new.tracks)):
                playlists[ctx.guild.name].append(f"{user_discord}|{playlist_id},{i + 1}")
        else:
            if "-" in playlist_ym[1]:
                playlist_b_e = playlist_ym[1].split('-')

                if playlist_b_e[1] == '':
                    index_begin = int(playlist_b_e[0])
                    index_track = index_begin

                    if index_track > len(playlist_new.tracks):
                        await ctx.send(
                            f"\"{index_track}\" - номер трека превышает количество треков в плейлисте \"{len(playlist_new.tracks)}\"")
                        return
                    elif index_track <= 0:
                        await ctx.send(f"\"{index_track}\" - номер трека должен быть больше 0 🙃")
                        return

                    for i in range(index_begin - 1, len(playlist_new.tracks)):
                        playlists[ctx.guild.name].append(f"{user_discord}|{playlist_id},{i + 1}")
                    # check_next_index = index_queue + len(playlist_new.tracks) - index_begin
                elif playlist_b_e[0] == '':
                    index_end = int(playlist_b_e[1])

                    if index_end > len(playlist_new.tracks):
                        await ctx.send(
                            f"\"{index_end}\" - номер трека превышает количество треков в плейлисте \"{len(playlist_new.tracks)}\"")
                        return
                    elif index_end <= 0:
                        await ctx.send(f"\"{index_end}\" - номер трека должен быть больше 0 🙃")
                        return

                    for i in range(index_end):
                        playlists[ctx.guild.name].append(f"{user_discord}|{playlist_id},{i + 1}")
                    # check_next_index = index_queue + index_end
                else:
                    index_begin = int(playlist_b_e[0])
                    index_end = int(playlist_b_e[1])

                    if index_end > len(playlist_new.tracks):
                        await ctx.send(
                            f"\"{index_end}\" - номер трека превышает количество треков в плейлисте \"{len(playlist_new.tracks)}\"")
                        return
                    elif index_end <= 0:
                        await ctx.send(f"\"{index_end}\" - номер трека должен быть больше 0 🙃")
                        return
                    elif index_begin > index_end:
                        await ctx.send(
                            f"\"{index_end}\" - номер окончания плейлиста должен быть больше номера начала 🙃")
                        return

                    for i in range(index_begin - 1, index_end):
                        playlists[ctx.guild.name].append(f"{user_discord}|{playlist_id},{i + 1}")
                    # check_next_index = index_queue + index_end - index_begin
            else:
                index_track = int(playlist_ym[1])
                playlists[ctx.guild.name].append(f"{user_discord}|{playlist_id},{index_track}")
                # check_next_index = index_queue + 1
    else:  # если введено название плейлиста
        if "Мне нравится" in playlist_id:
            playlist_new = client_ym.users_likes_tracks()
            if len(playlist_ym) == 1:
                for i in range(len(playlist_new.tracks)):
                    playlists[ctx.guild.name].append(f"{user_discord}|Мне нравится,{i + 1}")

            else:
                if "-" in playlist_ym[1]:
                    playlist_b_e = playlist_ym[1].split('-')

                    if playlist_b_e[1] == '':
                        index_begin = int(playlist_b_e[0])
                        index_track = index_begin

                        if index_track > len(playlist_new.tracks):
                            await ctx.send(
                                f"\"{index_track}\" - номер трека превышает количество треков в плейлисте \"{len(playlist_new.tracks)}\"")
                            return
                        elif index_track <= 0:
                            await ctx.send(f"\"{index_track}\" - номер трека должен быть больше 0 🙃")
                            return

                        for i in range(index_begin - 1, len(playlist_new.tracks)):
                            playlists[ctx.guild.name].append(f"{user_discord}|Мне нравится,{i + 1}")

                    elif playlist_b_e[0] == '':
                        index_end = int(playlist_b_e[1])

                        if index_end > len(playlist_new.tracks):
                            await ctx.send(
                                f"\"{index_end}\" - номер трека превышает количество треков в плейлисте \"{len(playlist_new.tracks)}\"")
                            return
                        elif index_end <= 0:
                            await ctx.send(f"\"{index_end}\" - номер трека должен быть больше 0 🙃")
                            return

                        for i in range(index_end):
                            playlists[ctx.guild.name].append(f"{user_discord}|Мне нравится,{i + 1}")

                    else:
                        index_begin = int(playlist_b_e[0])
                        index_end = int(playlist_b_e[1])

                        if index_end > len(playlist_new.tracks):
                            await ctx.send(
                                f"\"{index_end}\" - номер трека превышает количество треков в плейлисте \"{len(playlist_new.tracks)}\"")
                            return
                        elif index_end <= 0:
                            await ctx.send(f"\"{index_end}\" - номер трека должен быть больше 0 🙃")
                            return
                        elif index_begin > index_end:
                            await ctx.send(
                                f"\"{index_end}\" - номер окончания плейлиста должен быть больше номера начала 🙃")
                            return

                        for i in range(index_begin - 1, index_end):
                            playlists[ctx.guild.name].append(f"{user_discord}|Мне нравится,{i + 1}")

                else:
                    index_track = int(playlist_ym[1])
                    playlists[ctx.guild.name].append(f"{user_discord}|Мне нравится,{index_track}")
        else:
            playlists_name = client_ym.users_playlists_list()

            for name in playlists_name:
                if url_or_trackname_or_filepath in name.title:
                    playlist_id = name.playlist_id.split(':')[1]
            if not playlist_id.isdigit():
                with open("C:\\Users\\tima\\Pictures\\Gif\\spin-1.gif", 'rb') as f:
                    file = discord.File(f)
                await ctx.send(content=f"\"{playlist_id}\" - не удалось найти плейлист с таким названием", file=file)
                return
            playlist_new = client_ym.users_playlists(int(playlist_id))
            if len(playlist_ym) == 1:
                for i in range(len(playlist_new.tracks)):
                    playlists[ctx.guild.name].append(f"{user_discord}|{playlist_new.title},{i + 1}")
            else:
                if "-" in playlist_ym[1]:
                    playlist_b_e = playlist_ym[1].split('-')

                    if playlist_b_e[1] == '':
                        index_begin = int(playlist_b_e[0])
                        index_track = index_begin

                        if index_track > len(playlist_new.tracks):
                            await ctx.send(
                                f"\"{index_track}\" - номер трека превышает количество треков в плейлисте \"{len(playlist_new.tracks)}\"")
                            return
                        elif index_track <= 0:
                            await ctx.send(f"\"{index_track}\" - номер трека должен быть больше 0 🙃")
                            return

                        for i in range(index_begin - 1, len(playlist_new.tracks)):
                            playlists[ctx.guild.name].append(f"{user_discord}|{playlist_new.title},{i + 1}")

                    elif playlist_b_e[0] == '':
                        index_end = int(playlist_b_e[1])

                        if index_end > len(playlist_new.tracks):
                            await ctx.send(
                                f"\"{index_end}\" - номер трека превышает количество треков в плейлисте \"{len(playlist_new.tracks)}\"")
                            return
                        elif index_end <= 0:
                            await ctx.send(f"\"{index_end}\" - номер трека должен быть больше 0 🙃")
                            return

                        for i in range(index_end):
                            playlists[ctx.guild.name].append(f"{user_discord}|{playlist_new.title},{i + 1}")
                    else:
                        index_begin = int(playlist_b_e[0])
                        index_end = int(playlist_b_e[1])

                        if index_end > len(playlist_new.tracks):
                            await ctx.send(
                                f"\"{index_end}\" - номер трека превышает количество треков в плейлисте \"{len(playlist_new.tracks)}\"")
                            return
                        elif index_end <= 0:
                            await ctx.send(f"\"{index_end}\" - номер трека должен быть больше 0 🙃")
                            return
                        elif index_begin > index_end:
                            await ctx.send(
                                f"\"{index_end}\" - номер окончания плейлиста должен быть больше номера начала 🙃")
                            return

                        for i in range(index_begin - 1, index_end):
                            playlists[ctx.guild.name].append(f"{user_discord}|{playlist_new.title},{i + 1}")

                else:
                    index_track = int(playlist_ym[1])
                    playlists[ctx.guild.name].append(f"{user_discord}|{playlist_new.title},{i + 1}")
async def play_YouTube(url_or_trackname_or_filepath, user_discord, interaction: discord.Interaction):
    global data_servers

    api_key = "AIzaSyB_OXBg1a2u4bnMVhh6hPZ1nxA398AfhdU"

    data_servers[interaction.guild.name]['track_url'] = url_or_trackname_or_filepath
    data_servers[interaction.guild.name]['track_id_play_now'] = None
    data_servers[interaction.guild.name]['radio_check'] = False
    data_servers[interaction.guild.name]['stream_by_track_check'] = False

    # Извлеките идентификатор видео из ссылки
    video_id = re.findall(r'v=(\w+)', url_or_trackname_or_filepath)[0]

    # Создайте объект YouTube API
    youtube = build('youtube', 'v3', developerKey=api_key)

    # Получите информацию о видео
    video_info = youtube.videos().list(part='snippet', id=video_id).execute()

    # Извлеките название видео из полученных данных
    play_now = f"Название видео: {video_info['items'][0]['snippet']['title']}\nАвтор: {video_info['items'][0]['snippet']['channelTitle']}"

    # Извлеките URL превью из полученных данных
    data_servers[interaction.guild.name]['cover_url'] = video_info['items'][0]['snippet']['thumbnails']['high']['url']

    audio_file_path = f'{output_path}\\YT_{str(user_discord)}.mp3'

    yt = YouTube(url_or_trackname_or_filepath)

    # Выбираем аудио поток с максимальным битрейтом
    audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()

    # Скачиваем аудио
    audio_stream.download(output_path=output_path, filename=f'YT_{str(user_discord)}.mp3')

    return [play_now, audio_file_path]
async def play_Yandex_Music_url(interaction: discord.Interaction, url_or_trackname_or_filepath, user_discord):
    global data_servers

    client_ym = Client(tokens[user_discord]).init()

    numbers = [int(s) for s in url_or_trackname_or_filepath.split('/') if s.isdigit()]
    if len(numbers) == 1:
        track_id = numbers[0]
        track = client_ym.tracks(track_id)[0]
    else:
        album_id = numbers[0]
        track_id = numbers[1]
        track = client_ym.tracks(f'{track_id}:{album_id}')[0]

    track.download(f'C:\\Users\\{user}\\Music\\YM_{user_discord}.mp3')
    data_servers[interaction.guild.name]['track_id_play_now'] = track.id

    try:
        data_servers[interaction.guild.name]['lyrics'] = track.get_lyrics().fetch_lyrics()
    except Exception:
        data_servers[interaction.guild.name]['lyrics'] = None

    base_url = 'https://music.yandex.ru/track/'
    data_servers[interaction.guild.name]['track_url'] = base_url + str(track_id)

    if track.cover_uri:
        data_servers[interaction.guild.name]['cover_url'] = f"https://{track.cover_uri.replace('%%', '200x200')}"
    else:
        data_servers[interaction.guild.name]['cover_url'] = None

    artists = track.artists
    if not artists:
        artist_all = ""
    else:
        artist_names = [artist.name for artist in artists]  # получаем список имен артистов
        artist_all = ", ".join(artist_names)  # объединяем их через запятую

    if data_servers[interaction.guild.name]['radio_check']:
        play_now = f"\nРадио: Моя волна\nТрек: {track.title}\nИсполнители: {artist_all}\n"
    elif data_servers[interaction.guild.name]['stream_by_track_check']:
        play_now = f"\nРадио: Моя волна по треку\nТрек: {track.title}\nИсполнители: {artist_all}\n"
    else:
        play_now = f"\nТрек: {track.title}\nИсполнители: {artist_all}\n"
    audio_file_path = f'{output_path}\\YM_{user_discord}.mp3'

    # if not await check_audio_file(audio_file_path):
    #     # Изменяем параметры трека
    #     audio = AudioSegment.from_file(audio_file_path)
    #     audio = audio.set_frame_rate(96000).set_channels(2)
    #     audio.export(audio_file_path, format="mp3")

    return [play_now, audio_file_path]
async def play_Yandex_Music_playlist(interaction: discord.Interaction, url_or_trackname_or_filepath, user_discord):
    global data_servers
    voice_client = interaction.guild.voice_client

    playlist_ym = url_or_trackname_or_filepath.split(',')
    playlist_id = playlist_ym[0]

    client_ym = Client(tokens[user_discord]).init()

    if playlist_id == "3":
        playlist_new = client_ym.users_likes_tracks()
    else:
        try:
            playlist_new = client_ym.users_playlists(playlist_id)
        except Exception:
            p = await send_search_request(interaction, url_or_trackname_or_filepath, user_discord)
            if not p:
                return False

            play_now = p[0]
            audio_file_path = p[1]
            return [play_now, audio_file_path]

    if len(playlist_ym) == 1:
        for i in range(len(playlist_new.tracks)):
            data_servers[interaction.guild.name]['playlist'].append(f"{user_discord}|{playlist_id},{i + 1}")

        index_track = 1
        track_short = playlist_new.tracks[index_track - 1]
    else:
        if "-" in playlist_ym[1]:
            playlist_b_e = playlist_ym[1].split('-')

            if playlist_b_e[1] == '':
                index_begin = int(playlist_b_e[0])
                index_track = index_begin

                if index_track > len(playlist_new.tracks):
                    await interaction.response.send_message(
                        f"\"{index_track}\" - номер трека превышает количество треков в плейлисте \"{len(playlist_new.tracks)}\"",
                        ephemeral=True)
                    return False
                elif index_track <= 0:
                    await interaction.response.send_message(f"\"{index_track}\" - номер трека должен быть больше 0 🙃",
                                                            ephemeral=True)
                    return False

                for i in range(index_begin - 1, len(playlist_new.tracks)):
                    data_servers[interaction.guild.name]['playlist'].append(f"{user_discord}|{playlist_id},{i + 1}")

                track_short = playlist_new.tracks[index_track - 1]
            elif playlist_b_e[0] == '':
                index_end = int(playlist_b_e[1])

                if index_end > len(playlist_new.tracks):
                    await interaction.response.send_message(
                        f"\"{index_end}\" - номер трека превышает количество треков в плейлисте \"{len(playlist_new.tracks)}\"",
                        ephemeral=True)
                    return False
                elif index_end <= 0:
                    await interaction.response.send_message(f"\"{index_end}\" - номер трека должен быть больше 0 🙃",
                                                            ephemeral=True)
                    return False

                for i in range(index_end):
                    data_servers[interaction.guild.name]['playlist'].append(f"{user_discord}|{playlist_id},{i + 1}")

                index_track = 1
                track_short = playlist_new.tracks[index_track - 1]
            else:
                index_begin = int(playlist_b_e[0])
                index_end = int(playlist_b_e[1])

                if index_end > len(playlist_new.tracks):
                    await interaction.response.send_message(
                        f"\"{index_end}\" - номер трека превышает количество треков в плейлисте \"{len(playlist_new.tracks)}\"",
                        ephemeral=True)
                    return False
                elif index_end <= 0:
                    await interaction.response.send_message(f"\"{index_end}\" - номер трека должен быть больше 0 🙃",
                                                            ephemeral=True)
                    return False
                elif index_begin > index_end:
                    await interaction.response.send_message(
                        f"\"{index_end}\" - номер окончания плейлиста должен быть больше номера начала 🙃",
                        ephemeral=True)
                    return False

                for i in range(index_begin - 1, index_end):
                    data_servers[interaction.guild.name]['playlist'].append(f"{user_discord}|{playlist_id},{i + 1}")

                index_track = index_begin
                track_short = playlist_new.tracks[index_track - 1]
        else:
            index_track = int(playlist_ym[1])
            if f"{user_discord}|{playlist_id},{index_track}" not in data_servers[interaction.guild.name]['playlist']:
                data_servers[interaction.guild.name]['playlist'].append(f"{user_discord}|{playlist_id},{index_track}")
            track_short = playlist_new.tracks[index_track - 1]

    track = client_ym.tracks(track_short.track_id)[0]

    if not track.available:
        await interaction.response.send_message(f"{index_track} - {track.title} - трек отозван правообладателем",
                                                ephemeral=True)
        if data_servers[interaction.guild.name]['index_play_now'] + 1 < len(
                data_servers[interaction.guild.name]['playlist']):
            voice_client.stop()
            data_servers[interaction.guild.name]['index_play_now'] += 1
            try:
                data_servers[interaction.guild.name]['task'].cancel()
            except Exception as e:
                await interaction.response.send_message(f"Произошла ошибка: {e}", ephemeral=True)
                return False
            data_servers[interaction.guild.name]['task'] = asyncio.create_task(play(interaction, data_servers[
                interaction.guild.name]['playlist'][data_servers[interaction.guild.name]['index_play_now']]))
            data_servers[interaction.guild.name]['task_reserv'] = data_servers[interaction.guild.name]['task']
            return False
        else:
            await interaction.channel.send("Треки в очереди закончились")
            return False
    artists = track.artists
    if not artists:
        artist_all = ""
    else:
        artist_names = [artist.name for artist in artists]  # получаем список имен артистов
        artist_all = ", ".join(artist_names)  # объединяем их через запятую
    if playlist_id == "3":
        play_now = f"\nПлейлист: Мне нравится\nТрек: {track.title}\nИсполнители: {artist_all}\nНомер трека: {index_track}\\{len(playlist_new.tracks)}"
    else:
        play_now = f"\nПлейлист: {playlist_new.title}\nТрек: {track.title}\nИсполнители: {artist_all}\nНомер трека: {index_track}\\{len(playlist_new.tracks)}"

    track.download(f'C:\\Users\\{user}\\Music\\YM_{user_discord}.mp3')
    try:
        data_servers[interaction.guild.name]['lyrics'] = track.get_lyrics().fetch_lyrics()
    except Exception:
        data_servers[interaction.guild.name]['lyrics'] = None

    if track.desired_visibility:
        data_servers[interaction.guild.name]['track_url'] = None
        data_servers[interaction.guild.name]['track_id_play_now'] = None
    else:
        data_servers[interaction.guild.name]['track_id_play_now'] = track.id
        base_url = 'https://music.yandex.ru/track/'
        if ":" in track_short.track_id:
            data_servers[interaction.guild.name]['track_url'] = base_url + str(track_short.track_id).split(":")[0]
        else:
            data_servers[interaction.guild.name]['track_url'] = base_url + str(track_short.track_id)

    if track.cover_uri:
        data_servers[interaction.guild.name]['cover_url'] = f"https://{track.cover_uri.replace('%%', '200x200')}"
    else:
        data_servers[interaction.guild.name]['cover_url'] = None

    audio_file_path = f'{output_path}\\YM_{user_discord}.mp3'

    # if not await check_audio_file(audio_file_path):
    #     # Изменяем параметры трека
    #     audio = AudioSegment.from_file(audio_file_path)
    #     audio = audio.set_frame_rate(48000).set_channels(2)
    #     audio.export(audio_file_path, format="mp3")

    return [play_now, audio_file_path]
async def send_search_request(interaction: discord.Interaction, query, user_discord):
    global data_servers
    voice_client = interaction.guild.voice_client

    client_ym = Client(tokens[user_discord]).init()

    search_result = client_ym.search(query.replace('"', ''))

    type_to_name = {
        'track': 'трек',
        'artist': 'исполнитель',
        'album': 'альбом',
        'playlist': 'плейлист',
        'video': 'видео',
        'user': 'пользователь',
        'podcast': 'подкаст',
        'podcast_episode': 'эпизод подкаста',
    }

    type_ = search_result.best.type
    best = search_result.best.result
    if type_ in ['track', 'podcast_episode']:
        track = client_ym.tracks(best.track_id)[0]
        data_servers[interaction.guild.name]['track_id_play_now'] = track.id
        artists = track.artists
        if not artists:
            artist_all = ""
        else:
            artist_names = [artist.name for artist in artists]  # получаем список имен артистов
            artist_all = ", ".join(artist_names)  # объединяем их через запятую
        play_now = f"\nТрек: {track.title}\nИсполнители: {artist_all}"

        track.download(f'{output_path}\\YM_{user_discord}.mp3')

        try:
            data_servers[interaction.guild.name]['lyrics'] = track.get_lyrics().fetch_lyrics()
        except Exception:
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

        audio_file_path = f'{output_path}\\YM_{user_discord}.mp3'

        # if not await check_audio_file(audio_file_path):
        #     # Изменяем параметры трека
        #     audio = AudioSegment.from_file(audio_file_path)
        #     audio = audio.set_frame_rate(96000).set_channels(2)
        #     audio.export(audio_file_path, format="mp3")

        return [play_now, audio_file_path]
    else:
        data_servers[interaction.guild.name]['track_id_play_now'] = None
        await interaction.response.send_message("Не удалось найти трек с таким названием", ephemeral=True)
        return False
async def play_radio(interaction: discord.Interaction, user_discord=None, first: bool = False, station_id: str = None, station_from: str = None):
    global data_servers
    if first:
        client_ym = Client(tokens[str(user_discord)]).init()
        data_servers[interaction.guild.name]['radio'] = Radio(client_ym)
        data_servers[interaction.guild.name]['user_discord_radio'] = user_discord
        for rotor in client_ym.rotor_stations_dashboard().stations:
            if rotor.station['name'] == "Моя волна":
                station = rotor.station
        _station_id = station_id or f'{station.id.type}:{station.id.tag}'
        _station_from = station_from or station.id_for_from
        track = data_servers[interaction.guild.name]['radio'].start_radio(_station_id, _station_from)
    else:
        track = data_servers[interaction.guild.name]['radio'].play_next()

    data_servers[interaction.guild.name]['track_id_play_now'] = track.id
    base_url = 'https://music.yandex.ru/track/'
    if ":" in track.track_id:
        data_servers[interaction.guild.name]['track_url'] = base_url + str(track.track_id).split(":")[0]
    else:
        data_servers[interaction.guild.name]['track_url'] = base_url + str(track.track_id)
    data_servers[interaction.guild.name]['task'] = asyncio.create_task(
        play(interaction, data_servers[interaction.guild.name]['track_url']))
    data_servers[interaction.guild.name]['task_reserv'] = data_servers[interaction.guild.name]['task']


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
        if self.style == ButtonStyle.green:
            self.style = ButtonStyle.primary  # изменяем стиль кнопки на primary
            data_servers[interaction.guild.name]['repeat_flag'] = False  # устанавливаем repeat_flag в False
        else:
            self.style = ButtonStyle.green  # изменяем стиль кнопки на зеленый
            data_servers[interaction.guild.name]['repeat_flag'] = True  # устанавливаем repeat_flag в True
        await interaction.response.edit_message(view=self.view)  # обновляем стиль кнопки
class next_button(Button):
    def __init__(self, interaction: discord.Interaction):
        super().__init__(style=ButtonStyle.primary,
                         label="К следующему",
                         emoji="⏭️",
                         row=1,
                         disabled=data_servers[interaction.guild.name]['index_play_now'] + 1 >= len(
                             data_servers[interaction.guild.name]['playlist']) and not
                                  data_servers[interaction.guild.name]['radio_check'] and not
                                  data_servers[interaction.guild.name]['stream_by_track_check'])

    async def callback(self, interaction: discord.Interaction):
        global data_servers
        voice_client = interaction.guild.voice_client
        voice_client.stop()
        if data_servers[interaction.guild.name]['radio_check'] or data_servers[interaction.guild.name][
            'stream_by_track_check']:
            data_servers[interaction.guild.name]['task'].cancel()
            await play_radio(interaction=interaction)
        else:
            data_servers[interaction.guild.name]['index_play_now'] += 1
            try:
                data_servers[interaction.guild.name]['task'].cancel()
            except Exception as e:
                await interaction.response.send_message(f"Произошла ошибка: {e}", ephemeral=True)
            data_servers[interaction.guild.name]['task'] = asyncio.create_task(play(interaction, data_servers[
                interaction.guild.name]['playlist'][data_servers[interaction.guild.name]['index_play_now']]))
            data_servers[interaction.guild.name]['task_reserv'] = data_servers[interaction.guild.name]['task']
class prev_button(Button):
    def __init__(self, interaction: discord.Interaction):
        super().__init__(style=ButtonStyle.primary,
                         label="К предыдущему",
                         emoji="⏮️",
                         row=1,
                         disabled=data_servers[interaction.guild.name]['index_play_now'] - 1 < 0 or
                                  data_servers[interaction.guild.name]['radio_check'] or
                                  data_servers[interaction.guild.name]['stream_by_track_check'])

    async def callback(self, interaction: discord.Interaction):
        global data_servers
        voice_client = interaction.guild.voice_client
        voice_client.stop()
        data_servers[interaction.guild.name]['index_play_now'] -= 1
        try:
            data_servers[interaction.guild.name]['task'].cancel()
        except Exception as e:
            await interaction.response.send_message(f"Произошла ошибка: {e}", ephemeral=True)
        data_servers[interaction.guild.name]['task'] = asyncio.create_task(play(interaction,
                                                                                data_servers[interaction.guild.name][
                                                                                    'playlist'][data_servers[
                                                                                    interaction.guild.name][
                                                                                    'index_play_now']]))
        data_servers[interaction.guild.name]['task_reserv'] = data_servers[interaction.guild.name]['task']
class pause_resume_button(Button):
    def __init__(self):
        super().__init__(style=ButtonStyle.primary, label="Пауза/Продолжить", emoji="⏯️", row=1)

    async def callback(self, interaction):
        voice_client = interaction.guild.voice_client  # use the attribute
        if self.style == ButtonStyle.green:
            self.style = ButtonStyle.primary  # изменяем стиль кнопки на primary
            voice_client.resume()
        else:
            self.style = ButtonStyle.green  # изменяем стиль кнопки на зеленый
            voice_client.pause()
        await interaction.response.edit_message(view=self.view)  # обновляем стиль кнопки
class disconnect_button(Button):
    def __init__(self):
        super().__init__(style=ButtonStyle.red, label="Отключить", emoji="📛", row=3)

    async def callback(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client  # use the attribute
        if voice_client.is_playing():
            voice_client.stop()

        await disconnect(interaction)
class lyrics_button(Button):
    def __init__(self, interaction: discord.Interaction):
        super().__init__(style=ButtonStyle.primary,
                         label="Текст",
                         emoji="🗒️",
                         row=2,
                         disabled=data_servers[interaction.guild.name]['lyrics'] is None)

    async def callback(self, interaction: discord.Interaction):
        global data_servers
        if self.style == ButtonStyle.green:
            self.style = ButtonStyle.primary  # изменяем стиль кнопки на primary
            async for message in interaction.channel.history():
                if message.author == client.user and message.content.startswith('Текст'):
                    await message.delete()
        else:
            self.style = ButtonStyle.green  # изменяем стиль кнопки на зеленый
            if len(data_servers[interaction.guild.name]['lyrics']) > 2000:
                # Split the lyrics into two parts using textwrap
                parts = textwrap.wrap(data_servers[interaction.guild.name]['lyrics'], width=1800,
                                      break_long_words=False, replace_whitespace=False)
                await interaction.channel.send(f"Текст трека (часть 1):\n{parts[0]}")
                await interaction.channel.send(f"Текст трека (часть 2):\n{parts[1]}")
            else:
                await interaction.channel.send(f"Текст трека:\n{data_servers[interaction.guild.name]['lyrics']}")
        await interaction.response.edit_message(view=self.view)  # обновляем стиль кнопки
class track_url_button(Button):
    def __init__(self, interaction: discord.Interaction):
        if data_servers[interaction.guild.name]['track_url']:
            super().__init__(style=ButtonStyle.url,
                             label="Ссылка",
                             emoji="🌐",
                             url=data_servers[interaction.guild.name]['track_url'],
                             row=2)
        else:
            super().__init__(style=ButtonStyle.grey,
                             label="Ссылка",
                             emoji="🌐",
                             disabled=True,
                             row=2)
class stream_by_track_button(Button):
    def __init__(self, interaction: discord.Interaction):
        super().__init__(style=ButtonStyle.primary,
                         label="Моя волна по треку",
                         emoji="💫",
                         row=2,
                         disabled=not data_servers[interaction.guild.name]['track_id_play_now'])

    async def callback(self, interaction: discord.Interaction):
        global data_servers
        if str(interaction.user) not in tokens:
            await interaction.response.send_message(
                f"Пользователь {str(interaction.user)} не вошёл в аккаунт Яндекс.Музыки. Для входа воспользуйтесь командой !authorize",
                ephemeral=True)
            return
        data_servers[interaction.guild.name]['radio_check'] = False
        data_servers[interaction.guild.name]['stream_by_track_check'] = True
        voice_client = interaction.guild.voice_client
        data_servers[interaction.guild.name]['playlist'] = []
        data_servers[interaction.guild.name]['index_play_now'] = 0
        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()
            data_servers[interaction.guild.name]['task'].cancel()
        await play_radio(interaction=interaction,
                         user_discord=interaction.user,
                         first=True,
                         station_id='track:' + data_servers[interaction.guild.name]['track_id_play_now'],
                         station_from='track')
class PlaylistSelect(Select):
    def __init__(self, interaction: discord.Interaction):
        options = []
        user_discord = str(interaction.user)
        client_ym = Client(tokens[user_discord]).init()

        options.append(SelectOption(label="Моя волна", value="1", description="Радио"))
        options.append(SelectOption(label="Мне нравится", value="3",
                                    description=f"Количество треков: {len(client_ym.users_likes_tracks())}"))

        # Формируем сообщение со списком плейлистов и их ID
        playlists_ym = client_ym.users_playlists_list()
        for playlist_ym in playlists_ym:
            playlist_ym_id = playlist_ym.playlist_id.split(':')[1]
            options.append(SelectOption(label=str(playlist_ym.title), value=str(playlist_ym_id),
                                        description=f"Количество треков: {len(client_ym.users_playlists(int(playlist_ym_id)).tracks)}"))

        super().__init__(placeholder='Выберете плейлист...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        global data_servers
        voice_client = interaction.guild.voice_client
        data_servers[interaction.guild.name]['playlist'] = []
        data_servers[interaction.guild.name]['index_play_now'] = 0
        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()
            data_servers[interaction.guild.name]['task_reserv'].cancel()
            data_servers[interaction.guild.name]['task'].cancel()
        if self.values[0] == "1":
            data_servers[interaction.guild.name]['radio_check'] = True
            data_servers[interaction.guild.name]['stream_by_track_check'] = False
            return await play_radio(interaction=interaction, user_discord=interaction.user, first=True)
        else:
            data_servers[interaction.guild.name]['radio_check'] = False
            data_servers[interaction.guild.name]['stream_by_track_check'] = False
            data_servers[interaction.guild.name]['task'] = asyncio.create_task(play(interaction, self.values[0]))
            data_servers[interaction.guild.name]['task_reserv'] = data_servers[interaction.guild.name]['task']
class onyourwave_setting_button(Button):
    def __init__(self, interaction: discord.Interaction):
        super().__init__(style=ButtonStyle.primary,
                         label="Настроить волну",
                         emoji="⚙️",
                         row=3,
                         disabled=not data_servers[interaction.guild.name]['radio_check'])

    async def callback(self, interaction: discord.Interaction):
        view = View(timeout=1200.0)
        if interaction.user == data_servers[interaction.guild.name]['user_discord_radio']:
            view.add_item(onyourwave_setting_diversity())
            view.add_item(onyourwave_setting_mood_energy())
            view.add_item(onyourwave_setting_language())

            await interaction.response.send_message(view=view, ephemeral=True)
        else:
            await interaction.response.send_message('Настраивать волну может только тот, кто её запустил',
                                                    ephemeral=True)
class onyourwave_setting_diversity(Select):
    def __init__(self):
        super().__init__(placeholder=f'По характеру...', min_values=1, max_values=1, options=[
            SelectOption(label='Любимое', value='favorite', emoji='💖'),
            SelectOption(label='Незнакомое', value='discover', emoji='✨'),
            SelectOption(label='Популярное', value='popular', emoji='⚡'),
            SelectOption(label='По умолчанию', value='default', emoji='♦️')
        ])

    async def callback(self, interaction: discord.Interaction):
        global settings_onyourwave, data_servers

        settings_onyourwave[str(interaction.user)]['diversity'] = self.values[0]

        client_ym = Client(tokens[str(interaction.user)]).init()

        client_ym.rotor_station_settings2(
            station='user:onyourwave',
            mood_energy=settings_onyourwave[str(interaction.user)]['mood_energy'],
            diversity=settings_onyourwave[str(interaction.user)]['diversity'],
            language=settings_onyourwave[str(interaction.user)]['language']
        )
        voice_client = interaction.guild.voice_client
        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()
            data_servers[interaction.guild.name]['task_reserv'].cancel()
            data_servers[interaction.guild.name]['task'].cancel()
        await play_radio(interaction=interaction, user_discord=interaction.user, first=True)
class onyourwave_setting_mood_energy(Select):
    def __init__(self):
        super().__init__(placeholder=f'Под настроение...', min_values=1, max_values=1, options=[
            SelectOption(label='Бодрое', value='active', emoji='🟠'),
            SelectOption(label='Весёлое', value='fun', emoji='🟢'),
            SelectOption(label='Спокойное', value='calm', emoji='🔵'),
            SelectOption(label='Грустное', value='sad', emoji='🟣'),
            SelectOption(label='Любое', value='all', emoji='🔘')
        ])

    async def callback(self, interaction: discord.Interaction):
        global settings_onyourwave, data_servers

        settings_onyourwave[str(interaction.user)]['mood_energy'] = self.values[0]

        client_ym = Client(tokens[str(interaction.user)]).init()

        client_ym.rotor_station_settings2(
            station='user:onyourwave',
            mood_energy=settings_onyourwave[str(interaction.user)]['mood_energy'],
            diversity=settings_onyourwave[str(interaction.user)]['diversity'],
            language=settings_onyourwave[str(interaction.user)]['language']
        )
        voice_client = interaction.guild.voice_client
        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()
            data_servers[interaction.guild.name]['task_reserv'].cancel()
            data_servers[interaction.guild.name]['task'].cancel()
        await play_radio(interaction=interaction, user_discord=interaction.user, first=True)
class onyourwave_setting_language(Select):
    def __init__(self):
        super().__init__(placeholder=f'По языку...', min_values=1, max_values=1, options=[
            SelectOption(label='Русский', value='russian'),
            SelectOption(label='Иностранный', value='not-russian'),
            SelectOption(label='Без слов', value='without-words'),
            SelectOption(label='Любой', value='any')
        ])

    async def callback(self, interaction: discord.Interaction):
        global settings_onyourwave, data_servers

        settings_onyourwave[str(interaction.user)]['language'] = self.values[0]

        client_ym = Client(tokens[str(interaction.user)]).init()

        client_ym.rotor_station_settings2(
            station='user:onyourwave',
            mood_energy=settings_onyourwave[str(interaction.user)]['mood_energy'],
            diversity=settings_onyourwave[str(interaction.user)]['diversity'],
            language=settings_onyourwave[str(interaction.user)]['language']
        )
        voice_client = interaction.guild.voice_client
        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()
            data_servers[interaction.guild.name]['task_reserv'].cancel()
            data_servers[interaction.guild.name]['task'].cancel()
        await play_radio(interaction=interaction, user_discord=interaction.user, first=True)


'''
Функции для реализации команд
'''
@tree.command(name='play', description="🎧Воспроизвести трек. При вызове без аргумента - воспроизвести плейлист из списка")
@app_commands.describe(url_or_trackname='Вы можете указать: ссылку на трек из Яндекс.Музыки или YouTube, название трека')
async def start_play(interaction: discord.Interaction, url_or_trackname: str = None):
    global data_servers, settings_onyourwave

    if interaction.guild.name not in data_servers:
        data_servers[interaction.guild.name] = data_server

    if str(interaction.user) not in settings_onyourwave:
        settings_onyourwave[str(interaction.user)] = {'mood_energy': 'all', 'diversity': 'default', 'language': 'any'}

    author_voice_state = interaction.user.voice
    if author_voice_state is None:
        await interaction.response.send_message("Вы не подключены к голосовому каналу.", ephemeral=True)
        return

    # Проверяем, подключен ли бот к голосовому каналу
    voice_client = interaction.guild.voice_client

    if not voice_client:
        voice_channel = interaction.user.voice.channel
        await voice_channel.connect()
        voice_client = interaction.guild.voice_client

    data_servers[interaction.guild.name]['task'] = asyncio.create_task(play(interaction, url_or_trackname))
    data_servers[interaction.guild.name]['task_check_inactivity'] = asyncio.create_task(check_inactivity(interaction))
    data_servers[interaction.guild.name]['task_check_voice_clients'] = asyncio.create_task(
        check_voice_clients(interaction))
async def play(interaction: discord.Interaction, url_or_trackname_or_filepath: str = None, flag_repeat: bool = True):
    try:
        global output_path, tokens, data_servers

        voice_client = interaction.guild.voice_client

        if not url_or_trackname_or_filepath:  # если не передан url
            view = View()
            view.add_item(PlaylistSelect(interaction))
            await interaction.response.send_message(view=view, ephemeral=True)
            return
        else:

            # if len(data_servers[interaction.guild.name]['playlist']) == 0 and not data_servers[interaction.guild.name]['radio_check']
            #
            # while data_servers[interaction.guild.name]['index_play_now'] < len(data_servers[interaction.guild.name]['playlist']):
            #
            #     url_or_trackname_or_filepath = data_servers[interaction.guild.name]['playlist'][data_servers[interaction.guild.name]['index_play_now']]

            if "youtube.com" in url_or_trackname_or_filepath:
                if "|" not in url_or_trackname_or_filepath:
                    user_discord = interaction.user
                else:
                    p = url_or_trackname_or_filepath.split('|')
                    name_and_discriminator = p[0]  # получаем имя и дискриминатор в формате "Имя#Дискриминатор"

                    user_discord = discord.utils.get(interaction.guild.members,
                                                     name=name_and_discriminator.split("#")[0],
                                                     discriminator=name_and_discriminator.split("#")[
                                                         1])  # ищем участника с заданным именем и дискриминатором
                    url_or_trackname_or_filepath = p[1]

                # Проверяем, играет ли бот уже какую-то музыку
                if voice_client.is_playing() or voice_client.is_paused():
                    # playlists[ctx.guild.name].append(f"{user_discord}-{url_or_trackname_or_filepath}")
                    # await ctx.send(f"Трек {url_or_trackname_or_filepath} добавлен в очередь")
                    # return
                    voice_client.stop()
                    data_servers[interaction.guild.name]['task_reserv'].cancel()

                p = await play_YouTube(url_or_trackname_or_filepath, user_discord, interaction)

                play_now = p[0]
                audio_file_path = p[1]

            elif "music.yandex.ru" in url_or_trackname_or_filepath:

                if "|" not in url_or_trackname_or_filepath:
                    if data_servers[interaction.guild.name]['user_discord_radio']:
                        user_discord = data_servers[interaction.guild.name]['user_discord_radio']
                    else:
                        user_discord = interaction.user
                else:
                    p = url_or_trackname_or_filepath.split('|')
                    name_and_discriminator = p[0]  # получаем имя и дискриминатор в формате "Имя#Дискриминатор"

                    user_discord = discord.utils.get(interaction.guild.members,
                                                     name=name_and_discriminator.split("#")[0],
                                                     discriminator=name_and_discriminator.split("#")[
                                                         1])  # ищем участника с заданным именем и дискриминатором
                    url_or_trackname_or_filepath = p[1]

                if not str(user_discord) in tokens:
                    await interaction.response.send_message(
                        f"Пользователь {str(user_discord)} не вошёл в аккаунт Яндекс.Музыки. Для входа воспользуйтесь командой !authorize",
                        ephemeral=True)
                    return

                p = await play_Yandex_Music_url(interaction, url_or_trackname_or_filepath, str(user_discord))
                play_now = p[0]
                audio_file_path = p[1]

            elif ":\\" in url_or_trackname_or_filepath:
                play_now = url_or_trackname_or_filepath
                audio_file_path = url_or_trackname_or_filepath

                # Проверяем, что файл существует
                if not os.path.isfile(audio_file_path):
                    await ctx.send(f"Файл `{url_or_trackname_or_filepath}` не найден.")
                    return

                # Проверяем, играет ли бот уже какую-то музыку
                if voice_client.is_playing():
                    playlists[ctx.guild.name].append(url_or_trackname_or_filepath)
                    await ctx.send(f"Трек \"{url_or_trackname_or_filepath}\" добавлен в очередь")
                    return

                # if not await check_audio_file(audio_file_path):
                #     # Изменяем параметры трека
                #     audio = AudioSegment.from_file(audio_file_path)
                #     audio = audio.set_frame_rate(96000).set_channels(2)
                #     new_path = f'{output_path}\\audio_fixed.mp3'
                #     audio.export(new_path, format="mp3")
                #     audio_file_path = new_path

            elif ".mp3" in url_or_trackname_or_filepath or ".flac" in url_or_trackname_or_filepath:
                if "@" in url_or_trackname_or_filepath:
                    play_now = url_or_trackname_or_filepath[1:]
                    audio_file_path = f'{output_path}\\{url_or_trackname_or_filepath[1:]}'

                    # Проверяем, что файл существует
                    if not os.path.isfile(audio_file_path):
                        await ctx.send(f"Файл \"{url_or_trackname_or_filepath[1:]}\" не найден.")
                        return

                    if not await check_audio_file(audio_file_path):
                        # Изменяем параметры трека
                        audio = AudioSegment.from_file(audio_file_path)
                        audio = audio.set_frame_rate(96000).set_channels(2)
                        new_path = f'{output_path}\\audio_fixed.mp3'
                        audio.export(new_path, format="mp3")
                        audio_file_path = new_path

                    index_play_now -= 1

                    if voice_client.is_playing():
                        voice_client.stop()
                else:
                    play_now = url_or_trackname_or_filepath
                    audio_file_path = f'{output_path}\\{url_or_trackname_or_filepath}'

                    # Проверяем, что файл существует
                    if not os.path.isfile(audio_file_path):
                        await ctx.send(f"Файл \"{url_or_trackname_or_filepath}\" не найден.")
                        return

                    # Проверяем, играет ли бот уже какую-то музыку
                    if voice_client.is_playing():
                        playlists[ctx.guild.name].append(url_or_trackname_or_filepath)
                        await ctx.send(f"Трек \"{url_or_trackname_or_filepath}\" добавлен в очередь")
                        return

                    if not await check_audio_file(audio_file_path):
                        # Изменяем параметры трека
                        audio = AudioSegment.from_file(audio_file_path)
                        audio = audio.set_frame_rate(96000).set_channels(2)
                        new_path = f'{output_path}\\audio_fixed.mp3'
                        audio.export(new_path, format="mp3")
                        audio_file_path = new_path

            else:
                if "|" not in url_or_trackname_or_filepath:
                    user_discord = interaction.user
                else:
                    p = url_or_trackname_or_filepath.split('|')
                    name_and_discriminator = p[0]  # получаем имя и дискриминатор в формате "Имя#Дискриминатор"

                    user_discord = discord.utils.get(interaction.guild.members,
                                                     name=name_and_discriminator.split("#")[0],
                                                     discriminator=name_and_discriminator.split("#")[
                                                         1])  # ищем участника с заданным именем и дискриминатором
                    url_or_trackname_or_filepath = p[1]

                if not str(user_discord) in tokens:
                    await interaction.response.send_message(
                        f"Пользователь {str(user_discord)} не вошёл в аккаунт Яндекс.Музыки. Для входа воспользуйтесь командой !authorize",
                        ephemeral=True)
                    return

                p = await play_Yandex_Music_playlist(interaction, url_or_trackname_or_filepath, str(user_discord))
                if not p:
                    return

                play_now = p[0]
                audio_file_path = p[1]

            data_servers[interaction.guild.name]['queue_repeat'] = audio_file_path
            options = '-loglevel panic'
            audio_source = await discord.FFmpegOpusAudio.from_probe(audio_file_path, options=options)

            # Проигрываем аудио
            voice_client.play(audio_source)

        if flag_repeat:
            data_servers[interaction.guild.name]['repeat_flag'] = False

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
            if data_servers[interaction.guild.name]['radio_check']:
                view.add_item(onyourwave_setting_button(interaction))

            embed = Embed(title="Сейчас играет", description=play_now, color=0xf1ca0d)
            if data_servers[interaction.guild.name]['radio_check']:
                embed.set_footer(text=f"{user_discord} запустил волну", icon_url=user_discord.avatar)
            else:
                embed.set_footer(text=f"{user_discord} запустил трек", icon_url=user_discord.avatar)

            if data_servers[interaction.guild.name]['cover_url']:
                embed.set_thumbnail(url=data_servers[interaction.guild.name]['cover_url'])

            message = await interaction.channel.send(embed=embed, view=view)
            now = datetime.datetime.now()
            current_time = now.time()

            # with open(filename, "a", encoding='windows 1251') as f:
            #     f.seek(0, 2)  # перемещаем курсор в конец файла
            #     f.write(f"Время: {current_time}\n"
            #             f"Сервер: {interaction.guild.name}\n"
            #             f"Музыка пользователя: {user_discord}"
            #             f"{play_now}\n\n")
            data_servers[interaction.guild.name]['message_check'] = message

        while voice_client.is_playing() or voice_client.is_paused():
            if voice_client.is_playing():
                data_servers[interaction.guild.name]['last_activity_time'] = datetime.datetime.now()
            await asyncio.sleep(1)
        if data_servers[interaction.guild.name]['repeat_flag']:
            data_servers[interaction.guild.name]['task'] = asyncio.create_task(
                play(interaction, data_servers[interaction.guild.name]['queue_repeat'], False))
            return
        elif data_servers[interaction.guild.name]['radio_check'] or data_servers[interaction.guild.name][
            'stream_by_track_check']:
            await play_radio(interaction=interaction, user_discord=user_discord)
        else:
            if data_servers[interaction.guild.name]['index_play_now'] + 1 < len(
                    data_servers[interaction.guild.name]['playlist']):
                data_servers[interaction.guild.name]['index_play_now'] += 1
                data_servers[interaction.guild.name]['task'] = asyncio.create_task(play(interaction, data_servers[
                    interaction.guild.name]['playlist'][data_servers[interaction.guild.name]['index_play_now']]))
                data_servers[interaction.guild.name]['task_reserv'] = data_servers[interaction.guild.name]['task']
                return
            else:
                await interaction.channel.send("Треки в очереди закончились")
                return

    except Exception as e:
        await interaction.channel.send(f"Произошла ошибка при проигрывании музыки: {e}.")

@tree.command(name='authorize', description="🔑Авторизация для использования сервиса Яндекс.Музыка")
@app_commands.describe(token='Вам нужно указать свой токен от аккаунта Яндекс.Музыки')
async def authorize(interaction: discord.Interaction, token: str):
    global tokens
    try:
        if str(interaction.user) in tokens:
            await interaction.response.send_message("Вы уже авторизованы 🥰", ephemeral=True)
            return

        client_check = Client(str(token)).init()
    except Exception:
        await interaction.response.send_message("К сожалению ваш токен неправильный 😞", ephemeral=True)
    else:
        await interaction.response.send_message("Вы успешно авторизовались 😍", ephemeral=True)
        user_discord = str(interaction.user)
        tokens[user_discord] = str(token)

        # записываем данные в файл
        with open("tokens.txt", "a") as f:
            f.seek(0, 2)  # перемещаем курсор в конец файла
            f.write(user_discord + " " + str(token) + "\n")

@tree.command(name='log', description="Служебная команда")
@app_commands.describe(server_name='Название сервера для которого нужно вывести лог')
async def log(interaction: discord.Interaction, server_name: str):
    global data_servers
    if str(interaction.user) == 'ti_jack#2994':
        if server_name in data_servers:
            for item in data_servers[server_name]:
                print(f'{item}: {data_servers[server_name][item]}')
        else:
            print("Такого сервера в логах нет")
    else:
        interaction.response.send_message("Это служебная команда!", ephemeral=True)

@tree.command(name='help', description="❓Справка по командам")
async def commands(interaction: discord.Interaction):
    command = {'/play': 'Имеет необязательный аргумент \'url_or_trackname\'\n\n'
                        'При вызове команды без аргумента - предложит выбрать плейлист из списка и запустит его\n\n'
                        'В аргумент можно передать:\n'
                        '1. Ссылку на видео YouTube\n'
                        '2. Ссылку на трек Яндекс.Музыки\n'
                        '3. Название трека (Для лучшего результата можно узазать название вместе с исполнителями)\n',
               '/authorize': 'Имеет обязательный аргумент \'token\'\n\n'
                             'В аргумент нужно передать Ваш токен от аккаунта Яндекс.Музыки\n\n'
                             'Без авторизации Вы не сможете пользоваться Яндекс.Музыкой\n\n'
                             'С инструкцией по получению токена можно ознакимиться здесь:\nhttps://github.com/MarshalX/yandex-music-api/discussions/513'
               }

    class next_command_button(Button):
        def __init__(self, interaction: discord.Interaction):
            super().__init__(style=ButtonStyle.primary, emoji="➡️", disabled=data_servers[interaction.guild.name]['command_now'] + 1 >= len(command))

        async def callback(self, interaction: discord.Interaction):
            global data_servers
            data_servers[interaction.guild.name]['command_now'] += 1
            self.view.clear_items()
            self.view.add_item(prev_command_button())
            self.view.add_item(next_command_button())
            await interaction.response.edit_message(
                content=f'Команда {data_servers[interaction.guild.name]["command_now"]+1} из {len(command)}',
                embed=Embed(title='/authorize', description=command['/authorize'], color=0xf1ca0d),
                view=self.view)

    class prev_command_button(Button):
        def __init__(self, interaction: discord.Interaction):
            super().__init__(style=ButtonStyle.primary, emoji="⬅️", disabled=data_servers[interaction.guild.name]['command_now']-1<0)

        async def callback(self, interaction: discord.Interaction):
            global data_servers
            data_servers[interaction.guild.name]['command_now'] -= 1
            self.view.clear_items()
            self.view.add_item(prev_command_button(interaction))
            self.view.add_item(next_command_button(interaction))
            await interaction.response.edit_message(
                content=f'Команда {data_servers[interaction.guild.name]["command_now"]+1} из {len(command)}',
                embed=Embed(title='/play', description=command['/play'], color=0xf1ca0d),
                view=self.view)

    view = View(timeout=1200.0)

    view.add_item(prev_command_button(interaction))
    view.add_item(next_command_button(interaction))


    embed = Embed(title='/play', description=command['/play'], color=0xf1ca0d)

    await interaction.response.send_message(content=f'Команда {data_servers[interaction.guild.name]["command_now"]+1} из {len(command)}', embed=embed, view=view)

@client.event
async def on_ready():
    await tree.sync()
    await client.change_presence(activity=discord.Activity(name="/help", type=discord.ActivityType.playing))
    print("Ready!")

# Запускаем бота
client.run('MTEwODgxMjQzNjkzNDUxMjgwMg.GU-z4e.NwgOx5UDp7HRMI5CnMidI7mvYZ0O07UvzkC4zk')
