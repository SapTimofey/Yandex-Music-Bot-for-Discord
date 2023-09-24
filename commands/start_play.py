import asyncio
import copy

import discord
from discord import app_commands
from yandex_music import Client

from global_variables import tokens, data_server, tree, data_servers, settings_onyourwave
from command_processing.play import play
from command_processing.check_inactivity import check_inactivity
from command_processing.remove_last_playing_message import remove_last_playing_message


@tree.command(name='play',
              description="🎧Воспроизвести трек. При вызове без аргумента - воспроизвести трек из списка")
@app_commands.rename(url_or_trackname_or_filepath='ссылка_или_название')
@app_commands.describe(
    url_or_trackname_or_filepath='Ссылка на трек / альбом из Яндекс.Музыки; Ссылка на трек из YouTube; Название трека')
async def start_play(interaction: discord.Interaction, url_or_trackname_or_filepath: str = None):
    await remove_last_playing_message(interaction)
    await interaction.response.defer(ephemeral=True)

    author_voice_state = interaction.user.voice
    if author_voice_state is None:
        await interaction.edit_original_response(content="В ожидании, когда Вы подключитесь к голосовому каналу.")
        while not author_voice_state:
            await asyncio.sleep(0.1)
            author_voice_state = interaction.user.voice

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
    except (discord.HTTPException, discord.NotFound, discord.Forbidden):
        pass
