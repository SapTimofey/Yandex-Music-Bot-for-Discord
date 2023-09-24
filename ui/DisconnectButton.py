import discord
from discord import ButtonStyle
from discord.ui import Button

from command_processing.disconnect import disconnect


class DisconnectButton(Button):
    def __init__(self):
        super().__init__(style=ButtonStyle.red, label="Отключить", emoji="📛", row=3)

    async def callback(self, interaction: discord.Interaction):
        await disconnect(interaction)
