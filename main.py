import os
import time
import threading
import schedule
from datetime import datetime, timedelta
from dotenv import load_dotenv
import telebot
from telebot import types
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN не найден в .env файле")

subscribed_users = set()

test_time = (datetime.now() + timedelta(minutes=2)).strftime("%H:%M")
WATER_REMINDER_TIMES = ["09:00", "13:00", "15:00", "17:00", "23:00", test_time]
WATER_REMINDER_MESSAGE = "💧 Время пить воду! Не забудьте выпить стакан воды для поддержания водного баланса."

BOT_VERSION = "1.0.0"
BOT_AUTHOR = "ALINASUSHCHENKO"
BOT_PURPOSE = "Напоминать о питье воды в течение дня"

bot = telebot.TeleBot(TOKEN)
logger.info("Бот инициализирован")


class WaterReminderScheduler:
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.setup_schedule()

    def setup_schedule(self):
        for reminder_time in WATER_REMINDER_TIMES:
            schedule.every().day.at(reminder_time).do(self.send_water_reminder)
            logger.info(f"Напоминание настроено на {reminder_time}")

    def send_water_reminder(self):
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

        logger.info(f"Напоминания отправлены: {success_count} успешно, {error_count} с ошибками")

    def get_next_reminder_time(self):
        current_time = datetime.now()

        for time_str in WATER_REMINDER_TIMES:
            reminder_time = datetime.strptime(time_str, "%H:%M").replace(
                year=current_time.year,
                month=current_time.month,
                day=current_time.day
            )

            if reminder_time > current_time:
                return reminder_time

        return datetime.strptime(WATER_REMINDER_TIMES[0], "%H:%M").replace(
            year=current_time.year,
            month=current_time.month,
            day=current_time.day + 1
        )

    def run(self):
        logger.info("Планировщик напоминаний запущен")
        print("🕐 Планировщик запущен. Ожидайте напоминаний...")
        while True:
            schedule.run_pending()
            time.sleep(30)


def make_main_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("/about", "/ping")
    keyboard.row("/hide", "/show")
    keyboard.row("/help", "/confirm")
    return keyboard


def make_confirm_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("Да", callback_data="confirm:yes"),
        types.InlineKeyboardButton("Нет", callback_data="confirm:no"),
        types.InlineKeyboardButton("Позже", callback_data="confirm:later"),
        types.InlineKeyboardButton("Не уверен", callback_data="confirm:unsure")
    )
    return keyboard


scheduler = WaterReminderScheduler(bot)
scheduler_thread = threading.Thread(target=scheduler.run, daemon=True)
scheduler_thread.start()


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "💧 Water Reminder Bot 💧\n\n"
        "Я буду напоминать вам пить воду в оптимальное время:\n"
        "• 09:00 - Утро\n• 13:00 - Обед\n• 15:00 - День\n"
        "• 17:00 - Вечер\n• 23:00 - Ночь\n\n"
        "📋 Список команд:\n"
        "/start, /help - начать работу\n"
        "/about - информация о боте\n"
        "/ping - проверка работы\n"
        "/subscribe - подписаться на напоминания\n"
        "/unsubscribe - отписаться\n"
        "/status - статус подписки\n"
        "/next - следующее напоминание\n"
        "/schedule - расписание\n"
        "/confirm - подтверждение действия\n"
        "/test - тестовое напоминание\n"
        "/hide - скрыть клавиатуру\n"
        "/show - показать клавиатуру"
    )
    bot.reply_to(message, welcome_text, reply_markup=make_main_keyboard())
    logger.info(f"Пользователь {message.from_user.id} вызвал /start")


@bot.message_handler(commands=['about'])
def about_bot(message):
    about_text = (
        "Информация о боте:\n\n"
        f"Автор: {BOT_AUTHOR}\n"
        f"Версия: {BOT_VERSION}\n"
        f"Назначение: {BOT_PURPOSE}\n"
        f"Репозиторий: github.com/ALINASUSHCHENKO/tbotsimple\n\n"
        "Этот бот помогает поддерживать водный баланс, "
        "напоминая пить воду в течение дня."
    )
    bot.reply_to(message, about_text)
    logger.info(f"Пользователь {message.from_user.id} запросил /about")


@bot.message_handler(commands=['ping'])
def ping_bot(message):
    try:
        start_time = time.time()

        sent_msg = bot.send_message(message.chat.id, "⏳ Измеряем пинг...")

        end_time = time.time()
        round_trip_time = round((end_time - start_time) * 1000, 2)

        api_start = time.time()
        bot.get_me()
        api_end = time.time()
        api_ping = round((api_end - api_start) * 1000, 2)

        ping_text = (
            f"Результаты пинга:\n\n"
            f"Полное время ответа: {round_trip_time} мс\n"
            f"Пинг до API Telegram: {api_ping} мс\n\n"
        )

        if round_trip_time < 200:
            quality = "Отличное"
        elif round_trip_time < 500:
            quality = "Хорошее"
        elif round_trip_time < 1000:
            quality = "Среднее"
        else:
            quality = "Плохое"

        ping_text += f"Качество соединения: {quality}"

        bot.edit_message_text(
            ping_text,
            message.chat.id,
            sent_msg.message_id
        )

        logger.info(f"Ping от {message.from_user.id}: {round_trip_time} мс (API: {api_ping} мс)")

    except Exception as e:
        error_msg = f"Ошибка измерения пинга: {e}"
        if 'sent_msg' in locals():
            bot.edit_message_text(error_msg, message.chat.id, sent_msg.message_id)
        else:
            bot.reply_to(message, error_msg)
        logger.error(f"Ошибка пинга от {message.from_user.id}: {e}")


