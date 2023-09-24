import os

import discord

from global_variables import bot_token, client, tokens, birthdays, tree
from commands import *


if os.path.exists("tokens.txt") and os.path.getsize("tokens.txt") > 0:
    with open("tokens.txt", "r") as f:
        lines = f.readlines()
        for line in lines:
            user_discord, token = line.strip().rsplit(maxsplit=1)
            if user_discord == 'google':
                google_token = token
            elif user_discord == 'bot_test':
                bot_token = token
            else:
                # добавляем пару ключ-значение в глобальный словарь
                tokens[user_discord] = token
                birthdays[user_discord] = False


@client.event
async def on_ready():
    await tree.sync()
    await client.change_presence(activity=discord.Activity(name="/help", type=discord.ActivityType.playing))
    print("Ready!")


# Запускаем бота
client.run(bot_token)
