import os
import datetime
import discord

# Инициализируем Discord клиент
intents = discord.Intents.all()
intents.members = True
intents.messages = True
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

tokens = {}
birthdays = {}
google_token = None
bot_token = None
settings_onyourwave = {}
ru_settings_onyourwave = {
    'favorite': 'Любимое',
    'discover': 'Незнакомое',
    'popular': 'Популярное',
    'default': 'По умолчанию',
    'active': 'Бодрое',
    'fun': 'Весёлое',
    'calm': 'Спокойное',
    'sad': 'Грустное',
    'all': 'Любое',
    'russian': 'Русский',
    'not-russian': 'Иностранный',
    'without-words': 'Без слов',
    'any': 'Любой'
}
user = os.environ.get('USERNAME')
output_path = f'C:\\Users\\{user}\\Music'  # Путь к папке, где будет сохранен аудиофайл
data_server = {
    'playlist': [],
    'playlist_reserve': [],
    'playlist_title': None,
    'album': False,
    'album_list': [],
    'album_list_page_index': 0,
    'track_list': [],
    'track_list_page_index': 0,
    'mood_and_genre': [],
    'mood_and_genre_page_index': 0,
    'random': False,
    'repeat_flag': False,
    'queue_repeat': None,
    'index_play_now': 0,
    'task': None,
    'task_check_inactivity': None,
    'lyrics': None,
    'track_url': None,
    'cover_url': None,
    'track_id_play_now': None,
    'radio_client': None,
    'user_discord_play': None,
    'radio_check': False,
    'stream_by_track_check': False,
    'last_activity_time': datetime.datetime.now(),
    'message_check': None,
    'command_now': 0,
    'duration': 0,
    'can_edit_message': True
}
data_servers = {}