@bot.message_handler(commands=['confirm'])
def confirm_action(message):
    confirm_text = "Подтвердите ваше действие:"
    bot.send_message(
        message.chat.id,
        confirm_text,
        reply_markup=make_confirm_keyboard()
    )
    logger.info(f"Пользователь {message.from_user.id} запросил подтверждение")


@bot.callback_query_handler(func=lambda call: call.data.startswith('confirm:'))
def handle_confirmation(call):
    choice = call.data.split(':', 1)[1]

    responses = {
        'yes': 'Действие подтверждено!',
        'no': 'Действие отменено.',
        'later': 'Хорошо, напомню позже.',
        'unsure': 'Вернемся к этому позже.'
    }

    bot.answer_callback_query(call.id, "Принято!")

    bot.edit_message_text(
        f"{responses.get(choice, 'Неизвестный выбор')}",
        call.message.chat.id,
        call.message.message_id
    )
    logger.info(f"Пользователь {call.from_user.id} выбрал: {choice}")


@bot.message_handler(commands=['subscribe'])
def subscribe_user(message):
    chat_id = message.chat.id
    if chat_id in subscribed_users:
        bot.reply_to(message, "Вы уже подписаны на напоминания о воде!")
    else:
        subscribed_users.add(chat_id)
        bot.reply_to(message, "Вы успешно подписались на напоминания о воде! Я буду напоминать вам в 9, 13, 15, 17 и 23 часа.")
        logger.info(f"Пользователь {chat_id} подписался на напоминания")


@bot.message_handler(commands=['unsubscribe'])
def unsubscribe_user(message):
    chat_id = message.chat.id
    if chat_id in subscribed_users:
        subscribed_users.remove(chat_id)
        bot.reply_to(message, "Вы отписались от напоминаний..")
        logger.info(f"Пользователь {chat_id} отписался от напоминаний")
    else:
        bot.reply_to(message, "Вы не были подписаны на напоминания.")


@bot.message_handler(commands=['status'])
def check_status(message):
    chat_id = message.chat.id
    if chat_id in subscribed_users:
        bot.reply_to(message, "Вы подписаны на напоминания.")
    else:
        bot.reply_to(message, "Вы не подписаны на напоминания. Используйте /subscribe для подписки.")


@bot.message_handler(commands=['next'])
def next_reminder(message):
    next_time = scheduler.get_next_reminder_time()
    current_time = datetime.now()
    time_until = next_time - current_time

    hours = int(time_until.total_seconds() // 3600)
    minutes = int((time_until.total_seconds() % 3600) // 60)

    response = f"Следующее напоминание через {hours}ч {minutes}м в {next_time.strftime('%H:%M')}"
    bot.reply_to(message, response)


@bot.message_handler(commands=['schedule'])
def show_schedule(message):
    schedule_text = "Расписание напоминаний:\n\n"
    for time_str in WATER_REMINDER_TIMES:
        if any(time_str.startswith(x) for x in ["09:", "13:", "15:", "17:", "23:"]):
            schedule_text += f"• {time_str}\n"
        else:
            schedule_text += f"• {time_str} (тестовое)\n"

    schedule_text += f"\nВсего подписанных пользователей: {len(subscribed_users)}"
    bot.reply_to(message, schedule_text)


@bot.message_handler(commands=['test'])
def test_reminder(message):
    scheduler.send_water_reminder()
    bot.reply_to(message, "Тестовое напоминание отправлено всем подписанным пользователям!")


@bot.message_handler(commands=['hide'])
def hide_keyboard(message):
    remove_keyboard = types.ReplyKeyboardRemove()
    bot.send_message(
        message.chat.id,
        "Клавиатура скрыта. Используйте /show чтобы вернуть.",
        reply_markup=remove_keyboard
    )


@bot.message_handler(commands=['show'])
def show_keyboard(message):
    bot.send_message(
        message.chat.id,
        "Клавиатура активна:",
        reply_markup=make_main_keyboard()
    )


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "Не понимаю ваше сообщение. Используйте /help для просмотра доступных команд.")


if __name__ == "__main__":
    try:
        logger.info("ЗАПУСК БОТА")

        bot_info = bot.get_me()
        logger.info(f"Бот: {bot_info.first_name} (@{bot_info.username})")

        print("=" * 50)
        print("БОТ ЗАПУЩЕН!")
        print("=" * 50)
        print(f"Бот: {bot_info.first_name} (@{bot_info.username})")
        print(f"Версия: {BOT_VERSION}")
        print("Доступные команды:")
        print("  /about - информация о боте")
        print("  /ping - проверка пинга")
        print("  /confirm - подтверждение с кнопками")
        print("  /subscribe - подписка на напоминания")
        print("Тестовое напоминание через 2 минуты")
        print("Логи сохраняются в bot.log")
        print("Ctrl+C для остановки")
        print("=" * 50)

        bot.infinity_polling(skip_pending=True, timeout=20)

    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()