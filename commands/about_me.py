import discord
from discord import Embed

from global_variables import tree


@tree.command(name='about_me', description='🪪Обо мне')
async def about_me(interaction: discord.Interaction):
    await interaction.response.send_message(
        embed=Embed(
            title='Обо мне',
            description='Автором бота является пользователь 𝓽𝓲_𝓳𝓪𝓬𝓴\n\n'
                        'С открытым кодом можно ознакомиться тут:\n'
                        'https://github.com/SapTimofey/Yandex-Music-Bot-for-Discord\n\n'
                        'С открытым кодом библиотеки yandex_music можно ознакомиться тут:\n'
                        'https://github.com/MarshalX/yandex-music-api\n\n'
                        'Версия бота: 0.8.3',
            color=0xf1ca0d
        ),
        ephemeral=True
    )
