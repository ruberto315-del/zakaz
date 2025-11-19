from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards import get_orders_keyboard, get_main_menu
from database import db
from config import ORDER_STATUSES, ADMIN_ID, ADMIN_USERNAME

router = Router()

class OrderStates(StatesGroup):
    waiting_phone = State()
    waiting_address = State()
    waiting_receipt = State()

@router.callback_query(F.data == "checkout")
async def start_checkout(callback: CallbackQuery, state: FSMContext):
    """Почати оформлення замовлення"""
    user_id = callback.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        await callback.answer("Корзина порожня", show_alert=True)
        return
    
    user = await db.get_user(user_id)
    
    if user and user.get('phone'):
        await callback.message.answer(
            f"📞 Ваш номер телефону: {user['phone']}\n\n"
            "Відправте новий номер телефону або натисніть /skip щоб залишити поточний:"
        )
    else:
        await callback.message.answer(
            "📞 Введіть ваш номер телефону для замовлення:"
        )
    
    await state.set_state(OrderStates.waiting_phone)
    await callback.answer()

@router.message(OrderStates.waiting_phone)
async def process_phone(message: Message, state: FSMContext):
    """Обробити номер телефону"""
    phone = message.text.strip()
    
    if message.text == "/skip":
        user = await db.get_user(message.from_user.id)
        phone = user.get('phone') if user else None
    
    if not phone:
        await message.answer("Будь ласка, введіть номер телефону:")
        return
    
    await state.update_data(phone=phone)
    await db.update_user_data(message.from_user.id, phone=phone)
    
    user = await db.get_user(message.from_user.id)
    if user and user.get('address'):
        await message.answer(
            f"📍 Ваша адреса: {user['address']}\n\n"
            "Відправте нову адресу або натисніть /skip щоб залишити поточну:"
        )
    else:
        await message.answer("📍 Введіть адресу доставки:")
    
    await state.set_state(OrderStates.waiting_address)

@router.message(OrderStates.waiting_address)
async def process_address(message: Message, state: FSMContext):
    """Обробити адресу"""
    # Перевірка на команду /skip
    if message.text and message.text.strip() == "/skip":
        user = await db.get_user(message.from_user.id)
        address = user.get('address') if user else None
    else:
        # Отримуємо адресу з повідомлення
        if not message.text:
            await message.answer("Будь ласка, введіть адресу доставки або надішліть /skip:")
            return
        address = message.text.strip()
    
    if not address:
        await message.answer("Будь ласка, введіть адресу доставки:")
        return
    
    await state.update_data(address=address)
    await db.update_user_data(message.from_user.id, address=address)
    
    # Підрахувати загальну суму
    user_id = message.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        await message.answer("❌ Ваша корзина порожня. Додайте товари перед оформленням замовлення.")
        await state.clear()
        return
    
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    
    data = await state.get_data()
    phone = data.get('phone')
    
    if not phone:
        await message.answer("❌ Помилка: номер телефону не знайдено. Спробуйте оформити замовлення ще раз.")
        await state.clear()
        return
    
    # Створити замовлення
    try:
        order_id = await db.create_order(user_id, total, phone, address)
        
        # Отримати деталі замовлення для відправки адміну
        order = await db.get_order(order_id)
        order_items = await db.get_order_items(order_id)
        user = await db.get_user(user_id)
        
        # Відправити повідомлення користувачу
        admin_username_display = ADMIN_USERNAME if ADMIN_USERNAME.startswith('@') else f"@{ADMIN_USERNAME}"
        await message.answer(
            f"✅ Замовлення #{order_id} створено!\n\n"
            f"📞 Телефон: {phone}\n"
            f"📍 Адреса: {address}\n"
            f"💰 Сума: {total} грн\n\n"
            f"📞 Для оплати та уточнення деталей зв'яжіться з адміністратором: {admin_username_display}"
        )
        
        # Відправити повідомлення адміністратору
        bot = message.bot
        admin_text = f"🆕 <b>Нове замовлення #{order_id}</b>\n\n"
        admin_text += f"👤 <b>Користувач:</b>\n"
        admin_text += f"   ID: <code>{user_id}</code>\n"
        if user:
            admin_text += f"   Ім'я: {user.get('first_name', 'Не вказано')}\n"
            if user.get('username'):
                admin_text += f"   @{user['username']}\n"
        admin_text += f"\n📞 <b>Телефон:</b> {phone}\n"
        admin_text += f"📍 <b>Адреса:</b> {address}\n\n"
        admin_text += f"<b>Товари:</b>\n"
        for item in order_items:
            admin_text += f"• {item['name']} - {item['quantity']} шт. × {item['price']} грн\n"
        admin_text += f"\n💰 <b>Загалом: {total} грн</b>"
        
        try:
            await bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Помилка відправки повідомлення адміну: {e}")
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Помилка створення замовлення: {e}", exc_info=True)
        await message.answer(
            "❌ Помилка при створенні замовлення. Будь ласка, спробуйте ще раз або зверніться до адміністратора."
        )
    
    await state.clear()

