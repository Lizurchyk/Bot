import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ForceReply
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup 
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ============================================
# НАСТРОЙКА КАНАЛОВ ДЛЯ ПОДПИСКИ (3 ТИПА)
# ============================================
CHANNELS = [
    # ТВОЙ КАНАЛ SimpleDLC
    {
        'type': 'public',
        'username': '@SimpleDLC',
        'link': 'https://t.me/+MyUkrVP_q5E3YzM6',
        'name': 'SimpleDLC | Читы на игры',
        'emoji': '📢'
    },
    {
        'type': 'public',
        'username': '@SigmaAPK',
        'link': 'https://t.me/+TNKOjSyKCtg5M2Jh',
        'name': 'Sigma.APK - Игры и Приложения',
        'emoji': '📢'
    },
]

# ============================================
# FSM СОСТОЯНИЯ
# ============================================
class AddGame(StatesGroup):
    key = State()
    name = State()
    link = State()
    media = State()

class AdminStates(StatesGroup):
    waiting_game_key = State()
    waiting_text = State()

# ============================================
# ФУНКЦИЯ ПОИСКА games.json ПО ВСЕЙ ПАМЯТИ
# ============================================
def find_games_json():
    """Ищет файл games.json во всей доступной файловой системе"""
    
    # Список возможных путей для поиска
    search_paths = [
        '/app/games.json',              # Путь на хостинге
        '/home/games.json',              # Домашняя директория
        '/root/games.json',               # Root директория
        './games.json',                    # Текущая папка
        '../games.json',                   # Папка выше
        '/var/www/games.json',             # Веб-сервер
        '/usr/src/app/games.json',         # Docker контейнер
        os.path.join(os.path.dirname(__file__), 'games.json'),  # Папка со скриптом
        os.path.join(os.getcwd(), 'games.json'),  # Текущая рабочая папка
    ]
    
    # Добавляем путь из переменной окружения если есть
    env_path = os.getenv('GAMES_JSON_PATH')
    if env_path:
        search_paths.insert(0, env_path)
    
    # Ищем файл
    for path in search_paths:
        try:
            if os.path.exists(path):
                print(f"✅ games.json найден по пути: {path}")
                return path
        except:
            continue
    
    # Если не нашли, ищем рекурсивно по всей файловой системе
    print("🔍 Файл не найден в стандартных путях, ищу рекурсивно...")
    
    # Папки для рекурсивного поиска
    root_dirs = ['/app', '/home', '/root', '/var', '/usr']
    
    for root_dir in root_dirs:
        if os.path.exists(root_dir):
            for dirpath, dirnames, filenames in os.walk(root_dir, followlinks=False):
                if 'games.json' in filenames:
                    found_path = os.path.join(dirpath, 'games.json')
                    print(f"✅ games.json найден по пути: {found_path}")
                    return found_path
                # Ограничиваем глубину поиска
                if dirpath.count(os.sep) > 5:
                    del dirnames[:]
    
    print("❌ games.json не найден нигде!")
    return None

# ============================================
# ЗАГРУЗКА ИГР ИЗ JSON (ТОЛЬКО ЧТЕНИЕ)
# ============================================
def load_games():
    """Только читает games.json, ничего не записывает"""
    
    # Находим путь к файлу
    json_path = find_games_json()
    
    if json_path and os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                games = json.load(f)
                print(f"✅ Загружено {len(games)} игр из {json_path}")
                return games
        except Exception as e:
            print(f"❌ Ошибка загрузки JSON: {e}")
            return {}
    else:
        print("❌ Файл games.json не найден!")
        return {}

# Загружаем игры (только чтение)
GAMES = load_games()

# Пустая функция сохранения (ничего не делает)
def save_games(games):
    """Заглушка - ничего не сохраняет"""
    return True

# Хранилище ожидающих игр для пользователей
pending_games = {}

# ============================================
# ФУНКЦИИ ПРОВЕРКИ ПОДПИСКИ
# ============================================
async def check_subscription(user_id: int):
    """Проверяет подписку на ВСЕ каналы"""
    unsubscribed = []
    
    for channel in CHANNELS:
        if channel['type'] == 'link':
            continue
            
        try:
            if channel['type'] == 'private':
                member = await bot.get_chat_member(channel['id'], user_id)
            elif channel['type'] == 'public':
                member = await bot.get_chat_member(channel['username'], user_id)
            
            if member.status not in ['creator', 'administrator', 'member']:
                unsubscribed.append(channel)
        except:
            unsubscribed.append(channel)
    
    return len(unsubscribed) == 0, unsubscribed

