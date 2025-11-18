"""
Модуль для відправки сповіщень користувачам про зміни статусів замовлень
"""
from aiogram import Bot
from database import db
from config import BOT_TOKEN, ORDER_STATUSES

async def send_order_status_notification(user_id: int, order_id: int, status: str):
    """Відправити сповіщення про зміну статусу замовлення"""
    bot = Bot(token=BOT_TOKEN)
    
    try:
        order = await db.get_order(order_id)
        if not order:
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
        
        await bot.send_message(user_id, message, parse_mode="HTML")
    except Exception as e:
        print(f"Помилка відправки сповіщення: {e}")
    finally:
        await bot.session.close()

async def send_preorder_notification(user_id: int, preorder_id: int, product_name: str):
    """Відправити сповіщення про готовність предзаказу"""
    bot = Bot(token=BOT_TOKEN)
    
    try:
        message = f"📋 <b>Предзаказ готовий!</b>\n\n"
        message += f"Товар: <b>{product_name}</b>\n"
        message += f"Ваш предзаказ #{preorder_id} готовий до оформлення.\n\n"
        message += "Перейдіть в розділ 'Предзакази' для оформлення замовлення."
        
        await bot.send_message(user_id, message, parse_mode="HTML")
    except Exception as e:
        print(f"Помилка відправки сповіщення: {e}")
    finally:
        await bot.session.close()

