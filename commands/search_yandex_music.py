import discord
from discord import app_commands
from yandex_music import Client

from .start_play import start_play
from global_variables import tokens


@start_play.autocomplete('url_or_trackname_or_filepath')
async def search_yandex_music(interaction: discord.Interaction, search: str):
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
    return [app_commands.Choice(name=item, value=item) for item in url_or_trackname_or_filepath]
