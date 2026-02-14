import os
from dotenv import load_dotenv

# Загружаем только токен из .env
load_dotenv()

# Токен бота (только это скрыто)
TOKEN = os.getenv('BOT_TOKEN')

if not TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN не найден в .env файле!")
    exit(1)

# ID админа (открыто в коде)
ADMIN_ID = 1439379837

# ID канала (открыто в коде)
CHANNEL_ID = -1003606116956

# Настройка каналов для подписки
CHANNELS = [
    {
        'type': 'private',
        'id': -1003606116956,
        'link': 'https://t.me/+wUhQkvhZrcdiZDYy',
        'name': 'Первый канал'
    },
]

# Путь к JSON файлу
GAMES_JSON_PATH = "games.json"