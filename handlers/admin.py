from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from keyboards import (
    get_admin_menu, get_admin_orders_keyboard, get_order_status_keyboard,
    get_admin_products_keyboard, get_product_edit_keyboard, get_main_menu,
    get_cancel_add_product_keyboard
)
from database import db
from config import ADMIN_ID, ORDER_STATUSES
from notifications import send_order_status_notification
import logging

logger = logging.getLogger(__name__)

router = Router()

class AdminStates(StatesGroup):
    adding_product_name = State()
    adding_product_description = State()
    adding_product_price = State()
    adding_product_photo = State()
    adding_product_category = State()
    editing_product_name = State()
    editing_product_description = State()
    editing_product_price = State()
    editing_product_photo = State()

def is_admin(user_id: int) -> bool:
    """Перевірити чи користувач адмін"""
    return user_id == ADMIN_ID


@router.message(F.text == "➕ Додати товар")
async def start_adding_product(message: Message, state: FSMContext):
    """Почати додавання товару"""
    if not is_admin(message.from_user.id):
        return
    
    keyboard = get_cancel_add_product_keyboard()
    await message.answer("Введіть назву товару:", reply_markup=keyboard)
    await state.set_state(AdminStates.adding_product_name)

@router.message(AdminStates.adding_product_name)
async def process_product_name(message: Message, state: FSMContext):
    """Обробити назву товару"""
    await state.update_data(name=message.text)
    keyboard = get_cancel_add_product_keyboard()
    await message.answer("Введіть опис товару:", reply_markup=keyboard)
    await state.set_state(AdminStates.adding_product_description)

@router.message(AdminStates.adding_product_description)
async def process_product_description(message: Message, state: FSMContext):
    """Обробити опис товару"""
    await state.update_data(description=message.text)
    keyboard = get_cancel_add_product_keyboard()
    await message.answer("Введіть ціну товару (тільки число):", reply_markup=keyboard)
    await state.set_state(AdminStates.adding_product_price)

@router.message(AdminStates.adding_product_price)
async def process_product_price(message: Message, state: FSMContext):
    """Обробити ціну товару"""
    try:
        price = float(message.text.replace(",", "."))
        await state.update_data(price=price)
        keyboard = get_cancel_add_product_keyboard()
        await message.answer("Введіть категорію товару (або /skip щоб пропустити):", reply_markup=keyboard)
        await state.set_state(AdminStates.adding_product_category)
    except ValueError:
        keyboard = get_cancel_add_product_keyboard()
        await message.answer("Будь ласка, введіть коректну ціну (тільки число):", reply_markup=keyboard)

@router.message(AdminStates.adding_product_category)
async def process_product_category(message: Message, state: FSMContext):
    """Обробити категорію товару"""
    category = message.text.strip() if message.text != "/skip" else None
    await state.update_data(category=category)
    keyboard = get_cancel_add_product_keyboard()
    await message.answer("Надішліть фото товару:", reply_markup=keyboard)
    await state.set_state(AdminStates.adding_product_photo)

@router.message(AdminStates.adding_product_photo, F.photo)
async def process_product_photo(message: Message, state: FSMContext):
    """Обробити фото товару"""
    photo_id = message.photo[-1].file_id
    data = await state.get_data()
    
    # Зберігаємо file_id від Telegram
    product_id = await db.add_product(
        name=data['name'],
        description=data['description'],
        price=data['price'],
        photo_id=photo_id,  # Зберігаємо file_id від Telegram
        category=data.get('category')
    )
    
    await message.answer(
        f"✅ Товар додано!\n\n"
        f"ID: {product_id}\n"
        f"Назва: {data['name']}\n"
        f"Ціна: {data['price']} грн",
        reply_markup=None
    )
    
    await state.clear()

