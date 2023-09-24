import discord
from discord import ButtonStyle
from discord.ui import Button, View

from .OnyourwaveSettingDiversity import OnyourwaveSettingDiversity
from .OnyourwaveSettingLanguage import OnyourwaveSettingLanguage
from .OnyourwaveSettingMoodEnergy import OnyourwaveSettingMoodEnergy
from global_variables import data_servers, ru_settings_onyourwave, settings_onyourwave


class OnyourwaveSettingButton(Button):
    def __init__(self):
        super().__init__(
            style=ButtonStyle.primary,
            label="Настроить радио",
            emoji="⚙️",
            row=3
        )

    async def callback(self, interaction: discord.Interaction):
        view = View(timeout=1200.0)
        view.add_item(OnyourwaveSettingDiversity())
        view.add_item(OnyourwaveSettingMoodEnergy())
        view.add_item(OnyourwaveSettingLanguage())
        embed = discord.Embed(
            title=f'Настройки радио: {data_servers[interaction.guild.name]["radio_check"]["name"]}',
            color=0xf1ca0d,
            description=f'Характер: {ru_settings_onyourwave[settings_onyourwave[str(data_servers[interaction.guild.name]["user_discord_play"])]["diversity"]]}\n'
                        f'Настроение: {ru_settings_onyourwave[settings_onyourwave[str(data_servers[interaction.guild.name]["user_discord_play"])]["mood_energy"]]}\n'
                        f'Язык: {ru_settings_onyourwave[settings_onyourwave[str(data_servers[interaction.guild.name]["user_discord_play"])]["language"]]}'
        )
        await interaction.response.send_message(view=view, embed=embed, ephemeral=True)
