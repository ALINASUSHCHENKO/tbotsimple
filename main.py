import os
import time
import threading
import schedule
from datetime import datetime, timedelta
from dotenv import load_dotenv
import telebot
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN не найден в .env файле")

# Глобальные переменные
subscribed_users = set()

# Добавляем тестовое время +2 минуты от текущего времени для проверки
test_time = (datetime.now() + timedelta(minutes=2)).strftime("%H:%M")
WATER_REMINDER_TIMES = ["09:00", "13:00", "15:00", "17:00", "23:00", test_time]
WATER_REMINDER_MESSAGE = "💧 Время пить воду! Не забудьте выпить стакан воды для поддержания водного баланса."

# Создание бота
bot = telebot.TeleBot(TOKEN)
logger.info("Бот инициализирован")


class WaterReminderScheduler:
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.setup_schedule()
    
    def setup_schedule(self):
        """Настройка расписания напоминаний"""
        for reminder_time in WATER_REMINDER_TIMES:
            schedule.every().day.at(reminder_time).do(self.send_water_reminder)
            logger.info(f"Напоминание настроено на {reminder_time}")
    
    def send_water_reminder(self):
        """Отправка напоминаний всем подписанным пользователям"""
        if not subscribed_users:
            logger.info("Нет подписанных пользователей для отправки напоминания")
            return
        
        current_time = datetime.now().strftime("%H:%M")
        user_count = len(subscribed_users)
        logger.info(f"Отправка напоминаний в {current_time} для {user_count} пользователей")
        
        success_count = 0
        error_count = 0
        
        for chat_id in subscribed_users.copy():
            try:
                self.bot.send_message(chat_id, WATER_REMINDER_MESSAGE)
                success_count += 1
                logger.info(f"Напоминание отправлено пользователю {chat_id}")
            except Exception as e:
                error_count += 1
                logger.error(f"Ошибка отправки пользователю {chat_id}: {e}")
                # Не удаляем сразу, возможно временная ошибка
                
        logger.info(f"Напоминания отправлены: {success_count} успешно, {error_count} с ошибками")
    
    def get_next_reminder_time(self):
        """Возвращает время следующего напоминания"""
        current_time = datetime.now()
        
        for time_str in WATER_REMINDER_TIMES:
            reminder_time = datetime.strptime(time_str, "%H:%M").replace(
                year=current_time.year,
                month=current_time.month,
                day=current_time.day
            )
            
            if reminder_time > current_time:
                return reminder_time
        
        # Если все напоминания сегодня прошли, берем первое завтра
        return datetime.strptime(WATER_REMINDER_TIMES[0], "%H:%M").replace(
            year=current_time.year,
            month=current_time.month,
            day=current_time.day + 1
        )
    
    def run(self):
        """Запуск планировщика в отдельном потоке"""
        logger.info("Планировщик напоминаний запущен")
        print("🕐 Планировщик запущен. Ожидайте напоминаний...")
        while True:
            schedule.run_pending()
            time.sleep(30)  # Проверяем каждые 30 секунд


scheduler = WaterReminderScheduler(bot)
scheduler_thread = threading.Thread(target=scheduler.run, daemon=True)
scheduler_thread.start()


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "💧 Water Reminder Bot 💧\n\n"
        "Я буду напоминать вам пить воду в оптимальное время:\n"
        "• 09:00 - Утро\n• 13:00 - Обед\n• 15:00 - День\n• 17:00 - Вечер\n• 23:00 - Ночь\n\n"
        "Команды:\n"
        "/start - начать работу\n"
        "/subscribe - подписаться на напоминания\n"
        "/unsubscribe - отписаться\n"
        "/status - статус подписки\n"
        "/next - следующее напоминание\n"
        "/schedule - расписание\n"
        "/test - тестовое напоминание"
    )
    bot.reply_to(message, welcome_text)
    logger.info(f"Пользователь {message.from_user.id} вызвал /start")


