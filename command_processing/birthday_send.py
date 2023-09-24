import discord
from yandex_music import Client

from global_variables import tokens, birthdays


async def birthday_send(interaction: discord.Interaction):
    if str(interaction.user) in tokens:
        birthdays[str(interaction.user)] = True
        client_ym = Client(tokens[str(interaction.user)]).init()
        if client_ym.me.account.now.split('T')[0].split('-', maxsplit=1)[1] == \
                client_ym.me.account.birthday.split('-', maxsplit=1)[1]:
            await interaction.response.send_message(
                content=f"С Днём Рождения {client_ym.me.account.first_name} 🎉🎊",
                ephemeral=True
            )