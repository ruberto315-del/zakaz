import os
from dotenv import load_dotenv

load_dotenv()

# Токен бота
BOT_TOKEN = "8264290134:AAGdDjDFrwYxrrHqDw3Fbj1FjwGg9g30Mhs"

# ID адміністратора
ADMIN_ID = 810944378

# Назва бази даних
DATABASE_NAME = "shop_bot.db"

# LiqPay налаштування (заповніть своїми даними)
LIQPAY_PUBLIC_KEY = os.getenv("LIQPAY_PUBLIC_KEY", "")
LIQPAY_PRIVATE_KEY = os.getenv("LIQPAY_PRIVATE_KEY", "")

# Статуси замовлення
ORDER_STATUSES = {
    "pending": "Очікує обробки",
    "processing": "В обробці",
    "ready": "Готове до відправки",
    "shipped": "Відправлено",
    "delivered": "Доставлено",
    "cancelled": "Скасовано"
}