@bot.message_handler(commands=['subscribe'])
def subscribe_user(message):
    chat_id = message.chat.id
    if chat_id in subscribed_users:
        bot.reply_to(message, "✅ Вы уже подписаны на напоминания о воде!")
    else:
        subscribed_users.add(chat_id)
        bot.reply_to(message, "✅ Вы успешно подписались на напоминания о воде! Я буду напоминать вам в 9, 13, 15, 17 и 23 часа.")
        logger.info(f"Пользователь {chat_id} подписался на напоминания")


@bot.message_handler(commands=['unsubscribe'])
def unsubscribe_user(message):
    chat_id = message.chat.id
    if chat_id in subscribed_users:
        subscribed_users.remove(chat_id)
        bot.reply_to(message, "❌ Вы отписались от напоминаний о воде.")
        logger.info(f"Пользователь {chat_id} отписался от напоминаний")
    else:
        bot.reply_to(message, "ℹ️ Вы не были подписаны на напоминания.")


@bot.message_handler(commands=['status'])
def check_status(message):
    chat_id = message.chat.id
    if chat_id in subscribed_users:
        bot.reply_to(message, "✅ Вы подписаны на напоминания о воде.")
    else:
        bot.reply_to(message, "❌ Вы не подписаны на напоминания о воде. Используйте /subscribe для подписки.")


@bot.message_handler(commands=['next'])
def next_reminder(message):
    """Показывает время следующего напоминания"""
    next_time = scheduler.get_next_reminder_time()
    current_time = datetime.now()
    time_until = next_time - current_time
    
    hours = int(time_until.total_seconds() // 3600)
    minutes = int((time_until.total_seconds() % 3600) // 60)
    
    response = f"⏰ Следующее напоминание через {hours}ч {minutes}м в {next_time.strftime('%H:%M')}"
    bot.reply_to(message, response)


@bot.message_handler(commands=['schedule'])
def show_schedule(message):
    """Показывает полное расписание напоминаний"""
    schedule_text = "📅 Расписание напоминаний:\n\n"
    for time_str in WATER_REMINDER_TIMES:
        if time_str.startswith("09:") or time_str.startswith("13:") or time_str.startswith("15:") or time_str.startswith("17:") or time_str.startswith("23:"):
            schedule_text += f"• {time_str}\n"
        else:
            schedule_text += f"• {time_str} (тестовое)\n"
    
    schedule_text += f"\nВсего подписанных пользователей: {len(subscribed_users)}"
    bot.reply_to(message, schedule_text)


@bot.message_handler(commands=['test'])
def test_reminder(message):
    """Тестовая команда для проверки напоминания"""
    scheduler.send_water_reminder()
    bot.reply_to(message, "✅ Тестовое напоминание отправлено всем подписанным пользователям!")


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    """Обработка любых других сообщений"""
    bot.reply_to(message, "🤔 Не понимаю ваше сообщение. Используйте /help для просмотра доступных команд.")


if __name__ == "__main__":
    try:
        logger.info("=== ЗАПУСК БОТА ===")
        
        # Проверяем подключение к боту
        bot_info = bot.get_me()
        logger.info(f"Бот: {bot_info.first_name} (@{bot_info.username})")
        
        print("=" * 50)
        print("🤖 БОТ ЗАПУЩЕН!")
        print("=" * 50)
        print(f"Бот: {bot_info.first_name} (@{bot_info.username})")
        print("📋 Доступные команды:")
        print("  /start - начать работу")
        print("  /subscribe - подписаться на напоминания")
        print("  /test - тестовое напоминание")
        print("  /schedule - показать расписание")
        print("⏰ Тестовое напоминание через 2 минуты")
        print("📝 Логи сохраняются в bot.log")
        print("⏸️  Нажмите Ctrl+C для остановки")
        print("=" * 50)
        
        # Запускаем бота
        bot.infinity_polling(skip_pending=True, timeout=20)
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()