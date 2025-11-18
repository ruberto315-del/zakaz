import os
from dotenv import load_dotenv

load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN", "8264290134:AAGdDjDFrwYxrrHqDw3Fbj1FjwGg9g30Mhs")

# ID адміністратора
ADMIN_ID = int(os.getenv("ADMIN_ID", "810944378"))

# Підключення до PostgreSQL
# Railway надає DATABASE_URL або окремі змінні
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Якщо DATABASE_URL не встановлено, використовуємо окремі змінні
    PGUSER = os.getenv("PGUSER", "postgres")
    PGPASSWORD = os.getenv("POSTGRES_PASSWORD", "")
    PGHOST = os.getenv("RAILWAY_PRIVATE_DOMAIN") or os.getenv("PGHOST", "localhost")
    PGPORT = os.getenv("PGPORT", "5432")
    PGDATABASE = os.getenv("POSTGRES_DB") or os.getenv("PGDATABASE", "railway")
    if PGPASSWORD and PGHOST != "localhost":
        DATABASE_URL = f"postgresql://{PGUSER}:{PGPASSWORD}@{PGHOST}:{PGPORT}/{PGDATABASE}"

# Визначаємо чи використовувати PostgreSQL
# Якщо DATABASE_URL встановлено, автоматично використовуємо PostgreSQL
USE_POSTGRES = os.getenv("USE_POSTGRES", "true" if DATABASE_URL else "false").lower() == "true"
DATABASE_NAME = "shop_bot.db"  # Використовується тільки для SQLite

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

