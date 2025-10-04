import time
import schedule
import threading
from datetime import datetime

from config import WATER_REMINDER_TIMES, WATER_REMINDER_MESSAGE, subscribed_users
from utils.logger import logger


class WaterReminderScheduler:
    def __init__(self, bot):
        self.bot = bot
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

        for chat_id in subscribed_users.copy():
            try:
                self.bot.send_message(chat_id, WATER_REMINDER_MESSAGE)
                logger.info(f"Напоминание отправлено пользователю {chat_id}")
            except Exception as e:
                logger.error(f"Ошибка отправки пользователю {chat_id}: {e}")
                subscribed_users.discard(chat_id)

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
        while True:
            schedule.run_pending()
            time.sleep(60)


def start_scheduler(bot):
    """Запуск планировщика в фоновом режиме"""
    scheduler = WaterReminderScheduler(bot)
    scheduler_thread = threading.Thread(target=scheduler.run, daemon=True)
    scheduler_thread.start()
    return scheduler
