import discord

from global_variables import client


async def remove_last_playing_message(interaction: discord.Interaction):
    async for message in interaction.channel.history():
        if message.author == client.user and \
                (message.content.startswith('Текст') or
                 message.content.startswith('Треки в очереди') or
                 message.content.startswith('Не удалось') or
                 message.content.startswith('Произошла ошибка') or
                 len(message.embeds) > 0):
            try:
                await message.delete()
            except Exception:
                pass
