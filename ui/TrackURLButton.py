import discord
from discord import ButtonStyle
from discord.ui import Button

from global_variables import data_servers


class TrackURLButton(Button):
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
