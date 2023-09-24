import discord
from discord import app_commands

from global_variables import tree, data_servers


@tree.command(name='log', description="Служебная команда")
@app_commands.describe(server_name='По умоляанию Ваш сервер.')
@app_commands.default_permissions()
async def log(interaction: discord.Interaction, server_name: str = None):
    await interaction.response.defer(ephemeral=True)

    if not server_name:
        server_name = interaction.guild.name

    if server_name in data_servers:
        message = ''
        for item in data_servers[server_name]:
            if item == 'lyrics' and data_servers[server_name][item]:
                message += f'{item}: is present\n'
            else:
                message += f'{item}: {data_servers[server_name][item]}\n'

        filename = f'{server_name}_log.txt'
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(message)

        await interaction.edit_original_response(attachments=[discord.File(filename)])
    else:
        await interaction.edit_original_response(content="Такого сервера в логах нет")
