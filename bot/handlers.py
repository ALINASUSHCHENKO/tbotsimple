from datetime import datetime
import telebot

from config import subscribed_users, WATER_REMINDER_TIMES
from utils.logger import logger


class BotHandlers:
    def __init__(self, bot, scheduler):
        self.bot = bot
        self.scheduler = scheduler
        self.setup_handlers()

    def setup_handlers(self):

        @self.bot.message_handler(commands=['start', 'help'])
        def send_welcome(message):
            welcome_text = (
                "Water Reminder Bot \n\n"
                "Я буду напоминать вам пить воду в оптимальное время:\n"
                "• 09:00 - Утро\n"
                "• 13:00 - Обед\n"
                "• 15:00 - Послеобеденное время\n"
                "• 17:00 - Вечер\n"
                "• 23:00 - Перед сном\n\n"
                "Команды:\n"
                "/start - начать работу\n"
                "/subscribe - подписаться на напоминания\n"
                "/unsubscribe - отписаться от напоминаний\n"
                "/status - статус подписки\n"
                "/next - следующее напоминание\n"
                "/schedule - расписание напоминаний"
            )
            self.bot.reply_to(message, welcome_text)
            logger.info(f"Пользователь {message.from_user.id} вызвал команду /start")

        @self.bot.message_handler(commands=['subscribe'])
        def subscribe_user(message):
            chat_id = message.chat.id
            if chat_id in subscribed_users:
                self.bot.reply_to(message, "Вы уже подписаны на напоминания о воде!")
            else:
                subscribed_users.add(chat_id)
                response = (
                    "Вы успешно подписались на напоминания о воде! "
                    "Я буду напоминать вам в 9, 13, 15, 17 и 23 часа."
                )
                self.bot.reply_to(message, response)
                logger.info(f"Пользователь {chat_id} подписался на напоминания")

        @self.bot.message_handler(commands=['unsubscribe'])
        def unsubscribe_user(message):
            chat_id = message.chat.id
            if chat_id in subscribed_users:
                subscribed_users.remove(chat_id)
                self.bot.reply_to(message, "Вы отписались от напоминаний о воде.")
                logger.info(f"Пользователь {chat_id} отписался от напоминаний")
            else:
                self.bot.reply_to(message, "ℹВы не были подписаны на напоминания.")

        @self.bot.message_handler(commands=['status'])
        def check_status(message):
            chat_id = message.chat.id
            if chat_id in subscribed_users:
                self.bot.reply_to(message, "Вы подписаны на напоминания о воде.")
            else:
                response = (
                    "Вы не подписаны на напоминания о воде. "
                    "Используйте /subscribe для подписки."
                )
                self.bot.reply_to(message, response)

        @self.bot.message_handler(commands=['next'])
        def next_reminder(message):
            next_time = self.scheduler.get_next_reminder_time()
            current_time = datetime.now()
            time_until = next_time - current_time

            hours = int(time_until.total_seconds() // 3600)
            minutes = int((time_until.total_seconds() % 3600) // 60)

            response = (
                f"Следующее напоминание через {hours}ч {minutes}м "
                f"в {next_time.strftime('%H:%M')}"
            )
            self.bot.reply_to(message, response)

        @self.bot.message_handler(commands=['schedule'])
        def show_schedule(message):
            schedule_text = "📅 Расписание напоминаний:\n\n"
            for time_str in WATER_REMINDER_TIMES:
                schedule_text += f"• {time_str}\n"

            schedule_text += f"\nВсего подписанных пользователей: {len(subscribed_users)}"
            self.bot.reply_to(message, schedule_text)

        @self.bot.message_handler(func=lambda message: True)
        def echo_all(message):
            response = (
                "Не понимаю ваше сообщение. "
                "Используйте /help для просмотра доступных команд."
            )
            self.bot.reply_to(message, response)