def subscription_keyboard(channels):
    """Создает клавиатуру с кнопками для каналов"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for ch in channels:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"{ch['emoji']} {ch['name']}",
                url=ch['link']
            )
        ])
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(
            text="✅ Проверить подписку",
            callback_data="check_subs"
        )
    ])
    
    return keyboard

def game_keyboard(download_link):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Скачать", url=download_link)]
    ])

def post_keyboard(bot_username, game_key):
    deep_link = f"https://t.me/{bot_username}?start={game_key}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Скачать", url=deep_link)]
    ])

# ============================================
# ОТПРАВКА ИГРЫ ПОЛЬЗОВАТЕЛЮ
# ============================================
async def send_game_to_user(chat_id: int, game_key: str):
    game = GAMES.get(game_key)
    if not game:
        await bot.send_message(chat_id, "❌ Игра не найдена.")
        return False

    keyboard = game_keyboard(game['download_link'])
    text = f"**{game['name']}**"
    
    if game.get('media') and game.get('media_type'):
        try:
            if game['media_type'] == 'photo':
                await bot.send_photo(
                    chat_id,
                    game['media'],
                    caption=text,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
            elif game['media_type'] == 'video':
                await bot.send_video(
                    chat_id,
                    game['media'],
                    caption=text,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
        except:
            await bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=keyboard)
    else:
        await bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=keyboard)
    
    return True

# ============================================
# ПУБЛИКАЦИЯ ПОСТА В КАНАЛ
# ============================================
async def publish_post(chat_id: int, game_key: str, message: types.Message, is_test: bool = False):
    game = GAMES.get(game_key)
    if not game:
        return False, "Игра не найдена"

    target = ADMIN_ID if is_test else CHANNEL_ID
    bot_username = (await bot.get_me()).username
    keyboard = post_keyboard(bot_username, game_key)

    try:
        if game.get('media') and game.get('media_type') == 'photo':
            sent = await bot.send_photo(
                target,
                game['media'],
                caption=message.caption or message.text or "",
                caption_entities=message.caption_entities or message.entities,
                reply_markup=keyboard
            )
        elif game.get('media') and game.get('media_type') == 'video':
            sent = await bot.send_video(
                target,
                game['media'],
                caption=message.caption or message.text or "",
                caption_entities=message.caption_entities or message.entities,
                reply_markup=keyboard
            )
        elif message.photo:
            sent = await bot.send_photo(
                target,
                message.photo[-1].file_id,
                caption=message.caption,
                caption_entities=message.caption_entities,
                reply_markup=keyboard
            )
        elif message.video:
            sent = await bot.send_video(
                target,
                message.video.file_id,
                caption=message.caption,
                caption_entities=message.caption_entities,
                reply_markup=keyboard
            )
        elif message.text:
            sent = await bot.send_message(
                target,
                message.text,
                entities=message.entities,
                reply_markup=keyboard
            )
        else:
            return False, "Нет контента для отправки"
        
        if not is_test:
            post_link = f"https://t.me/c/{str(CHANNEL_ID).replace('-100', '')}/{sent.message_id}"
            # НЕ сохраняем в games.json, просто возвращаем ссылку
            return True, post_link
        return True, "Тест отправлен"
            
    except Exception as e:
        return False, str(e)

# ============================================
# ПРОВЕРКА ДОСТУПА АДМИНА
# ============================================
async def check_admin_access(message: types.Message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID:
        await message.answer("❌ У вас нет прав администратора")
        return False
    
    is_subscribed, unsubscribed = await check_subscription(user_id)
    if not is_subscribed:
        keyboard = subscription_keyboard(unsubscribed)
        channels_text = "\n".join([f"• {ch['name']}" for ch in unsubscribed])
        await bot.send_message(
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
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    args = message.text.split()
    game_key = args[1] if len(args) > 1 else None

    is_subscribed, unsubscribed = await check_subscription(user_id)

    if not is_subscribed:
        keyboard = subscription_keyboard(unsubscribed)
        channels_text = "\n".join([f"• {ch['name']}" for ch in unsubscribed])
        
        if game_key:
            pending_games[user_id] = game_key
        
        await message.answer(
            f"⚠️ **Подпишись на каналы:**\n\n{channels_text}",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    else:
        if game_key:
            await send_game_to_user(chat_id, game_key)
        else:
            await message.answer("Для установки нажми кнопку скачать под постом в канале @SimpleDLC")

# ============================================
# АДМИН КОМАНДЫ
# ============================================
@dp.message(Command("admin"))
async def cmd_admin(message: types.Message, state: FSMContext):
    if not await check_admin_access(message):
        return
    
    await state.set_state(AdminStates.waiting_game_key)
    await state.update_data(test_mode=False)
    await message.answer(
        "📝 **Пост в канал**\n\nВведите ключ игры:",
        parse_mode="Markdown",
        reply_markup=ForceReply()
    )

@dp.message(Command("adminTest"))
async def cmd_admin_test(message: types.Message, state: FSMContext):
    if not await check_admin_access(message):
        return
    
    await state.set_state(AdminStates.waiting_game_key)
    await state.update_data(test_mode=True)
    await message.answer(
        "🧪 **Тестовый пост**\n\nВведите ключ игры:",
        parse_mode="Markdown",
        reply_markup=ForceReply()
    )

# ============================================
# КОМАНДА /addgame (ОТКЛЮЧЕНА - ТОЛЬКО ЧТЕНИЕ)
# ============================================
@dp.message(Command("addgame"))
async def cmd_add_game(message: types.Message, state: FSMContext):
    await message.answer("❌ Режим только для чтения. Добавление игр отключено.")

@dp.message(Command("games"))
async def cmd_list_games(message: types.Message):
    if not await check_admin_access(message):
        return
    
    if not GAMES:
        await message.answer("📭 База данных игр пуста или не найдена.")
        return
    
    text = "**📋 Список игр (только чтение):**\n\n"
    for key, game in GAMES.items():
        text += f"• `{key}` - {game['name']}"
        if game.get('post_link'):
            text += f" - [Пост]({game['post_link']})"
        if game.get('media'):
            text += f" - {'📸' if game['media_type'] == 'photo' else '🎬'}"
        text += "\n"
    
    await message.answer(text, parse_mode="Markdown")

# ============================================
# ОБРАБОТЧИК ДЛЯ ВВОДА КЛЮЧА
# ============================================
@dp.message(AdminStates.waiting_game_key, F.text)
async def process_game_key(message: types.Message, state: FSMContext):
    game_key = message.text.strip()
    
    if game_key not in GAMES:
        await message.answer(
            f"❌ Игра '{game_key}' не найдена!\n\nДоступные игры: {', '.join(GAMES.keys())}"
        )
        return
    
    await state.update_data(game_key=game_key)
    data = await state.get_data()
    
    if data.get('test_mode') is not None:
        await state.set_state(AdminStates.waiting_text)
        await message.answer(
            f"✅ Ключ: {game_key}\n\n"
            f"📝 Теперь отправь команду **/text**",
            parse_mode="Markdown"
        )

# ============================================
# КОМАНДА /text
# ============================================
@dp.message(Command("text"))
async def cmd_text(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    current_state = await state.get_state()
    if current_state != AdminStates.waiting_text.state:
        await message.answer("❌ Сначала введи ключ игры после /admin или /adminTest")
        return
    
    await state.set_state(AdminStates.waiting_text)
    await message.answer(
        "📤 **Отправь свой пост**\n\n"
        "Можешь использовать любое форматирование, фото или видео.\n"
        "После отправки пост сразу уйдет по назначению.",
        parse_mode="Markdown",
        reply_markup=ForceReply()
    )

# ============================================
# ОБРАБОТЧИК ДЛЯ ПОЛУЧЕНИЯ ПОСТА
# ============================================
@dp.message(AdminStates.waiting_text, F.text | F.photo | F.video)
async def process_post(message: types.Message, state: FSMContext):
    data = await state.get_data()
    game_key = data['game_key']
    is_test = data.get('test_mode', False)
    
    success, result = await publish_post(ADMIN_ID, game_key, message, is_test)
    
    if success:
        if is_test:
            await message.answer("✅ **Тестовый пост отправлен!**\nПосмотри выше ↑", parse_mode="Markdown")
        else:
            await message.answer(f"✅ **Пост опубликован в канале!**\n🔗 Ссылка: {result}", parse_mode="Markdown")
    else:
        await message.answer(f"❌ Ошибка: {result}")
    
    await state.clear()

# ============================================
# КНОПКА ПРОВЕРКИ ПОДПИСКИ
# ============================================
@dp.callback_query(lambda c: c.data == "check_subs")
async def process_check_subs(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    await callback.answer("🔍 Проверяю...")
    is_subscribed, unsubscribed = await check_subscription(user_id)

    if is_subscribed:
        try:
            await bot.delete_message(chat_id, callback.message.message_id)
        except:
            pass

        game_key = pending_games.pop(user_id, None)

        if game_key:
            await send_game_to_user(chat_id, game_key)
        else:
            await bot.send_message(chat_id, "✅ Подписка оформлена!")

    else:
        keyboard = subscription_keyboard(unsubscribed)
        channels_text = "\n".join([f"• {ch['name']}" for ch in unsubscribed])
        try:
            await callback.message.edit_text(
                text=f"⚠️ **Всё ещё нужно подписаться:**\n\n{channels_text}",
                parse_mode="Markdown",
                reply_markup=keyboard
            )
        except:
            pass

# ============================================
# ЗАПУСК
# ============================================
async def main():
    print("=" * 50)
    print("🤖 Бот запущен!")
    print(f"👤 Admin ID: {ADMIN_ID}")
    print(f"📢 Channel ID: {CHANNEL_ID}")
    print(f"📊 Каналов для подписки: {len(CHANNELS)}")
    print(f"🎮 Загружено игр: {len(GAMES)}")
    print("📁 Режим: ТОЛЬКО ЧТЕНИЕ (запись в JSON отключена)")
    print("=" * 50)
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
