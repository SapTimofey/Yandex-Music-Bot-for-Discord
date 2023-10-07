import asyncio
import datetime
import os

import discord
import eyed3
from discord import Embed
from discord.ui import View

from global_variables import birthdays, output_path, data_servers

from ui.DisconnectButton import DisconnectButton
from ui.LyricsButton import LyricsButton
from ui.NextTrackButton import NextTrackButton
from ui.OnyourwaveSettingButton import OnyourwaveSettingButton
from ui.PauseResumeButton import PauseResumeButton
from ui.PlaylistSelect import PlaylistSelect
from ui.PrevTrackButton import PrevTrackButton
from ui.RepeatButton import RepeatButton
from ui.StreamByTrackButton import StreamByTrackButton
from ui.TrackListSelectButton import TrackListSelectButton
from ui.TrackURLButton import TrackURLButton
from ui.RandomButton import RandomButton


async def play(interaction: discord.Interaction, url_or_trackname_or_filepath: str = None):
    from .play_yandex_music_radio import play_yandex_music_radio
    from .milliseconds_to_time import milliseconds_to_time
    from .remove_last_playing_message import remove_last_playing_message
    from .birthday_send import birthday_send
    from .play_yandex_music_playlist import play_yandex_music_playlist
    from .play_yandex_music_url import play_yandex_music_url
    from .play_youtube import play_youtube
    error_count = 0
    while error_count < 3:
        try:
            voice_client = interaction.guild.voice_client

            if not url_or_trackname_or_filepath:  # если не передан url
                view = View(timeout=1800)
                view.add_item(PlaylistSelect(interaction))
                await interaction.edit_original_response(content='', view=view)
                return

            while True:
                play_filepath = False
                if "youtube.com" in url_or_trackname_or_filepath:
                    play_now = await play_youtube(interaction, url_or_trackname_or_filepath)
                    if not play_now:
                        return

                elif "music.yandex.ru" in url_or_trackname_or_filepath:
                    play_now = await play_yandex_music_url(interaction, url_or_trackname_or_filepath)
                    if not play_now:
                        return

                elif ":\\" in url_or_trackname_or_filepath:
                    play_filepath = True
                    audio_file_path = url_or_trackname_or_filepath

                    if not os.path.isfile(audio_file_path):
                        await interaction.edit_original_response(
                            content=f"Файл `{url_or_trackname_or_filepath}` не найден.",
                        )
                        return
                    audiofile = eyed3.load(audio_file_path)

                    data_servers[interaction.guild.name]['duration'] = int(audiofile.info.time_secs) * 1000

                    if not audiofile.tag.artist or not audiofile.tag.title:
                        play_now = f'\nНазвание файла: {os.path.basename(audio_file_path)}'
                    else:
                        play_now = f"\nТрек: {audiofile.tag.title}" + \
                                    f"\nИсполнители: {audiofile.tag.artist}"
                else:
                    if not data_servers[interaction.guild.name]['playlist']:
                        play_now = await play_yandex_music_playlist(interaction, playlist_id=url_or_trackname_or_filepath)
                        if not play_now:
                            return
                    else:
                        play_now = await play_yandex_music_playlist(interaction, url_or_trackname_or_filepath)
                        if not play_now:
                            return

                data_servers[interaction.guild.name]['queue_repeat'] = url_or_trackname_or_filepath
                options = '-loglevel panic'
                if not play_filepath:
                    audio_source = await discord.FFmpegOpusAudio.from_probe(
                        source=f'{output_path}\\{data_servers[interaction.guild.name]["user_discord_play"]}.mp3',
                        options=options
                    )
                else:
                    audio_source = await discord.FFmpegOpusAudio.from_probe(
                        source=url_or_trackname_or_filepath,
                        options=options
                    )

                voice_client.play(audio_source)

                duration_track = await milliseconds_to_time(data_servers[interaction.guild.name]['duration'])

                if not birthdays[str(data_servers[interaction.guild.name]['user_discord_play'])]:
                    await birthday_send(interaction)

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

                if not data_servers[interaction.guild.name]['repeat_flag']:
                    await remove_last_playing_message(interaction)
                    view = View(timeout=1200.0)

                    view.add_item(PrevTrackButton(interaction))
                    view.add_item(PauseResumeButton())
                    view.add_item(NextTrackButton(interaction))
                    view.add_item(RepeatButton())
                    view.add_item(RandomButton(interaction))
                    view.add_item(LyricsButton(interaction))
                    view.add_item(TrackURLButton(interaction))
                    view.add_item(DisconnectButton())

                    if data_servers[interaction.guild.name]['playlist']:
                        view.add_item(TrackListSelectButton())
                    elif data_servers[interaction.guild.name]['radio_check']:
                        view.add_item(OnyourwaveSettingButton())

                    view.add_item(StreamByTrackButton(interaction))

                    message = await interaction.channel.send(embed=embed, view=view)
                    data_servers[interaction.guild.name]['message_check'] = message
                else:
                    embed.clear_fields()
                    embed.add_field(name=f'00:00 / {duration_track}', value='')
                    try:
                        await data_servers[interaction.guild.name]['message_check'].edit(embed=embed)
                    except (discord.HTTPException, discord.NotFound, discord.Forbidden):
                        pass

                start_time = 0
                while voice_client.is_playing() or voice_client.is_paused():
                    start_time_inaccuracy = datetime.datetime.now()
                    end_time_inaccuracy = datetime.datetime.now()
                    if voice_client.is_playing():
                        start_time += 1000
                        if data_servers[interaction.guild.name]['can_edit_message']:
                            time_now = await milliseconds_to_time(start_time)
                            embed.clear_fields()
                            embed.add_field(name=f'{time_now} / {duration_track}', value='')
                            try:
                                await data_servers[interaction.guild.name]['message_check'].edit(embed=embed)
                            except (discord.HTTPException, discord.NotFound, discord.Forbidden):
                                pass
                        data_servers[interaction.guild.name]['last_activity_time'] = datetime.datetime.now()
                        end_time_inaccuracy = datetime.datetime.now()
                    await asyncio.sleep(1 - (end_time_inaccuracy - start_time_inaccuracy).microseconds / 1000000)

                # Если включен повтор трека
                if data_servers[interaction.guild.name]['repeat_flag']:
                    url_or_trackname_or_filepath = data_servers[interaction.guild.name]['queue_repeat']

                # Если запущено радио
                elif data_servers[interaction.guild.name]['radio_check']:
                    url_or_trackname_or_filepath = await play_yandex_music_radio(
                        interaction=interaction,
                        station_id=data_servers[interaction.guild.name]["radio_check"]["station"],
                        station_from=data_servers[interaction.guild.name]["radio_check"]["station_from"]
                    )

                # Если запущено радио по треку
                elif data_servers[interaction.guild.name]['stream_by_track_check']:
                    url_or_trackname_or_filepath = await play_yandex_music_radio(
                        interaction=interaction,
                        station_id=data_servers[interaction.guild.name]['stream_by_track_check']["station"],
                        station_from=data_servers[interaction.guild.name]['stream_by_track_check']["station_from"]
                    )

                # Если запущен плейлист / альбом
                else:
                    # Если трек не последний, то переходим к следующему
                    if data_servers[interaction.guild.name]['index_play_now'] + 1 < len(
                            data_servers[interaction.guild.name]['playlist']):
                        data_servers[interaction.guild.name]['index_play_now'] += 1
                        url_or_trackname_or_filepath = \
                            data_servers[interaction.guild.name]['playlist'][
                                data_servers[interaction.guild.name]['index_play_now']]
                    else:
                        # Если трек последний, но включена случайная последовательность,
                        # то сбрасываем индекс и начинаем плейлист заново.
                        if data_servers[interaction.guild.name]['random']:
                            data_servers[interaction.guild.name]['index_play_now'] = 0
                            url_or_trackname_or_filepath = \
                                data_servers[interaction.guild.name]['playlist'][
                                    data_servers[interaction.guild.name]['index_play_now']]
                        else:
                            await interaction.channel.send("Треки в очереди закончились")
                            return

        except asyncio.CancelledError:
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
                return False