@router.callback_query(F.data == "cancel_add_product")
async def cancel_add_product(callback: CallbackQuery, state: FSMContext):
    """Скасувати додавання товару"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ заборонено", show_alert=True)
        return
    
    await state.clear()
    await callback.message.edit_text("❌ Додавання товару скасовано.")
    await callback.answer("Додавання скасовано")

@router.message(F.text == "🛍️ Переглянути товари")
async def show_all_products(message: Message):
    """Показати всі товари для перегляду"""
    if not is_admin(message.from_user.id):
        return
    
    products = await db.get_products(available_only=False)
    
    if not products:
        await message.answer("Товарів не знайдено")
        return
    
    keyboard = get_admin_products_keyboard(products, page=0, action="view")
    await message.answer(
        "🛍️ <b>Всі товари:</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@router.message(F.text == "📝 Редагувати товар")
async def show_products_for_edit(message: Message):
    """Показати товари для редагування"""
    if not is_admin(message.from_user.id):
        return
    
    products = await db.get_products(available_only=False)
    
    if not products:
        await message.answer("Товарів не знайдено")
        return
    
    keyboard = get_admin_products_keyboard(products, page=0, action="edit")
    await message.answer(
        "📝 <b>Оберіть товар для редагування:</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@router.message(F.text == "🗑️ Видалити товар")
async def show_products_for_delete(message: Message):
    """Показати товари для видалення"""
    if not is_admin(message.from_user.id):
        return
    
    products = await db.get_products(available_only=False)
    
    if not products:
        await message.answer("Товарів не знайдено")
        return
    
    keyboard = get_admin_products_keyboard(products, page=0, action="delete")
    await message.answer(
        "🗑️ <b>Оберіть товар для видалення:</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("admin_products_page_"))
async def admin_products_page(callback: CallbackQuery):
    """Пагінація товарів для адміна"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ заборонено", show_alert=True)
        return
    
    parts = callback.data.split("_")
    page = int(parts[3])
    action = parts[4] if len(parts) > 4 else "edit"
    
    products = await db.get_products(available_only=False)
    keyboard = get_admin_products_keyboard(products, page=page, action=action)
    
    action_texts = {
        "edit": "редагування",
        "delete": "видалення",
        "view": "перегляду"
    }
    action_text = action_texts.get(action, "перегляду")
    emoji = "📝" if action == "edit" else "🗑️" if action == "delete" else "🛍️"
    
    # Якщо повідомлення містить фото, видаляємо його і відправляємо нове
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(
            f"{emoji} <b>Оберіть товар для {action_text}:</b>",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        try:
            await callback.message.edit_text(
                f"{emoji} <b>Оберіть товар для {action_text}:</b>",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        except Exception:
            # Якщо не вдалося відредагувати, видаляємо і відправляємо нове
            await callback.message.delete()
            await callback.message.answer(
                f"{emoji} <b>Оберіть товар для {action_text}:</b>",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_product_"))
async def show_product_edit_options(callback: CallbackQuery):
    """Показати опції редагування товару"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ заборонено", show_alert=True)
        return
    
    parts = callback.data.split("_")
    product_id = int(parts[2])
    action = parts[3] if len(parts) > 3 else "edit"
    
    product = await db.get_product(product_id)
    
    if not product:
        await callback.answer("Товар не знайдено", show_alert=True)
        return
    
    if action == "view":
        # Просто перегляд товару
        text = f"🛍️ <b>{product['name']}</b>\n\n"
        if product['description']:
            text += f"{product['description']}\n\n"
        text += f"💰 Ціна: <b>{product['price']} грн</b>\n"
        text += f"Доступність: {'✅' if product['is_available'] else '❌'}\n"
        if product.get('category'):
            text += f"Категорія: {product['category']}\n"
        
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="🔙 До товарів", callback_data="admin_products_page_0_view"))
        builder.adjust(1)
        
        if product['photo_id'] and not product['photo_id'].startswith('http'):
            await callback.message.delete()
            try:
                await callback.message.answer_photo(
                    product['photo_id'],
                    caption=text,
                    reply_markup=builder.as_markup(),
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Помилка відправки фото: {e}")
                await callback.message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
        else:
            if callback.message.photo:
                await callback.message.delete()
            await callback.message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
        await callback.answer()
        return
    
    if action == "delete":
        # Підтвердження видалення
        text = f"🗑️ <b>Видалити товар?</b>\n\n"
        text += f"ID: {product_id}\n"
        text += f"Назва: {product['name']}\n"
        text += f"Ціна: {product['price']} грн\n\n"
        text += "Цю дію неможливо скасувати!"
        
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="✅ Так, видалити", callback_data=f"confirm_delete_{product_id}"))
        builder.add(InlineKeyboardButton(text="❌ Скасувати", callback_data="admin_products_page_0_delete"))
        builder.adjust(2)
        
        # Перевіряємо чи повідомлення містить фото
        if callback.message.photo:
            await callback.message.delete()
        
        if product['photo_id'] and not product['photo_id'].startswith('http'):
            # Це file_id від Telegram - відправляємо фото
            try:
                await callback.message.answer_photo(
                    product['photo_id'],
                    caption=text,
                    reply_markup=builder.as_markup(),
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Помилка відправки фото: {e}")
                # Якщо не вдалося відправити фото, відправляємо тільки текст
                await callback.message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
        else:
            # Немає фото або це URL (не відправляємо через URL)
            await callback.message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
        await callback.answer()
        return
    
    # Редагування
    text = f"📝 <b>Редагування товару</b>\n\n"
    text += f"ID: {product_id}\n"
    text += f"Назва: {product['name']}\n"
    text += f"Опис: {product['description']}\n"
    text += f"Ціна: {product['price']} грн\n"
    text += f"Доступність: {'✅' if product['is_available'] else '❌'}\n"
    
    keyboard = get_product_edit_keyboard(product_id)
    
    if product['photo_id']:
        await callback.message.delete()
        # Перевіряємо чи це URL (для сумісності зі старими даними) або file_id
        if product['photo_id'].startswith('http'):
            # Це URL (для сумісності зі старими даними)
            await callback.message.answer_photo(
                product['photo_id'],
                caption=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            # Це file_id від Telegram
            await callback.message.answer_photo(
                product['photo_id'],
                caption=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
    else:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    
    await callback.answer()

@router.callback_query(F.data.startswith("edit_name_"))
async def edit_product_name(callback: CallbackQuery, state: FSMContext):
    """Редагувати назву товару"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ заборонено", show_alert=True)
        return
    
    product_id = int(callback.data.split("_")[-1])
    await state.update_data(product_id=product_id)
    await state.set_state(AdminStates.editing_product_name)
    
    await callback.message.answer("Введіть нову назву товару:")
    await callback.answer()

@router.callback_query(F.data.startswith("edit_desc_"))
async def edit_product_description(callback: CallbackQuery, state: FSMContext):
    """Редагувати опис товару"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ заборонено", show_alert=True)
        return
    
    product_id = int(callback.data.split("_")[-1])
    await state.update_data(product_id=product_id)
    await state.set_state(AdminStates.editing_product_description)
    
    await callback.message.answer("Введіть новий опис товару:")
    await callback.answer()

@router.message(AdminStates.editing_product_description)
async def process_edit_description(message: Message, state: FSMContext):
    """Обробити новий опис"""
    data = await state.get_data()
    product_id = data['product_id']
    await db.update_product(product_id, description=message.text)
    await message.answer("✅ Опис оновлено!")
    await state.clear()

@router.callback_query(F.data.startswith("edit_photo_"))
async def edit_product_photo(callback: CallbackQuery, state: FSMContext):
    """Редагувати фото товару"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ заборонено", show_alert=True)
        return
    
    product_id = int(callback.data.split("_")[-1])
    await state.update_data(product_id=product_id)
    await state.set_state(AdminStates.editing_product_photo)
    
    await callback.message.answer("Надішліть нове фото товару:")
    await callback.answer()

@router.message(AdminStates.editing_product_photo, F.photo)
async def process_edit_photo(message: Message, state: FSMContext):
    """Обробити нове фото"""
    photo_id = message.photo[-1].file_id
    data = await state.get_data()
    product_id = data['product_id']
    
    # Зберігаємо file_id від Telegram
    await db.update_product(product_id, photo_id=photo_id)
    await message.answer("✅ Фото оновлено!")
    await state.clear()

@router.message(AdminStates.editing_product_name)
async def process_edit_name(message: Message, state: FSMContext):
    """Обробити нову назву"""
    data = await state.get_data()
    product_id = data['product_id']
    await db.update_product(product_id, name=message.text)
    await message.answer("✅ Назву оновлено!")
    await state.clear()

@router.callback_query(F.data.startswith("edit_price_"))
async def edit_product_price(callback: CallbackQuery, state: FSMContext):
    """Редагувати ціну товару"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ заборонено", show_alert=True)
        return
    
    product_id = int(callback.data.split("_")[-1])
    await state.update_data(product_id=product_id)
    await state.set_state(AdminStates.editing_product_price)
    
    await callback.message.answer("Введіть нову ціну товару (тільки число):")
    await callback.answer()

@router.message(AdminStates.editing_product_price)
async def process_edit_price(message: Message, state: FSMContext):
    """Обробити нову ціну"""
    try:
        price = float(message.text.replace(",", "."))
        data = await state.get_data()
        product_id = data['product_id']
        await db.update_product(product_id, price=price)
        await message.answer("✅ Ціну оновлено!")
        await state.clear()
    except ValueError:
        await message.answer("Будь ласка, введіть коректну ціну (тільки число):")

@router.callback_query(F.data.startswith("confirm_delete_"))
async def confirm_delete_product(callback: CallbackQuery):
    """Підтвердити видалення товару"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ заборонено", show_alert=True)
        return
    
    product_id = int(callback.data.split("_")[-1])
    product = await db.get_product(product_id)
    
    if not product:
        await callback.answer("Товар не знайдено", show_alert=True)
        return
    
    # Видаляємо товар
    await db.delete_product(product_id)
    
    # Перевіряємо чи повідомлення містить фото
    if callback.message.photo:
        # Якщо є фото, видаляємо повідомлення і відправляємо нове
        await callback.message.delete()
        await callback.message.answer(
            f"✅ Товар <b>{product['name']}</b> успішно видалено!",
            parse_mode="HTML"
        )
    else:
        # Якщо немає фото, редагуємо текст
        await callback.message.edit_text(
            f"✅ Товар <b>{product['name']}</b> успішно видалено!",
            parse_mode="HTML"
        )
    
    # Показуємо список товарів
    products = await db.get_products(available_only=False)
    if products:
        keyboard = get_admin_products_keyboard(products, page=0, action="delete")
        await callback.message.answer(
            "🗑️ <b>Оберіть товар для видалення:</b>",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        await callback.message.answer("Товарів не знайдено")
    
    await callback.answer("Товар видалено")

@router.callback_query(F.data.startswith("toggle_available_"))
async def toggle_available(callback: CallbackQuery):
    """Перемкнути доступність товару"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ заборонено", show_alert=True)
        return
    
    product_id = int(callback.data.split("_")[-1])
    product = await db.get_product(product_id)
    
    if product:
        new_status = not product['is_available']
        await db.update_product(product_id, is_available=new_status)
        status_text = "доступний" if new_status else "недоступний"
        await callback.answer(f"Товар тепер {status_text}")

@router.message(F.text == "📊 Замовлення")
async def show_admin_orders(message: Message):
    """Показати замовлення для адміна"""
    if not is_admin(message.from_user.id):
        return
    
    orders = await db.get_orders()
    
    if not orders:
        await message.answer("Замовлень немає")
        return
    
    keyboard = get_admin_orders_keyboard(orders)
    await message.answer(
        "📊 <b>Всі замовлення:</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("admin_order_"))
async def show_admin_order(callback: CallbackQuery):
    """Показати деталі замовлення для адміна"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ заборонено", show_alert=True)
        return
    
    order_id = int(callback.data.split("_")[-1])
    order = await db.get_order(order_id)
    
    if not order:
        await callback.answer("Замовлення не знайдено", show_alert=True)
        return
    
    items = await db.get_order_items(order_id)
    user = await db.get_user(order['user_id'])
    
    status_text = ORDER_STATUSES.get(order['status'], order['status'])
    
    text = f"📦 <b>Замовлення #{order_id}</b>\n\n"
    text += f"Користувач: {user['first_name'] if user else 'Невідомо'}\n"
    text += f"ID: <code>{order['user_id']}</code>\n"
    text += f"Статус: {status_text}\n"
    text += f"📞 Телефон: {order['phone']}\n"
    text += f"📍 Адреса: {order['address']}\n\n"
    text += "<b>Товари:</b>\n"
    
    for item in items:
        text += f"• {item['name']} - {item['quantity']} шт. × {item['price']} грн\n"
    
    text += f"\n<b>Загалом: {order['total_price']} грн</b>"
    
    keyboard = get_order_status_keyboard(order_id)
    
    if order.get('receipt_photo_id'):
        await callback.message.delete()
        await callback.message.answer_photo(
            order['receipt_photo_id'],
            caption=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    
    await callback.answer()

@router.callback_query(F.data.startswith("set_status_"))
async def set_order_status(callback: CallbackQuery):
    """Встановити статус замовлення"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ заборонено", show_alert=True)
        return
    
    parts = callback.data.split("_")
    order_id = int(parts[2])
    status = parts[3]
    
    await db.update_order_status(order_id, status)
    
    # Відправити сповіщення користувачу
    order = await db.get_order(order_id)
    if order:
        status_text = ORDER_STATUSES.get(status, status)
        await callback.answer(f"Статус змінено на: {status_text}")
        
        # Відправити сповіщення користувачу (використовуємо bot з callback)
        bot = callback.bot
        await send_order_status_notification(bot, order['user_id'], order_id, status)
        
        # Оновити відображення
        await show_admin_order(callback)

@router.callback_query(F.data == "admin_orders")
async def back_to_admin_orders(callback: CallbackQuery):
    """Повернутися до списку замовлень"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ заборонено", show_alert=True)
        return
    
    orders = await db.get_orders()
    keyboard = get_admin_orders_keyboard(orders)
    await callback.message.edit_text(
        "📊 <b>Всі замовлення:</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(F.text == "📋 Предзакази")
async def show_admin_preorders(message: Message):
    """Показати предзакази для адміна"""
    if not is_admin(message.from_user.id):
        return
    
    preorders = await db.get_preorders()
    
    if not preorders:
        await message.answer("Предзаказів немає")
        return
    
    text = "📋 <b>Всі предзакази:</b>\n\n"
    
    for preorder in preorders:
        status_text = {
            "pending": "⏳ Очікує",
            "ready": "✅ Готово",
            "cancelled": "❌ Скасовано"
        }.get(preorder['status'], preorder['status'])
        
        text += f"#{preorder['id']} - {preorder['name']}\n"
        text += f"Користувач: {preorder['user_id']}\n"
        text += f"Кількість: {preorder['quantity']}\n"
        text += f"Статус: {status_text}\n\n"
    
    await message.answer(text, parse_mode="HTML")


