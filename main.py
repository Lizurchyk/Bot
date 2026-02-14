import telebot
from config import TOKEN
from handlers import setup_handlers

# Инициализация бота
bot = telebot.TeleBot(TOKEN)

# Настройка обработчиков
setup_handlers(bot)

# ============================================
# ЗАПУСК
# ============================================
if __name__ == "__main__":
    print("🤖 Бот запущен!")
    print("🔒 Токен загружен из .env файла")
    print("📁 Все настройки в config.py")
    print("📁 Игры в games.json")
    
    bot.infinity_polling()