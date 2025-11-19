from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, URLInputFile, BufferedInputFile
from aiogram.utils.chat_action import ChatActionSender
from keyboards import get_catalog_keyboard, get_product_keyboard
from database import db
import aiohttp
import logging

logger = logging.getLogger(__name__)

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
        # Перевіряємо чи це URL (починається з http) або file_id
        if product['photo_id'].startswith('http'):
            # Це URL з postimages.org
            # Telegram не може отримати контент з деяких URL, тому скачуємо фото і відправляємо як файл
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                    async with session.get(product['photo_id'], headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                        if resp.status == 200:
                            photo_data = await resp.read()
                            # Визначаємо ім'я файлу з URL
                            filename = product['photo_id'].split('/')[-1] or 'photo.jpg'
                            # Використовуємо BufferedInputFile для відправки байтів
                            photo_file = BufferedInputFile(photo_data, filename=filename)
                            
                            async with ChatActionSender.upload_photo(chat_id=callback.message.chat.id, bot=callback.bot):
                                await callback.message.answer_photo(
                                    photo_file,
                                    caption=text,
                                    reply_markup=keyboard,
                                    parse_mode="HTML"
                                )
                        else:
                            # Якщо не вдалося скачати, відправляємо без фото
                            logger.error(f"Не вдалося скачати фото: статус {resp.status}")
                            await callback.message.answer(
                                text,
                                reply_markup=keyboard,
                                parse_mode="HTML"
                            )
            except Exception as e:
                logger.error(f"Помилка при скачуванні та відправці фото: {e}", exc_info=True)
                # Відправляємо без фото
                await callback.message.answer(
                    text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
        else:
            # Це старий file_id (для сумісності)
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

