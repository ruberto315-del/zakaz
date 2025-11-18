from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from keyboards import get_main_menu
from database import db

router = Router()

@router.message(F.text == "📋 Предзакази")
async def show_preorders(message: Message):
    """Показати предзакази користувача"""
    user_id = message.from_user.id
    preorders = await db.get_preorders(user_id)
    
    if not preorders:
        await message.answer("📋 У вас немає предзаказів")
        return
    
    text = "📋 <b>Ваші предзакази:</b>\n\n"
    
    for preorder in preorders:
        status_text = {
            "pending": "⏳ Очікує",
            "ready": "✅ Готово",
            "cancelled": "❌ Скасовано"
        }.get(preorder['status'], preorder['status'])
        
        text += f"• {preorder['name']}\n"
        text += f"  Кількість: {preorder['quantity']}\n"
        text += f"  Статус: {status_text}\n"
        text += f"  Ціна: {preorder['price']} грн\n\n"
    
    await message.answer(text, parse_mode="HTML")

@router.callback_query(F.data.startswith("preorder_"))
async def create_preorder(callback: CallbackQuery):
    """Створити предзаказ"""
    product_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    
    product = await db.get_product(product_id)
    if not product:
        await callback.answer("Товар не знайдено", show_alert=True)
        return
    
    preorder_id = await db.create_preorder(user_id, product_id)
    
    await callback.message.answer(
        f"✅ Предзаказ #{preorder_id} створено!\n\n"
        f"Товар: {product['name']}\n"
        f"Ціна: {product['price']} грн\n\n"
        "Ви отримаєте сповіщення, коли товар буде доступний."
    )
    await callback.answer("Предзаказ створено!")

