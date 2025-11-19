import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from database import db
from handlers import (
    common, catalog, cart, orders, preorders,
    admin, contact, comment_orders
)

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Головна функція"""
    try:
        # Ініціалізація бота та диспетчера
        bot = Bot(token=BOT_TOKEN)
        dp = Dispatcher(storage=MemoryStorage())
        
        # Реєстрація роутерів
        dp.include_router(common.router)
        dp.include_router(catalog.router)
        dp.include_router(cart.router)
        dp.include_router(orders.router)
        dp.include_router(preorders.router)
        dp.include_router(admin.router)
        dp.include_router(contact.router)
        dp.include_router(comment_orders.router)
        
        # Ініціалізація бази даних
        await db.init_db()
        logger.info("База даних ініціалізована")
        
        # Запуск бота
        logger.info("Бот запущено")
        await dp.start_polling(bot, skip_updates=True)
    finally:
        # Закрити підключення до БД
        await db.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот зупинено")

