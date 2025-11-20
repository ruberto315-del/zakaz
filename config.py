import os
from dotenv import load_dotenv

load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN", "8264290134:AAGdDjDFrwYxrrHqDw3Fbj1FjwGg9g30Mhs")

# ID адміністратора (основний)
ADMIN_ID = int(os.getenv("ADMIN_ID", "810944378"))

# Список ID адміністраторів
ADMIN_IDS = [
    ADMIN_ID,
    356379093,  # Другий адміністратор
    459423008,  # Третій адміністратор
    592109708   # Четвертий адміністратор
]

# Username адміністратора для зв'язку
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "testusername")

# Підключення до PostgreSQL
# Railway надає DATABASE_URL або окремі змінні
DATABASE_URL = os.getenv("DATABASE_URL")

# Окремі параметри для підключення до PostgreSQL (якщо DATABASE_URL не встановлено)
# Railway використовує POSTGRES_USER замість PGUSER
PGUSER = os.getenv("POSTGRES_USER") or os.getenv("PGUSER", "postgres")
PGPASSWORD = os.getenv("POSTGRES_PASSWORD", "") or os.getenv("PGPASSWORD", "")
PGHOST = os.getenv("RAILWAY_PRIVATE_DOMAIN") or os.getenv("PGHOST", "localhost")
PGPORT = os.getenv("PGPORT", "5432")
PGDATABASE = os.getenv("POSTGRES_DB") or os.getenv("PGDATABASE", "railway")

# Словник з параметрами для підключення (для використання з asyncpg.create_pool)
DB_CONFIG = {
    'user': "postgres",
    'password': "mptRpMNbdRfqtERUEaYMsDOcwkCgSgyf",
    'database': "railway",
    'host': "postgres.railway.internal",
    'port': "5432",
}

# Якщо DATABASE_URL не встановлено, але є окремі параметри, створюємо DATABASE_URL
# Але тільки якщо DB_CONFIG не заповнений (для сумісності зі старим кодом)
if not DATABASE_URL and not (DB_CONFIG.get('password') and DB_CONFIG.get('host')):
    if PGPASSWORD and PGHOST:
        DATABASE_URL = f"postgresql://{PGUSER}:{PGPASSWORD}@{PGHOST}:{PGPORT}/{PGDATABASE}"

# Визначаємо чи використовувати PostgreSQL
# Якщо DATABASE_URL встановлено або є параметри підключення, використовуємо PostgreSQL
USE_POSTGRES_ENV = os.getenv("USE_POSTGRES", "").lower()
if USE_POSTGRES_ENV in ("true", "1", "yes"):
    USE_POSTGRES = True
elif USE_POSTGRES_ENV in ("false", "0", "no"):
    USE_POSTGRES = False
else:
    # Автоматично визначаємо на основі наявності параметрів
    # Перевіряємо чи DB_CONFIG заповнений (має password та host)
    db_config_filled = bool(DB_CONFIG.get('password') and DB_CONFIG.get('host') and DB_CONFIG.get('host') != 'localhost')
    USE_POSTGRES = bool(DATABASE_URL or (PGPASSWORD and PGHOST and PGHOST != "localhost") or db_config_filled)

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

