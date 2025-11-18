from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from keyboards import get_contact_keyboard, get_main_menu
from config import ADMIN_ID

router = Router()

@router.message(F.text == "📞 Зв'язок з адміном")
async def show_contact(message: Message):
    """Показати опції зв'язку з адміном"""
    keyboard = get_contact_keyboard()
    await message.answer(
        "📞 <b>Зв'язок з адміністратором</b>\n\n"
        "Оберіть дію:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data == "contact_admin")
async def contact_admin(callback: CallbackQuery):
    """Написати адміну"""
    await callback.message.answer(
        "Напишіть ваше повідомлення, і воно буде переслано адміністратору:"
    )
    await callback.answer()

@router.message(F.text, F.chat.type == "private")
async def forward_to_admin(message: Message):
    """Переслати повідомлення адміну"""
    # Перевірити чи це не команда
    if message.text.startswith("/"):
        return
    
    # Перевірити чи це не адмін пише сам собі
    if message.from_user.id == ADMIN_ID:
        return
    
    # Переслати повідомлення адміну
    await message.forward(ADMIN_ID)
    await message.answer(
        "✅ Ваше повідомлення відправлено адміністратору!\n"
        "Він відповість найближчим часом."
    )

