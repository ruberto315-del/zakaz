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
    # Спробуємо створити DATABASE_URL якщо є всі необхідні змінні
    if PGPASSWORD and PGHOST and PGHOST != "localhost":
        DATABASE_URL = f"postgresql://{PGUSER}:{PGPASSWORD}@{PGHOST}:{PGPORT}/{PGDATABASE}"
    elif PGPASSWORD:  # Якщо є пароль, навіть якщо localhost, спробуємо підключитися
        DATABASE_URL = f"postgresql://{PGUSER}:{PGPASSWORD}@{PGHOST}:{PGPORT}/{PGDATABASE}"

# Визначаємо чи використовувати PostgreSQL
# Якщо DATABASE_URL встановлено, автоматично використовуємо PostgreSQL
# Якщо USE_POSTGRES явно встановлено в змінних оточення, використовуємо його
USE_POSTGRES_ENV = os.getenv("USE_POSTGRES", "").lower()
if USE_POSTGRES_ENV in ("true", "1", "yes"):
    USE_POSTGRES = True
elif USE_POSTGRES_ENV in ("false", "0", "no"):
    USE_POSTGRES = False
else:
    # Автоматично визначаємо на основі DATABASE_URL
    USE_POSTGRES = bool(DATABASE_URL)

DATABASE_NAME = "shop_bot.db"  # Використовується тільки для SQLite

# Логування для діагностики (тільки якщо є logging)
try:
    import logging
    logger = logging.getLogger(__name__)
    # Логуємо тільки якщо DATABASE_URL не встановлено, щоб не показувати пароль
    if DATABASE_URL:
        logger.info(f"Config: DATABASE_URL встановлено, USE_POSTGRES={USE_POSTGRES}")
    else:
        logger.warning(f"Config: DATABASE_URL не встановлено, USE_POSTGRES={USE_POSTGRES}")
        # Спробуємо показати які змінні є (без паролів)
        pg_vars = {
            "PGUSER": os.getenv("PGUSER"),
            "POSTGRES_PASSWORD": "***" if os.getenv("POSTGRES_PASSWORD") else None,
            "RAILWAY_PRIVATE_DOMAIN": os.getenv("RAILWAY_PRIVATE_DOMAIN"),
            "PGHOST": os.getenv("PGHOST"),
            "PGPORT": os.getenv("PGPORT"),
            "POSTGRES_DB": os.getenv("POSTGRES_DB"),
            "PGDATABASE": os.getenv("PGDATABASE"),
        }
        logger.warning(f"Доступні змінні PostgreSQL: {pg_vars}")
except:
    pass

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

