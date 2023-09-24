import discord
from discord import ButtonStyle
from discord.ui import Button

from global_variables import data_servers


class PrevPageButton(Button):
    def __init__(self, interaction: discord.Interaction, type_of_selection):
        self.type_of_selection = type_of_selection
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
        class_name = self.type_of_selection + '_select'
        self.view.add_item(globals()[class_name](interaction))
        self.view.add_item(PrevPageButton(interaction, self.type_of_selection))
        self.view.add_item(NextPageButton(interaction, self.type_of_selection))
        await interaction.edit_original_response(
            content=f"Страница {data_servers[interaction.guild.name][self.type_of_selection + '_page_index'] + 1} из "
                    f"{len(data_servers[interaction.guild.name][self.type_of_selection])}",
            view=self.view
        )
