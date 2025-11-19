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
        # Спробуємо різні можливі URL
        upload_urls = [
            "https://postimages.org/web",
            "https://postimages.org/api/upload.php",
            "https://postimages.org/upload.php"
        ]
        
        upload_url = upload_urls[0]  # Починаємо з першого
        
        # Підготовка даних для завантаження
        data = aiohttp.FormData()
        photo_file.seek(0)  # Переміщуємо вказівник на початок
        
        # Визначаємо content type за розширенням
        content_type = 'image/jpeg'
        if filename.lower().endswith('.png'):
            content_type = 'image/png'
        elif filename.lower().endswith('.gif'):
            content_type = 'image/gif'
        elif filename.lower().endswith('.webp'):
            content_type = 'image/webp'
        
        # Правильні поля для форми завантаження
        data.add_field('upload', photo_file, filename=filename, content_type=content_type)
        data.add_field('token', '')  # Публічне завантаження
        data.add_field('optsize', '0')  # Оригінальний розмір
        data.add_field('expire', '0')  # Без обмеження терміну
        data.add_field('upload_session', '')  # Порожня сесія
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://postimages.org/',
            'Origin': 'https://postimages.org',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        }
        
        async with aiohttp.ClientSession(headers=headers) as session:
            # Спочатку отримуємо головну сторінку для отримання cookies (якщо потрібно)
            async with session.get('https://postimages.org/', timeout=aiohttp.ClientTimeout(total=30)) as get_response:
                if get_response.status == 200:
                    logger.debug("Отримано головну сторінку postimages.org")
            
            # Спробуємо завантажити через різні URL
            last_error = None
            for url in upload_urls:
                try:
                    async with session.post(url, data=data, timeout=aiohttp.ClientTimeout(total=60)) as response:
                        if response.status == 200:
                            # Postimages може повертати HTML або JSON
                            content_type = response.headers.get('Content-Type', '').lower()
                            text = await response.text()
                            
                            # Логуємо перші 1000 символів для діагностики
                            logger.debug(f"Відповідь від {url} (Content-Type: {content_type}): {text[:1000]}")
                            
                            # Спочатку спробуємо JSON (якщо це JSON)
                            if 'application/json' in content_type or text.strip().startswith('{'):
                                try:
                                    result = await response.json()
                                    logger.debug(f"JSON відповідь: {result}")
                                    if isinstance(result, dict):
                                        # Різні можливі поля з URL
                                        for key in ['url', 'image', 'link', 'direct_link', 'direct_url']:
                                            if key in result:
                                                result_url = result[key]
                                                if 'i.postimg.cc' in result_url:
                                                    return result_url
                                                elif 'postimg.cc' in result_url:
                                                    # Конвертуємо postimg.cc в i.postimg.cc
                                                    parts = result_url.split('/')
                                                    if len(parts) >= 2:
                                                        code = parts[-1] if parts[-1] else parts[-2]
                                                        return f"https://i.postimg.cc/{code}/{filename}"
                                        if 'status' in result and result.get('status') == 'OK':
                                            # Можливо URL в іншому полі
                                            for key in result.keys():
                                                if 'url' in key.lower() or 'link' in key.lower():
                                                    result_url = result[key]
                                                    if isinstance(result_url, str) and 'postimg.cc' in result_url:
                                                        if 'i.postimg.cc' in result_url:
                                                            return result_url
                                                        else:
                                                            parts = result_url.split('/')
                                                            code = parts[-1] if parts[-1] else parts[-2]
                                                            return f"https://i.postimg.cc/{code}/{filename}"
                                except Exception as e:
                                    logger.debug(f"Не вдалося розпарсити як JSON: {e}")
                            
                            # Шукаємо пряме посилання на зображення в форматі i.postimg.cc
                            # Формат: https://i.postimg.cc/{код}/{ім'я_файла}.{розширення}
                            # Наприклад: https://i.postimg.cc/TyTb4qkC/zobrazenna.png
                            patterns = [
                                # Повний URL з кодом та ім'ям файлу: https://i.postimg.cc/CODE/filename.ext
                                r'https://i\.postimg\.cc/([a-zA-Z0-9]+)/([a-zA-Z0-9_\-]+\.(jpg|jpeg|png|gif|webp))',
                                # URL без імені файлу: https://i.postimg.cc/CODE.ext
                                r'https://i\.postimg\.cc/([a-zA-Z0-9]+)\.(jpg|jpeg|png|gif|webp)',
                                # Без https:// з ім'ям файлу
                                r'i\.postimg\.cc/([a-zA-Z0-9]+)/([a-zA-Z0-9_\-]+\.(jpg|jpeg|png|gif|webp))',
                                # Без https:// без імені файлу
                                r'i\.postimg\.cc/([a-zA-Z0-9]+)\.(jpg|jpeg|png|gif|webp)',
                            ]
                            
                            for pattern in patterns:
                                match = re.search(pattern, text, re.IGNORECASE)
                                if match:
                                    if match.group(0).startswith('http'):
                                        return match.group(0)
                                    else:
                                        # Формуємо повний URL
                                        code = match.group(1)
                                        if len(match.groups()) >= 2 and match.group(2):
                                            filename_part = match.group(2)
                                            return f"https://i.postimg.cc/{code}/{filename_part}"
                                        else:
                                            ext = filename.split('.')[-1] if '.' in filename else 'jpg'
                                            return f"https://i.postimg.cc/{code}/{filename}"
                            
                            # Шукаємо код зображення в форматі postimg.cc (без i.)
                            match = re.search(r'postimg\.cc/([a-zA-Z0-9]+)', text, re.IGNORECASE)
                            if match:
                                code = match.group(1)
                                # Формуємо URL з ім'ям файлу (як показав користувач)
                                return f"https://i.postimg.cc/{code}/{filename}"
                            
                            # Шукаємо в HTML атрибутах (data-url, href, src, data-src)
                            html_patterns = [
                                r'(?:data-url|href|src|data-src)=["\']([^"\']*i\.postimg\.cc[^"\']*)["\']',
                                r'(?:data-url|href|src|data-src)=["\']([^"\']*postimg\.cc[^"\']*)["\']',
                            ]
                            for pattern in html_patterns:
                                match = re.search(pattern, text, re.IGNORECASE)
                                if match:
                                    found_url = match.group(1)
                                    if 'i.postimg.cc' in found_url:
                                        return found_url
                                    elif 'postimg.cc' in found_url:
                                        parts = found_url.split('/')
                                        code = parts[-1] if parts[-1] else parts[-2]
                                        ext = filename.split('.')[-1] if '.' in filename else 'jpg'
                                        return f"https://i.postimg.cc/{code}/{filename}"
                            
                            logger.warning(f"Не вдалося знайти посилання в відповіді з {url}. Перші 1000 символів: {text[:1000]}")
                            # Продовжуємо спробувати наступний URL
                        else:
                            text = await response.text()
                            last_error = f"Status {response.status}: {text[:200]}"
                            logger.warning(f"Помилка завантаження на {url}: {last_error}")
                            continue  # Спробуємо наступний URL
                except Exception as e:
                    last_error = str(e)
                    logger.warning(f"Помилка при спробі завантаження на {url}: {e}")
                    continue  # Спробуємо наступний URL
            
            # Якщо всі спроби не вдалися
            logger.error(f"Всі спроби завантаження на postimages.org не вдалися. Остання помилка: {last_error}")
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

