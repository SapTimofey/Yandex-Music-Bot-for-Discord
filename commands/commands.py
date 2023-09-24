import copy

import discord
from discord import ButtonStyle, Embed
from discord.ui import Button, View

from global_variables import tree, data_servers, data_server


@tree.command(name='help', description="❓Справка по командам")
async def commands(interaction: discord.Interaction):
    if interaction.guild.name not in data_servers:
        data_servers[interaction.guild.name] = copy.deepcopy(data_server)
    command = {'/play': 'Имеет необязательный аргумент \'ссылка_или_название\'\n\n'
                        'При вызове команды без аргумента - предложит выбрать плейлист / радио / альбом из списка и запустит его\n\n'
                        'В аргумент можно передать:\n'
                        '1. Ссылку на видео YouTube\n'
                        '2. Ссылку на трек / альбом из Яндекс.Музыки\n'
                        '3. Название трека (При вводе можно выбрать из выпадающего списка)\n',
               '/authorize': 'Имеет обязательный аргумент \'token\'\n\n'
                             'В аргумент нужно передать Ваш токен от аккаунта Яндекс.Музыки\n\n'
                             'Без авторизации Вы не сможете пользоваться Яндекс.Музыкой\n\n'
                             'С инструкцией по получению токена можно ознакимиться здесь:\nhttps://github.com/MarshalX/yandex-music-api/discussions/513\n\n'
                             'Также можно воспользоваться программой, через которую можно войти с помощью Авторизации Яндекса\n\n'
                             'Скачать можно здесь: https://disk.yandex.ru/d/zBhcTwiut1kxJw\n\n'
                             'Примечания для программы (Windows):\n'
                             '- Для работы программы необходимо наличие Google Chrome на вашем устройстве\n'
                             '- Версия программы не финальная и будет дорабатываться\n\n'
                             'Примечания для программы (Android):\n'
                             '- Версия Android должна быть не ниже 5.0\n'
                             '- Версия программы не финальная и будет дорабатываться'
               }

    class NextCommandButton(Button):
        def __init__(self, interaction: discord.Interaction):
            super().__init__(
                style=ButtonStyle.primary,
                emoji="➡️",
                disabled=data_servers[interaction.guild.name]['command_now'] + 1 >= len(command)
            )

        async def callback(self, interaction: discord.Interaction):
            data_servers[interaction.guild.name]['command_now'] += 1
            self.view.clear_items()
            self.view.add_item(PrevCommandButton(interaction))
            self.view.add_item(NextCommandButton(interaction))
            await interaction.response.edit_message(
                content=f'Команда {data_servers[interaction.guild.name]["command_now"] + 1} из {len(command)}',
                embed=Embed(
                    title='/authorize',
                    description=command['/authorize'],
                    color=0xf1ca0d
                ),
                view=self.view
            )

    class PrevCommandButton(Button):
        def __init__(self, interaction: discord.Interaction):
            super().__init__(
                style=ButtonStyle.primary,
                emoji="⬅️",
                disabled=data_servers[interaction.guild.name]['command_now'] - 1 < 0
            )

        async def callback(self, interaction: discord.Interaction):
            data_servers[interaction.guild.name]['command_now'] -= 1
            self.view.clear_items()
            self.view.add_item(PrevCommandButton(interaction))
            self.view.add_item(NextCommandButton(interaction))
            await interaction.response.edit_message(
                content=f'Команда {data_servers[interaction.guild.name]["command_now"]+1} из {len(command)}',
                embed=Embed(
                    title='/play',
                    description=command['/play'],
                    color=0xf1ca0d
                ),
                view=self.view
            )

    view = View(timeout=1200.0)

    view.add_item(PrevCommandButton(interaction))
    view.add_item(NextCommandButton(interaction))

    embed = Embed(title='/play', description=command['/play'], color=0xf1ca0d)

    await interaction.response.send_message(
        content=f'Команда {data_servers[interaction.guild.name]["command_now"]+1} из {len(command)}',
        embed=embed,
        view=view
    )
