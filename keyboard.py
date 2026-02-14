from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def sub_keyboard(channels):
    """Клавиатура для подписки на каналы"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    for ch in channels:
        emoji = "🔐" if ch['type'] == 'private' else "📢"
        keyboard.add(InlineKeyboardButton(f"{emoji} {ch['name']}", url=ch['link']))
    keyboard.add(InlineKeyboardButton("✅ Проверить подписки", callback_data="check_subs"))
    return keyboard

def game_keyboard(download_link):
    """Клавиатура для скачивания игры"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("📥 Скачать", url=download_link))
    return keyboard

def post_keyboard(bot_username, game_key):
    """Клавиатура для поста в канале"""
    deep_link = f"https://t.me/{bot_username}?start={game_key}"
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🎮 Получить игру", url=deep_link))
    return keyboard