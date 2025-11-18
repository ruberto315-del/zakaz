from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from keyboards import get_main_menu, get_admin_menu
from database import db
from config import ADMIN_ID

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обробник команди /start"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    await db.add_user(user_id, username, first_name)
    
    if user_id == ADMIN_ID:
        await message.answer(
            "👋 Вітаю, адміністратор!\n\n"
            "Оберіть дію:",
            reply_markup=get_admin_menu()
        )
    else:
        await message.answer(
            "👋 Вітаю в нашому магазині!\n\n"
            "Оберіть дію з меню:",
            reply_markup=get_main_menu()
        )

@router.message(F.text == "🏠 Головне меню")
async def main_menu(message: Message):
    """Повернення до головного меню"""
    user_id = message.from_user.id
    if user_id == ADMIN_ID:
        await message.answer("Головне меню:", reply_markup=get_admin_menu())
    else:
        await message.answer("Головне меню:", reply_markup=get_main_menu())

@router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery):
    """Повернення до головного меню через callback"""
    user_id = callback.from_user.id
    if user_id == ADMIN_ID:
        await callback.message.edit_text("Головне меню:", reply_markup=get_admin_menu())
    else:
        await callback.message.edit_text("Головне меню:", reply_markup=get_main_menu())
    await callback.answer()

