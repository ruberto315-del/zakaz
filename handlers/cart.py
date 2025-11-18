from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from keyboards import get_cart_keyboard, get_main_menu
from database import db

router = Router()

@router.message(F.text == "🛒 Корзина")
async def show_cart(message: Message):
    """Показати корзину"""
    user_id = message.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        await message.answer("🛒 Ваша корзина порожня")
        return
    
    text = "🛒 <b>Ваша корзина:</b>\n\n"
    total = 0
    
    for item in cart_items:
        item_total = item['price'] * item['quantity']
        total += item_total
        text += f"• {item['name']}\n"
        text += f"  {item['quantity']} шт. × {item['price']} грн = {item_total} грн\n\n"
    
    text += f"<b>Загалом: {total} грн</b>"
    
    keyboard = get_cart_keyboard(cart_items)
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data.startswith("add_to_cart_"))
async def add_to_cart(callback: CallbackQuery):
    """Додати товар до корзини"""
    product_id = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id
    
    product = await db.get_product(product_id)
    if not product:
        await callback.answer("Товар не знайдено", show_alert=True)
        return
    
    if not product['is_available']:
        await callback.answer("Товар недоступний", show_alert=True)
        return
    
    await db.add_to_cart(user_id, product_id)
    await callback.answer(f"✅ {product['name']} додано до корзини!")

@router.callback_query(F.data.startswith("remove_cart_"))
async def remove_from_cart(callback: CallbackQuery):
    """Видалити товар з корзини"""
    cart_id = int(callback.data.split("_")[-1])
    await db.remove_from_cart(cart_id)
    
    user_id = callback.from_user.id
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        await callback.message.edit_text("🛒 Ваша корзина порожня")
        await callback.answer("Корзина очищена")
        return
    
    text = "🛒 <b>Ваша корзина:</b>\n\n"
    total = 0
    
    for item in cart_items:
        item_total = item['price'] * item['quantity']
        total += item_total
        text += f"• {item['name']}\n"
        text += f"  {item['quantity']} шт. × {item['price']} грн = {item_total} грн\n\n"
    
    text += f"<b>Загалом: {total} грн</b>"
    
    keyboard = get_cart_keyboard(cart_items)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer("Товар видалено")

@router.callback_query(F.data.startswith("inc_cart_"))
async def increase_cart_quantity(callback: CallbackQuery):
    """Збільшити кількість товару"""
    cart_id = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id
    
    cart_items = await db.get_cart(user_id)
    cart_item = next((item for item in cart_items if item['cart_id'] == cart_id), None)
    
    if cart_item:
        await db.update_cart_quantity(cart_id, cart_item['quantity'] + 1)
    
    # Оновити відображення
    cart_items = await db.get_cart(user_id)
    text = "🛒 <b>Ваша корзина:</b>\n\n"
    total = 0
    
    for item in cart_items:
        item_total = item['price'] * item['quantity']
        total += item_total
        text += f"• {item['name']}\n"
        text += f"  {item['quantity']} шт. × {item['price']} грн = {item_total} грн\n\n"
    
    text += f"<b>Загалом: {total} грн</b>"
    
    keyboard = get_cart_keyboard(cart_items)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("dec_cart_"))
async def decrease_cart_quantity(callback: CallbackQuery):
    """Зменшити кількість товару"""
    cart_id = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id
    
    cart_items = await db.get_cart(user_id)
    cart_item = next((item for item in cart_items if item['cart_id'] == cart_id), None)
    
    if cart_item:
        new_quantity = cart_item['quantity'] - 1
        await db.update_cart_quantity(cart_id, new_quantity)
    
    # Оновити відображення
    cart_items = await db.get_cart(user_id)
    
    if not cart_items:
        await callback.message.edit_text("🛒 Ваша корзина порожня")
        await callback.answer()
        return
    
    text = "🛒 <b>Ваша корзина:</b>\n\n"
    total = 0
    
    for item in cart_items:
        item_total = item['price'] * item['quantity']
        total += item_total
        text += f"• {item['name']}\n"
        text += f"  {item['quantity']} шт. × {item['price']} грн = {item_total} грн\n\n"
    
    text += f"<b>Загалом: {total} грн</b>"
    
    keyboard = get_cart_keyboard(cart_items)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "clear_cart")
async def clear_cart(callback: CallbackQuery):
    """Очистити корзину"""
    user_id = callback.from_user.id
    await db.clear_cart(user_id)
    await callback.message.edit_text("🛒 Ваша корзина очищена")
    await callback.answer("Корзина очищена")

