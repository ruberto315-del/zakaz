from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from keyboards import get_faq_keyboard, get_main_menu
from database import db

router = Router()

@router.message(F.text == "❓ FAQ")
async def show_faq(message: Message):
    """Показати FAQ"""
    faqs = await db.get_faq()
    
    if not faqs:
        await message.answer(
            "❓ <b>Часті питання</b>\n\n"
            "Наразі FAQ порожній. Питання будуть додані найближчим часом.",
            parse_mode="HTML"
        )
        return
    
    keyboard = get_faq_keyboard(faqs)
    await message.answer(
        "❓ <b>Часті питання</b>\n\n"
        "Оберіть питання:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("faq_"))
async def show_faq_answer(callback: CallbackQuery):
    """Показати відповідь на питання"""
    faq_id = int(callback.data.split("_")[1])
    faqs = await db.get_faq()
    
    faq = next((f for f in faqs if f['id'] == faq_id), None)
    
    if not faq:
        await callback.answer("Питання не знайдено", show_alert=True)
        return
    
    text = f"❓ <b>{faq['question']}</b>\n\n"
    text += f"{faq['answer']}"
    
    keyboard = get_faq_keyboard(faqs)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

