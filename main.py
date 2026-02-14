import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ForceReply
import json
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')


ADMIN_ID = 1439379837
CHANNEL_ID = -1003606116956
GAMES_JSON_PATH = "games.json"

CHANNELS = [
    {
        'type': 'private',
        'id': -1003606116956,
        'link': 'https://t.me/+wUhQkvhZrcdiZDYy',
        'name': 'Первый канал'
    },
]

# ============================================
# ЗАГРУЗКА ИГР ИЗ JSON
# ============================================
def load_games():
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
    try:
        with open(GAMES_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(games, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения JSON: {e}")
        return False

GAMES = load_games()

# ============================================
# ИНИЦИАЛИЗАЦИЯ БОТА
# ============================================
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
#bot = telebot.TeleBot(TOKEN)

# Хранилище состояний
admin_states = {}
pending_games = {}

# ============================================
# ФУНКЦИИ
# ============================================
def check_sub(user_id):
    unsubscribed = []
    for channel in CHANNELS:
        try:
            if channel['type'] == 'private':
                member = bot.get_chat_member(channel['id'], user_id)
                if member.status not in ['creator', 'administrator', 'member']:
                    unsubscribed.append(channel)
            elif channel['type'] == 'public':
                member = bot.get_chat_member(channel['username'], user_id)
                if member.status not in ['creator', 'administrator', 'member']:
                    unsubscribed.append(channel)
        except Exception as e:
            print(f"Ошибка проверки канала: {e}")
            unsubscribed.append(channel)
    return len(unsubscribed) == 0, unsubscribed

def sub_keyboard(channels):
    keyboard = InlineKeyboardMarkup(row_width=1)
    for ch in channels:
        emoji = "🔐" if ch['type'] == 'private' else "📢"
        keyboard.add(InlineKeyboardButton(f"{emoji} {ch['name']}", url=ch['link']))
    keyboard.add(InlineKeyboardButton("✅ Проверить подписки", callback_data="check_subs"))
    return keyboard

def send_game_to_user(chat_id, game_key):
    game = GAMES.get(game_key)
    if not game:
        bot.send_message(chat_id, "❌ Игра не найдена.")
        return False

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("📥 Скачать", url=game['download_link']))
    
    text = f"**{game['name']}**"
    
    if game.get('media') and game.get('media_type'):
        try:
            if game['media_type'] == 'photo':
                bot.send_photo(
                    chat_id,
                    game['media'],
                    caption=text,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
            elif game['media_type'] == 'video':
                bot.send_video(
                    chat_id,
                    game['media'],
                    caption=text,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
        except Exception as e:
            print(f"Ошибка отправки медиа: {e}")
            bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=keyboard)
    else:
        bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=keyboard)
    
    return True

def publish_post(chat_id, game_key, text_message, is_test=False):
    game = GAMES.get(game_key)
    if not game:
        return False, "Игра не найдена"

    target = ADMIN_ID if is_test else CHANNEL_ID
    bot_username = bot.get_me().username
    deep_link = f"https://t.me/{bot_username}?start={game_key}"
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🎮 Получить игру", url=deep_link))

    try:
        post_text = text_message.text or text_message.caption or ""
        
        if game.get('media') and game.get('media_type') == 'photo':
            sent = bot.send_photo(
                target,
                game['media'],
                caption=post_text,
                caption_entities=text_message.entities or text_message.caption_entities,
                reply_markup=keyboard
            )
        elif game.get('media') and game.get('media_type') == 'video':
            sent = bot.send_video(
                target,
                game['media'],
                caption=post_text,
                caption_entities=text_message.entities or text_message.caption_entities,
                reply_markup=keyboard
            )
        elif text_message.photo:
            sent = bot.send_photo(
                target,
                text_message.photo[-1].file_id,
                caption=text_message.caption,
                caption_entities=text_message.caption_entities,
                reply_markup=keyboard
            )
        elif text_message.video:
            sent = bot.send_video(
                target,
                text_message.video.file_id,
                caption=text_message.caption,
                caption_entities=text_message.caption_entities,
                reply_markup=keyboard
            )
        elif text_message.text:
            sent = bot.send_message(
                target,
                text_message.text,
                entities=text_message.entities,
                reply_markup=keyboard
            )
        else:
            return False, "Нет контента для отправки"
        
        if not is_test:
            post_link = f"https://t.me/c/{str(CHANNEL_ID).replace('-100', '')}/{sent.message_id}"
            game['post_link'] = post_link
            save_games(GAMES)
            return True, post_link
        return True, "Тест отправлен"
            
    except Exception as e:
        return False, str(e)

def check_admin_access(message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID:
        bot.reply_to(message, "❌ У вас нет прав администратора")
        return False
    
    is_subscribed, unsubscribed = check_sub(user_id)
    if not is_subscribed:
        keyboard = sub_keyboard(unsubscribed)
        channels_text = "\n".join([f"• {ch['name']}" for ch in unsubscribed])
        bot.send_message(
            message.chat.id,
            f"⚠️ **Вы не подписаны на каналы:**\n\n{channels_text}",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        return False
    
    return True

# ============================================
# КОМАНДА /start
# ============================================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    args = message.text.split()
    game_key = args[1] if len(args) > 1 else None

    is_subscribed, unsubscribed = check_sub(user_id)

    if not is_subscribed:
        keyboard = sub_keyboard(unsubscribed)
        channels_text = "\n".join([f"• {ch['name']}" for ch in unsubscribed])
        
        if game_key:
            pending_games[user_id] = game_key
        
        bot.send_message(
            chat_id,
            f"⚠️ **Подпишись на каналы:**\n\n{channels_text}",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    else:
        if game_key:
            send_game_to_user(chat_id, game_key)
        else:
            bot.send_message(chat_id, "Для установки нажми кнопку скачать под постом в канале @SimpleDLC")

# ============================================
# АДМИН КОМАНДЫ
# ============================================
@bot.message_handler(commands=['admin'])
def admin_command(message):
    if not check_admin_access(message):
        return
    
    admin_states[ADMIN_ID] = {'action': 'waiting_game_key', 'test_mode': False}
    bot.send_message(
        ADMIN_ID,
        "📝 **Пост в канал**\n\nВведите ключ игры:",
        parse_mode="Markdown",
        reply_markup=ForceReply(selective=True)
    )

@bot.message_handler(commands=['adminTest'])
def admin_test(message):
    if not check_admin_access(message):
        return
    
    admin_states[ADMIN_ID] = {'action': 'waiting_game_key', 'test_mode': True}
    bot.send_message(
        ADMIN_ID,
        "🧪 **Тестовый пост**\n\nВведите ключ игры:",
        parse_mode="Markdown",
        reply_markup=ForceReply(selective=True)
    )

@bot.message_handler(commands=['text'])
def text_command(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    is_subscribed, _ = check_sub(ADMIN_ID)
    if not is_subscribed:
        bot.send_message(ADMIN_ID, "❌ Сначала подпишись на каналы!")
        return
    
    if ADMIN_ID not in admin_states:
        bot.send_message(ADMIN_ID, "❌ Сначала используй /admin или /adminTest")
        return
    
    state = admin_states[ADMIN_ID]
    if state.get('action') != 'waiting_text_command':
        bot.send_message(ADMIN_ID, "❌ Сначала введи ключ игры после /admin или /adminTest")
        return
    
    state['action'] = 'waiting_post_text'
    bot.send_message(
        ADMIN_ID,
        "📤 **Отправь свой пост**\n\n"
        "Можешь использовать любое форматирование, фото или видео.\n"
        "После отправки пост сразу уйдет по назначению.",
        parse_mode="Markdown",
        reply_markup=ForceReply(selective=True)
    )

@bot.message_handler(commands=['addgame'])
def add_game(message):
    if not check_admin_access(message):
        return
    
    admin_states[ADMIN_ID] = {'action': 'adding_game', 'step': 'key'}
    bot.send_message(
        ADMIN_ID,
        "➕ **Добавление игры**\n\nВведите ключ (например: game3):",
        parse_mode="Markdown",
        reply_markup=ForceReply(selective=True)
    )

@bot.message_handler(commands=['games'])
def list_games(message):
    if not check_admin_access(message):
        return
    
    text = "**📋 Список игр:**\n\n"
    for key, game in GAMES.items():
        text += f"• `{key}` - {game['name']}"
        if game.get('post_link'):
            text += f" - [Пост]({game['post_link']})"
        if game.get('media'):
            text += f" - {'📸' if game['media_type'] == 'photo' else '🎬'}"
        text += "\n"
    
    bot.send_message(ADMIN_ID, text, parse_mode="Markdown")

# ============================================
# ОБРАБОТЧИКИ СООБЩЕНИЙ
# ============================================
@bot.message_handler(func=lambda message: message.from_user.id == ADMIN_ID and 
                     message.from_user.id in admin_states and 
                     admin_states[ADMIN_ID].get('action') == 'waiting_game_key',
                     content_types=['text'])
def handle_game_key(message):
    game_key = message.text.strip()
    
    if game_key not in GAMES:
        bot.send_message(
            ADMIN_ID, 
            f"❌ Игра '{game_key}' не найдена!\n\nДоступные игры: {', '.join(GAMES.keys())}"
        )
        return
    
    state = admin_states[ADMIN_ID]
    state['game_key'] = game_key
    state['action'] = 'waiting_text_command'
    
    bot.send_message(
        ADMIN_ID,
        f"✅ Ключ: {game_key}\n\n"
        f"📝 Теперь отправь команду **/text**",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda message: message.from_user.id == ADMIN_ID and 
                     message.from_user.id in admin_states and 
                     admin_states[ADMIN_ID].get('action') == 'waiting_post_text',
                     content_types=['text', 'photo', 'video'])
def handle_post_text(message):
    state = admin_states[ADMIN_ID]
    game_key = state['game_key']
    is_test = state.get('test_mode', False)
    
    success, result = publish_post(ADMIN_ID, game_key, message, is_test)
    
    if success:
        if is_test:
            bot.send_message(
                ADMIN_ID,
                "✅ **Тестовый пост отправлен!**\nПосмотри выше ↑",
                parse_mode="Markdown"
            )
        else:
            bot.send_message(
                ADMIN_ID,
                f"✅ **Пост опубликован в канале!**\n🔗 Ссылка: {result}",
                parse_mode="Markdown"
            )
    else:
        bot.send_message(
            ADMIN_ID,
            f"❌ Ошибка: {result}"
        )
    
    del admin_states[ADMIN_ID]

@bot.message_handler(func=lambda message: message.from_user.id == ADMIN_ID and 
                     message.from_user.id in admin_states and 
                     admin_states[ADMIN_ID].get('action') == 'adding_game',
                     content_types=['text', 'photo', 'video'])
def handle_add_game(message):
    state = admin_states[ADMIN_ID]
    
    if state['step'] == 'key':
        if message.text in GAMES:
            bot.send_message(ADMIN_ID, "❌ Такой ключ уже есть!")
            return
        
        state['game_key'] = message.text
        state['step'] = 'name'
        bot.send_message(
            ADMIN_ID,
            "Введите **название игры**:",
            parse_mode="Markdown",
            reply_markup=ForceReply(selective=True)
        )
    
    elif state['step'] == 'name':
        state['game_name'] = message.text
        state['step'] = 'link'
        bot.send_message(
            ADMIN_ID,
            "Введите **ссылку для скачивания**:",
            parse_mode="Markdown",
            reply_markup=ForceReply(selective=True)
        )
    
    elif state['step'] == 'link':
        state['download_link'] = message.text
        state['step'] = 'media'
        bot.send_message(
            ADMIN_ID,
            "📸 **Отправьте фото для игры**\n\n"
            "Просто отправьте фото сюда (как обычное сообщение)\n"
            "Или отправьте 'пропустить' если фото не нужно",
            parse_mode="Markdown",
            reply_markup=ForceReply(selective=True)
        )
    
    elif state['step'] == 'media':
        media_id = None
        media_type = None
        
        if message.photo:
            media_id = message.photo[-1].file_id
            media_type = 'photo'
            bot.send_message(ADMIN_ID, "✅ Фото сохранено!")
        elif message.video:
            media_id = message.video.file_id
            media_type = 'video'
            bot.send_message(ADMIN_ID, "✅ Видео сохранено!")
        elif message.text and message.text.lower() == 'пропустить':
            pass
        else:
            bot.send_message(ADMIN_ID, "❌ Отправь фото, видео или 'пропустить'")
            return
        
        GAMES[state['game_key']] = {
            "name": state['game_name'],
            "download_link": state['download_link'],
            "media": media_id,
            "media_type": media_type,
            "post_link": None
        }
        
        if save_games(GAMES):
            bot.send_message(
                ADMIN_ID,
                f"✅ **Игра {state['game_key']} добавлена!**\n"
                f"Название: {state['game_name']}\n"
                f"Медиа: {'✅' if media_id else '❌'}\n"
                f"📁 Данные сохранены в games.json",
                parse_mode="Markdown"
            )
        else:
            bot.send_message(
                ADMIN_ID,
                f"⚠️ **Игра добавлена, но ошибка сохранения в JSON**",
                parse_mode="Markdown"
            )
        
        del admin_states[ADMIN_ID]

# ============================================
# КНОПКА ПРОВЕРКИ ПОДПИСКИ
# ============================================
@bot.callback_query_handler(func=lambda call: call.data == "check_subs")
def check_subs_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    bot.answer_callback_query(call.id, "🔍 Проверяю...")
    is_subscribed, unsubscribed = check_sub(user_id)

    if is_subscribed:
        try:
            bot.delete_message(chat_id, call.message.message_id)
        except:
            pass

        game_key = pending_games.pop(user_id, None)

        if game_key:
            send_game_to_user(chat_id, game_key)
        else:
            bot.send_message(chat_id, "✅ Подписка оформлена!")

    else:
        keyboard = sub_keyboard(unsubscribed)
        channels_text = "\n".join([f"• {ch['name']}" for ch in unsubscribed])
        try:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text=f"⚠️ **Всё ещё нужно подписаться:**\n\n{channels_text}",
                parse_mode="Markdown",
                reply_markup=keyboard
            )
        except:
            pass

# ============================================
# ЗАПУСК
# ============================================
if __name__ == "__main__":
    print("🤖 Бот запущен!")
    print("🔒 Только токен загружен из .env файла")
    print(f"👤 Admin ID: {ADMIN_ID}")
    print(f"📢 Channel ID: {CHANNEL_ID}")
    print(f"📁 JSON файл с играми: {GAMES_JSON_PATH}")
    print(f"🎮 Загружено игр: {len(GAMES)}")
    
    bot.infinity_polling()