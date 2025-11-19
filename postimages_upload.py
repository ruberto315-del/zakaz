"""
Модуль для завантаження фото на postimages.org
"""
import aiohttp
import logging
from io import BytesIO
import re

logger = logging.getLogger(__name__)

async def upload_photo_to_postimages(photo_file: BytesIO, filename: str = "photo.jpg") -> str:
    """
    Завантажити фото на postimages.org
    
    Args:
        photo_file: BytesIO об'єкт з фото
        filename: Ім'я файлу
        
    Returns:
        str: Пряме посилання на фото
    """
    try:
        # Postimages.org використовує POST запит до форми завантаження
        upload_url = "https://postimages.org/api/upload"
        
        # Підготовка даних для завантаження
        data = aiohttp.FormData()
        photo_file.seek(0)  # Переміщуємо вказівник на початок
        
        # Визначаємо content type за розширенням
        content_type = 'image/jpeg'
        if filename.lower().endswith('.png'):
            content_type = 'image/png'
        elif filename.lower().endswith('.gif'):
            content_type = 'image/gif'
        
        data.add_field('upload', photo_file, filename=filename, content_type=content_type)
        data.add_field('token', '')  # Публічне завантаження
        data.add_field('optsize', '0')  # Оригінальний розмір
        data.add_field('expire', '0')  # Без обмеження терміну
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(upload_url, data=data) as response:
                if response.status == 200:
                    # Postimages повертає HTML з посиланням
                    text = await response.text()
                    
                    # Шукаємо пряме посилання на зображення в форматі i.postimg.cc
                    # Можливі формати:
                    # https://i.postimg.cc/xxxxx/xxxxx.jpg
                    # https://postimg.cc/xxxxx (потрібно конвертувати)
                    match = re.search(r'https://i\.postimg\.cc/[a-zA-Z0-9/]+\.(jpg|jpeg|png|gif)', text, re.IGNORECASE)
                    if match:
                        return match.group(0)
                    
                    # Шукаємо код зображення
                    match = re.search(r'postimg\.cc/([a-zA-Z0-9]+)', text, re.IGNORECASE)
                    if match:
                        code = match.group(1)
                        # Формуємо пряме посилання
                        return f"https://i.postimg.cc/{code}.jpg"
                    
                    # Спробуємо знайти в JSON форматі
                    try:
                        result = await response.json()
                        if isinstance(result, dict):
                            if 'url' in result:
                                url = result['url']
                                if 'postimg.cc' in url:
                                    code = url.split('/')[-1]
                                    return f"https://i.postimg.cc/{code}.jpg"
                                return url
                            if 'status' in result and result.get('status') == 'OK':
                                url = result.get('url', '')
                                if url and 'postimg.cc' in url:
                                    code = url.split('/')[-1]
                                    return f"https://i.postimg.cc/{code}.jpg"
                                return url
                    except:
                        pass
                    
                    logger.error(f"Не вдалося знайти посилання в відповіді. Перші 500 символів: {text[:500]}")
                    return None
                else:
                    text = await response.text()
                    logger.error(f"Помилка завантаження на postimages: {response.status} - {text[:200]}")
                    return None
    except Exception as e:
        logger.error(f"Помилка при завантаженні фото на postimages.org: {e}", exc_info=True)
        return None

async def upload_telegram_photo_to_postimages(bot, photo_file_id: str) -> str:
    """
    Завантажити фото з Telegram на postimages.org
    
    Args:
        bot: Bot об'єкт aiogram
        photo_file_id: file_id фото з Telegram
        
    Returns:
        str: Пряме посилання на фото
    """
    try:
        # Отримуємо інформацію про файл
        file = await bot.get_file(photo_file_id)
        
        # Завантажуємо файл з Telegram
        photo_bytes = BytesIO()
        await bot.download_file(file.file_path, photo_bytes)
        photo_bytes.seek(0)
        
        # Завантажуємо на postimages.org
        url = await upload_photo_to_postimages(photo_bytes, filename=file.file_path.split('/')[-1])
        return url
    except Exception as e:
        logger.error(f"Помилка при завантаженні фото з Telegram на postimages.org: {e}", exc_info=True)
        return None

