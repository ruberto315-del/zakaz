"""
Обробник для збору замовлень з коментарів до постів
"""
import re
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from database import db
from config import ADMIN_ID, ADMIN_IDS

logger = logging.getLogger(__name__)
router = Router()

def is_admin(user_id: int) -> bool:
    """Перевірити чи користувач адміністратор"""
    return user_id in ADMIN_IDS

def extract_position_numbers(text: str) -> list:
    """Витягнути номери позицій з тексту
    
    Повертає список чисел - номери позицій
    """
    # Шукаємо всі числа в тексті
    numbers = re.findall(r'\d+', text)
    return [int(n) for n in numbers if n.isdigit()]

def extract_positions_with_quantity(text: str) -> dict:
    """Витягнути позиції з кількістю з тексту
    
    Підтримує формати:
    - "5" -> позиція 5, кількість 1
    - "5 x2" або "5 2" -> позиція 5, кількість 2
    - "5, 6, 7" -> позиції 5, 6, 7, кожна кількість 1
    
    Повертає словник: {номер_позиції: кількість}
    """
    positions = {}
    text = text.strip()
    
    # Спроба знайти формат "номер xкількість" або "номер кількість"
    pattern = r'(\d+)\s*(?:[xх×]\s*)?(\d+)?'
    matches = re.findall(pattern, text)
    
    for match in matches:
        pos_num = int(match[0])
        quantity = int(match[1]) if match[1] else 1
        # Якщо позиція вже є, додаємо кількість
        if pos_num in positions:
            positions[pos_num] += quantity
        else:
            positions[pos_num] = quantity
    
    # Якщо не знайдено жодного збігу, спробуємо просто знайти всі числа
    if not positions:
        numbers = re.findall(r'\d+', text)
        for num in numbers:
            pos_num = int(num)
            if pos_num not in positions:
                positions[pos_num] = 1
            else:
                positions[pos_num] += 1
    
    return positions

@router.message(F.reply_to_message)
async def handle_comment(message: Message):
    """Обробка коментарів до постів"""
    try:
        # Перевіряємо чи це коментар до поста
        if not message.reply_to_message:
            return
        
        reply_to = message.reply_to_message
        chat_id = message.chat.id
        user_id = message.from_user.id
        text = message.text or ""
        text_lower = text.lower().strip()
        
        # Перевіряємо команди адміністратора
        if is_admin(user_id):
            # Команда "старт" - почати збір замовлень
            if text_lower in ["старт", "start", "/старт", "/start"]:
                post_message_id = reply_to.message_id
                post_id = await db.start_post_collection(post_message_id, chat_id, user_id)
                await message.reply(
                    f"✅ Збір замовлень розпочато!\n\n"
                    f"Покупатели можуть писати номери позицій в коментарях.\n"
                    f"Для завершення напишіть 'фініш' або 'finish'."
                )
                logger.info(f"Почато збір замовлень для поста {post_message_id} в чаті {chat_id}")
                return
            
            # Команда "фініш" - завершити збір замовлень
            if text_lower in ["фініш", "finish", "/фініш", "/finish"]:
                post_message_id = reply_to.message_id
                active_post = await db.get_active_post(post_message_id, chat_id)
                
                if not active_post:
                    await message.reply("❌ Активний збір замовлень для цього поста не знайдено.")
                    return
                
                # Завершуємо збір
                await db.finish_post_collection(post_message_id, chat_id)
                
                # Отримуємо всі замовлення
                orders = await db.get_comment_orders(active_post['id'])
                summary = await db.get_comment_orders_summary(active_post['id'])
                
                if not orders:
                    await message.reply("📋 Замовлень не знайдено.")
                    return
                
                # Формуємо підсумок
                summary_text = "📋 <b>Підсумок замовлень:</b>\n\n"
                
                # Групуємо по позиціях
                summary_text += "<b>За позиціями:</b>\n"
                for item in summary:
                    summary_text += f"Позиція {item['position_number']}: {item['total_quantity']} шт. ({item['unique_users']} покупців)\n"
                
                summary_text += "\n<b>Деталі по покупцях:</b>\n"
                
                # Групуємо по користувачах
                user_orders = {}
                for order in orders:
                    user_id_key = order['user_id']
                    if user_id_key not in user_orders:
                        username = order.get('username') or order.get('first_name') or f"ID: {user_id_key}"
                        user_orders[user_id_key] = {
                            'username': username,
                            'positions': []
                        }
                    user_orders[user_id_key]['positions'].append({
                        'number': order['position_number'],
                        'quantity': order['quantity']
                    })
                
                for user_id_key, user_data in user_orders.items():
                    positions_str = ", ".join([f"#{p['number']} ({p['quantity']} шт.)" for p in user_data['positions']])
                    summary_text += f"\n👤 {user_data['username']}:\n   {positions_str}"
                
                summary_text += f"\n\n📊 Всього замовлень: {len(orders)}"
                summary_text += f"\n👥 Унікальних покупців: {len(user_orders)}"
                
                await message.reply(summary_text, parse_mode="HTML")
                logger.info(f"Завершено збір замовлень для поста {post_message_id}, знайдено {len(orders)} замовлень")
                return
        
        # Обробка замовлень від покупців
        # Перевіряємо чи є активний збір для цього поста
        post_message_id = reply_to.message_id
        active_post = await db.get_active_post(post_message_id, chat_id)
        
        if not active_post:
            # Якщо немає активного збору, ігноруємо
            return
        
        # Витягуємо позиції з кількістю з коментаря
        positions_with_qty = extract_positions_with_quantity(text)
        
        if not positions_with_qty:
            # Якщо немає позицій, ігноруємо
            return
        
        # Додаємо користувача в базу, якщо його немає
        is_new_user = await db.add_user(
            user_id,
            username=message.from_user.username,
            first_name=message.from_user.first_name
        )
        
        # Відправити сповіщення адміну про нового користувача
        if is_new_user:
            bot = message.bot
            username = message.from_user.username
            first_name = message.from_user.first_name
            
            admin_text = "🆕 <b>Новий користувач зареєстрований!</b>\n\n"
            # Використовуємо <code> для ID, щоб його можна було скопіювати
            admin_text += f"🆔 ID: <code>{user_id}</code>\n"
            
            # Додаємо username або ім'я або тільки ID
            if username:
                admin_text += f"👤 Username: @{username}\n"
            elif first_name:
                admin_text += f"👤 Ім'я: {first_name}\n"
            # ID завжди виводиться, тому додаткового тексту не потрібно
            
            try:
                await bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML")
            except Exception as e:
                logger.error(f"Помилка відправки сповіщення про нового користувача адміну: {e}")
        
        # Додаємо замовлення для кожної позиції
        added_orders = []
        for pos_num, quantity in positions_with_qty.items():
            order_id = await db.add_comment_order(
                post_id=active_post['id'],
                user_id=user_id,
                position_number=pos_num,
                quantity=quantity,
                comment_message_id=message.message_id
            )
            added_orders.append(f"#{pos_num} ({quantity} шт.)" if quantity > 1 else f"#{pos_num}")
        
        if added_orders:
            positions_str = ", ".join(added_orders)
            await message.reply(
                f"✅ Ваші замовлення прийнято: {positions_str}\n\n"
                f"Очікуйте підтвердження від адміністратора."
            )
            logger.info(f"Додано замовлення від користувача {user_id}: {positions_with_qty}")
    
    except Exception as e:
        logger.error(f"Помилка обробки коментаря: {e}", exc_info=True)
        # Не відповідаємо на помилку, щоб не спамити

