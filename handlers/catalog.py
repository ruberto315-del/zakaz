from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from keyboards import get_catalog_keyboard, get_product_keyboard
from database import db

router = Router()

@router.message(F.text == "🛍️ Каталог товарів")
async def show_catalog(message: Message):
    """Показати каталог товарів"""
    products = await db.get_products()
    
    if not products:
        await message.answer("📦 Каталог порожній. Товари будуть додані найближчим часом.")
        return
    
    # Показати перші товари
    keyboard = get_catalog_keyboard(products, page=0)
    await message.answer(
        "🛍️ <b>Каталог товарів</b>\n\n"
        "Оберіть товар:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("catalog_page_"))
async def catalog_page(callback: CallbackQuery):
    """Пагінація каталогу"""
    page = int(callback.data.split("_")[-1])
    products = await db.get_products()
    keyboard = get_catalog_keyboard(products, page=page)
    
    await callback.message.edit_text(
        "🛍️ <b>Каталог товарів</b>\n\n"
        "Оберіть товар:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("product_"))
async def show_product(callback: CallbackQuery):
    """Показати товар"""
    product_id = int(callback.data.split("_")[1])
    product = await db.get_product(product_id)
    
    if not product:
        await callback.answer("Товар не знайдено", show_alert=True)
        return
    
    text = f"🛍️ <b>{product['name']}</b>\n\n"
    if product['description']:
        text += f"{product['description']}\n\n"
    text += f"💰 Ціна: <b>{product['price']} грн</b>\n"
    
    if product['is_preorder']:
        text += "\n📋 Цей товар доступний для предзаказу"
    
    keyboard = get_product_keyboard(product_id, product['is_preorder'])
    
    if product['photo_id']:
        await callback.message.delete()
        await callback.message.answer_photo(
            product['photo_id'],
            caption=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    await callback.answer()

@router.callback_query(F.data == "back_to_catalog")
async def back_to_catalog(callback: CallbackQuery):
    """Повернутися до каталогу"""
    products = await db.get_products()
    keyboard = get_catalog_keyboard(products, page=0)
    
    # Якщо повідомлення містить фото, видаляємо його і відправляємо нове
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(
            "🛍️ <b>Каталог товарів</b>\n\n"
            "Оберіть товар:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        try:
            await callback.message.edit_text(
                "🛍️ <b>Каталог товарів</b>\n\n"
                "Оберіть товар:",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        except Exception:
            # Якщо не вдалося відредагувати, видаляємо і відправляємо нове
            await callback.message.delete()
            await callback.message.answer(
                "🛍️ <b>Каталог товарів</b>\n\n"
                "Оберіть товар:",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
    await callback.answer()

