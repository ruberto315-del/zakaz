from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards import (
    get_admin_menu, get_admin_orders_keyboard, get_order_status_keyboard,
    get_admin_products_keyboard, get_product_edit_keyboard, get_main_menu
)
from database import db
from config import ADMIN_ID, ORDER_STATUSES
from notifications import send_order_status_notification

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
    adding_faq_question = State()
    adding_faq_answer = State()

def is_admin(user_id: int) -> bool:
    """Перевірити чи користувач адмін"""
    return user_id == ADMIN_ID

@router.message(F.text == "🏠 Головне меню")
async def admin_main_menu(message: Message):
    """Головне меню адміна"""
    if is_admin(message.from_user.id):
        await message.answer("Адмін-панель:", reply_markup=get_admin_menu())

@router.message(F.text == "➕ Додати товар")
async def start_adding_product(message: Message, state: FSMContext):
    """Почати додавання товару"""
    if not is_admin(message.from_user.id):
        return
    
    await message.answer("Введіть назву товару:")
    await state.set_state(AdminStates.adding_product_name)

@router.message(AdminStates.adding_product_name)
async def process_product_name(message: Message, state: FSMContext):
    """Обробити назву товару"""
    await state.update_data(name=message.text)
    await message.answer("Введіть опис товару:")
    await state.set_state(AdminStates.adding_product_description)

@router.message(AdminStates.adding_product_description)
async def process_product_description(message: Message, state: FSMContext):
    """Обробити опис товару"""
    await state.update_data(description=message.text)
    await message.answer("Введіть ціну товару (тільки число):")
    await state.set_state(AdminStates.adding_product_price)

@router.message(AdminStates.adding_product_price)
async def process_product_price(message: Message, state: FSMContext):
    """Обробити ціну товару"""
    try:
        price = float(message.text.replace(",", "."))
        await state.update_data(price=price)
        await message.answer("Введіть категорію товару (або /skip щоб пропустити):")
        await state.set_state(AdminStates.adding_product_category)
    except ValueError:
        await message.answer("Будь ласка, введіть коректну ціну (тільки число):")

@router.message(AdminStates.adding_product_category)
async def process_product_category(message: Message, state: FSMContext):
    """Обробити категорію товару"""
    category = message.text.strip() if message.text != "/skip" else None
    await state.update_data(category=category)
    await message.answer("Надішліть фото товару:")
    await state.set_state(AdminStates.adding_product_photo)

@router.message(AdminStates.adding_product_photo, F.photo)
async def process_product_photo(message: Message, state: FSMContext):
    """Обробити фото товару"""
    photo_id = message.photo[-1].file_id
    data = await state.get_data()
    
    product_id = await db.add_product(
        name=data['name'],
        description=data['description'],
        price=data['price'],
        photo_id=photo_id,
        category=data.get('category')
    )
    
    await message.answer(
        f"✅ Товар додано!\n\n"
        f"ID: {product_id}\n"
        f"Назва: {data['name']}\n"
        f"Ціна: {data['price']} грн"
    )
    
    await state.clear()

@router.message(F.text == "📝 Редагувати товар")
async def show_products_for_edit(message: Message):
    """Показати товари для редагування"""
    if not is_admin(message.from_user.id):
        return
    
    products = await db.get_products(available_only=False)
    
    if not products:
        await message.answer("Товарів не знайдено")
        return
    
    keyboard = get_admin_products_keyboard(products)
    await message.answer(
        "📝 <b>Оберіть товар для редагування:</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("admin_product_"))
async def show_product_edit_options(callback: CallbackQuery):
    """Показати опції редагування товару"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ заборонено", show_alert=True)
        return
    
    product_id = int(callback.data.split("_")[-1])
    product = await db.get_product(product_id)
    
    if not product:
        await callback.answer("Товар не знайдено", show_alert=True)
        return
    
    text = f"📝 <b>Редагування товару</b>\n\n"
    text += f"ID: {product_id}\n"
    text += f"Назва: {product['name']}\n"
    text += f"Опис: {product['description']}\n"
    text += f"Ціна: {product['price']} грн\n"
    text += f"Доступність: {'✅' if product['is_available'] else '❌'}\n"
    
    keyboard = get_product_edit_keyboard(product_id)
    
    if product['photo_id']:
        await callback.message.delete()
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
    text += f"ID: {order['user_id']}\n"
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
        
        # Відправити сповіщення користувачу
        await send_order_status_notification(order['user_id'], order_id, status)
        
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

@router.message(F.text == "❓ Керування FAQ")
async def manage_faq(message: Message, state: FSMContext):
    """Керування FAQ"""
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "❓ <b>Керування FAQ</b>\n\n"
        "Введіть питання для нового FAQ:",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.adding_faq_question)

@router.message(AdminStates.adding_faq_question)
async def process_faq_question(message: Message, state: FSMContext):
    """Обробити питання FAQ"""
    await state.update_data(question=message.text)
    await message.answer("Введіть відповідь на питання:")
    await state.set_state(AdminStates.adding_faq_answer)

@router.message(AdminStates.adding_faq_answer)
async def process_faq_answer(message: Message, state: FSMContext):
    """Обробити відповідь FAQ"""
    data = await state.get_data()
    question = data['question']
    answer = message.text
    
    faq_id = await db.add_faq(question, answer)
    
    await message.answer(
        f"✅ FAQ додано!\n\n"
        f"ID: {faq_id}\n"
        f"Питання: {question}\n"
        f"Відповідь: {answer}"
    )
    
    await state.clear()

