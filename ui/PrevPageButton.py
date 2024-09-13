import discord
from discord import ButtonStyle
from discord.ui import Button

from global_variables import data_servers
from .TrackListSelect import TrackListSelect
from .AlbumListSelect import AlbumListSelect
from .MoodAndGenreSelect import MoodAndGenreSelect


class PrevPageButton(Button):
    def __init__(self, interaction: discord.Interaction, class_name, type_of_selection):
        self.type_of_selection = type_of_selection
        self.class_name = class_name
        super().__init__(
            style=ButtonStyle.primary,
            emoji="⬅️",
            row=2,
            disabled=data_servers[interaction.guild.name][type_of_selection + '_page_index'] - 1 < 0
        )

    async def callback(self, interaction: discord.Interaction):
        from .NextPageButton import NextPageButton

        await interaction.response.defer()
        data_servers[interaction.guild.name][self.type_of_selection + '_page_index'] -= 1
        self.view.clear_items()
        self.view.add_item(globals()[self.class_name](interaction))
        self.view.add_item(PrevPageButton(interaction, self.class_name, self.type_of_selection))
        self.view.add_item(NextPageButton(interaction, self.class_name, self.type_of_selection))
        await interaction.edit_original_response(
            content=f"Страница {data_servers[interaction.guild.name][self.type_of_selection + '_page_index'] + 1} из "
                    f"{len(data_servers[interaction.guild.name][self.type_of_selection])}",
            view=self.view
        )