@router.message(F.text == "📦 Мої замовлення")
async def show_orders(message: Message):
    """Показати замовлення користувача"""
    user_id = message.from_user.id
    orders = await db.get_orders(user_id)
    
    if not orders:
        await message.answer("📦 У вас немає замовлень")
        return
    
    keyboard = get_orders_keyboard(orders)
    await message.answer(
        "📦 <b>Ваші замовлення:</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("order_"))
async def show_order(callback: CallbackQuery):
    """Показати деталі замовлення"""
    order_id = int(callback.data.split("_")[1])
    order = await db.get_order(order_id)
    
    if not order:
        await callback.answer("Замовлення не знайдено", show_alert=True)
        return
    
    items = await db.get_order_items(order_id)
    
    status_text = ORDER_STATUSES.get(order['status'], order['status'])
    
    text = f"📦 <b>Замовлення #{order_id}</b>\n\n"
    text += f"Статус: {status_text}\n"
    text += f"📞 Телефон: {order['phone']}\n"
    text += f"📍 Адреса: {order['address']}\n\n"
    text += "<b>Товари:</b>\n"
    
    for item in items:
        text += f"• {item['name']} - {item['quantity']} шт. × {item['price']} грн\n"
    
    text += f"\n<b>Загалом: {order['total_price']} грн</b>"
    
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("attach_receipt_"))
async def attach_receipt(callback: CallbackQuery, state: FSMContext):
    """Прикріпити чек"""
    order_id = int(callback.data.split("_")[-1])
    await state.update_data(order_id=order_id)
    await state.set_state(OrderStates.waiting_receipt)
    
    await callback.message.answer(
        "📸 Будь ласка, надішліть фото чека:"
    )
    await callback.answer()

@router.message(OrderStates.waiting_receipt, F.photo)
async def process_receipt(message: Message, state: FSMContext):
    """Обробити чек"""
    data = await state.get_data()
    order_id = data.get('order_id')
    
    if not order_id:
        await message.answer("Помилка. Спробуйте ще раз.")
        await state.clear()
        return
    
    photo_id = message.photo[-1].file_id
    
    # Оновити замовлення з фото чека
    order = await db.get_order(order_id)
    if order:
        # Оновлюємо через метод бази даних
        if db.use_postgres:
            async with db.pool.acquire() as conn:
                await conn.execute(
                    "UPDATE orders SET receipt_photo_id = $1 WHERE id = $2",
                    photo_id, order_id
                )
        else:
            try:
                import aiosqlite
            except ImportError:
                await message.answer("Помилка: aiosqlite не встановлено")
                await state.clear()
                return
            from config import DATABASE_NAME
            async with aiosqlite.connect(DATABASE_NAME) as conn:
                await conn.execute(
                    "UPDATE orders SET receipt_photo_id = ? WHERE id = ?",
                    (photo_id, order_id)
                )
                await conn.commit()
        
        # Відправити чек адміністратору
        bot = message.bot
        order_items = await db.get_order_items(order_id)
        user = await db.get_user(order['user_id'])
        
        admin_text = f"📸 <b>Чек для замовлення #{order_id}</b>\n\n"
        admin_text += f"👤 <b>Користувач:</b>\n"
        admin_text += f"   ID: <code>{order['user_id']}</code>\n"
        if user:
            admin_text += f"   Ім'я: {user.get('first_name', 'Не вказано')}\n"
            if user.get('username'):
                admin_text += f"   @{user['username']}\n"
        admin_text += f"\n📞 <b>Телефон:</b> {order['phone']}\n"
        admin_text += f"📍 <b>Адреса:</b> {order['address']}\n\n"
        admin_text += f"<b>Товари:</b>\n"
        for item in order_items:
            admin_text += f"• {item['name']} - {item['quantity']} шт. × {item['price']} грн\n"
        admin_text += f"\n💰 <b>Загалом: {order['total_price']} грн</b>"
        
        try:
            # Відправляємо фото з описом адміну
            await bot.send_photo(
                ADMIN_ID,
                photo_id,
                caption=admin_text,
                parse_mode="HTML"
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Помилка відправки чека адміну: {e}")
    
    await message.answer(
        "✅ Чек прикріплено до замовлення!\n\n"
        "Ваше замовлення буде оброблено найближчим часом."
    )
    
    await state.clear()


