import json
import os
from config import GAMES_JSON_PATH

def load_games():
    """Загружает игры из JSON файла"""
    if os.path.exists(GAMES_JSON_PATH):
        try:
            with open(GAMES_JSON_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Ошибка загрузки JSON: {e}")
            return create_default_games()
    else:
        print("📁 JSON файл не найден, создаю с базовыми играми")
        return create_default_games()

def create_default_games():
    """Создает базовую структуру игр"""
    default_games = {
        "game1": {
            "name": "Название игры 1",
            "download_link": "https://example.com/game1.apk",
            "media": None,
            "media_type": None,
            "post_link": None
        },
        "game2": {
            "name": "Название игры 2",
            "download_link": "https://example.com/game2.apk",
            "media": None,
            "media_type": None,
            "post_link": None
        }
    }
    save_games(default_games)
    return default_games

def save_games(games):
    """Сохраняет игры в JSON файл"""
    try:
        with open(GAMES_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(games, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения JSON: {e}")
        return False

# Загружаем игры при импорте
GAMES = load_games()