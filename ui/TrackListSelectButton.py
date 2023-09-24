import discord
from discord import ButtonStyle
from discord.ui import Button, View

from .NextPageButton import NextPageButton
from .PrevPageButton import PrevPageButton
from .TrackListSelect import TrackListSelect
from global_variables import data_servers


class TrackListSelectButton(Button):
    def __init__(self):
        super().__init__(
            style=ButtonStyle.primary,
            label="Выбор трека",
            row=3,
            emoji='🔎'
        )

    async def callback(self, interaction: discord.Interaction):
        view = View(timeout=1200)
        view.add_item(TrackListSelect(interaction))
        view.add_item(PrevPageButton(interaction, 'track_list'))
        view.add_item(NextPageButton(interaction, 'track_list'))
        await interaction.response.send_message(
            content=f"Страница {data_servers[interaction.guild.name]['track_list_page_index'] + 1} из "
                    f"{len(data_servers[interaction.guild.name]['track_list'])}",
            view=view,
            ephemeral=True
        )
