import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не найден в .env файле")

WATER_REMINDER_TIMES = ["09:00", "13:00", "15:00", "17:00", "23:00"]

WATER_REMINDER_MESSAGE = "Время пить воду! Не забудьте выпить стакан воды для поддержания водного баланса! Иначе будут камни в почках :)"

subscribed_users = set()