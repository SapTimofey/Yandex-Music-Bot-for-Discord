import discord
from discord import app_commands

from .log import log
from global_variables import data_servers


@log.autocomplete('server_name')
async def autocomplete_log(interaction: discord.Interaction, search: str):
    return [app_commands.Choice(name=item, value=item) for item in data_servers if search in item]
