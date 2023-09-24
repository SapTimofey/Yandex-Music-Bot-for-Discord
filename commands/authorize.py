import discord
from discord import app_commands
from yandex_music import Client, exceptions

from global_variables import tree, tokens, birthdays


@tree.command(name='authorize', description="🔑Авторизация для использования сервиса Яндекс.Музыка")
@app_commands.describe(token='Вам нужно указать свой токен от аккаунта Яндекс.Музыки')
async def authorize(interaction: discord.Interaction, token: str):
    try:
        if str(interaction.user) in tokens:
            await interaction.response.send_message(content="Вы уже авторизованы 🥰", ephemeral=True)
            return

        Client(str(token)).init()
    except exceptions:
        await interaction.response.send_message(content="К сожалению Ваш токен неправильный 😞", ephemeral=True)
    else:
        await interaction.response.send_message(content="Вы успешно авторизовались 😍", ephemeral=True)
        user_discord = str(interaction.user)
        tokens[user_discord] = str(token)
        birthdays[user_discord] = False

        # записываем данные в файл
        with open("tokens.txt", "a") as f:
            f.seek(0, 2)
            f.write(user_discord + " " + str(token) + "\n")
