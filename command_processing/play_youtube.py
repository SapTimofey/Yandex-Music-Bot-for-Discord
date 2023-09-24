import asyncio
import re

import discord
from googleapiclient.discovery import build
from pytube import YouTube

from global_variables import data_servers, google_token, output_path


async def play_youtube(interaction: discord.Interaction, url_or_trackname_or_filepath):
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
