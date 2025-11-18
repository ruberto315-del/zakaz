"""
Модуль для відправки сповіщень користувачам про зміни статусів замовлень
"""
import logging
from aiogram import Bot
from database import db
from config import ORDER_STATUSES

logger = logging.getLogger(__name__)

async def send_order_status_notification(bot: Bot, user_id: int, order_id: int, status: str):
    """Відправити сповіщення про зміну статусу замовлення"""
    try:
        order = await db.get_order(order_id)
        if not order:
            logger.warning(f"Замовлення {order_id} не знайдено для сповіщення")
            return
        
        status_text = ORDER_STATUSES.get(status, status)
        
        message = f"📦 <b>Оновлення замовлення #{order_id}</b>\n\n"
        message += f"Статус змінено на: <b>{status_text}</b>\n\n"
        
        if status == "shipped":
            message += "Ваше замовлення відправлено! Очікуйте доставку."
        elif status == "delivered":
            message += "Ваше замовлення доставлено! Дякуємо за покупку!"
        elif status == "ready":
            message += "Ваше замовлення готове до відправки!"
        elif status == "cancelled":
            message += "Ваше замовлення скасовано. Якщо у вас виникли питання, зверніться до адміністратора."
        elif status == "processing":
            message += "Ваше замовлення прийнято в обробку."
        
        await bot.send_message(user_id, message, parse_mode="HTML")
        logger.info(f"Сповіщення відправлено користувачу {user_id} про замовлення {order_id}, статус: {status}")
    except Exception as e:
        logger.error(f"Помилка відправки сповіщення користувачу {user_id} про замовлення {order_id}: {e}", exc_info=True)

async def send_preorder_notification(bot: Bot, user_id: int, preorder_id: int, product_name: str):
    """Відправити сповіщення про готовність предзаказу"""
    try:
        message = f"📋 <b>Предзаказ готовий!</b>\n\n"
        message += f"Товар: <b>{product_name}</b>\n"
        message += f"Ваш предзаказ #{preorder_id} готовий до оформлення.\n\n"
        message += "Перейдіть в розділ 'Предзакази' для оформлення замовлення."
        
        await bot.send_message(user_id, message, parse_mode="HTML")
        logger.info(f"Сповіщення про предзаказ {preorder_id} відправлено користувачу {user_id}")
    except Exception as e:
        logger.error(f"Помилка відправки сповіщення про предзаказ {preorder_id} користувачу {user_id}: {e}", exc_info=True)

