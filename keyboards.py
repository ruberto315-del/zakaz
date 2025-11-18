from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

def get_main_menu():
    """Головне меню"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="🛍️ Каталог товарів"))
    builder.add(KeyboardButton(text="🛒 Корзина"))
    builder.add(KeyboardButton(text="📦 Мої замовлення"))
    builder.add(KeyboardButton(text="📋 Предзакази"))
    builder.add(KeyboardButton(text="❓ FAQ"))
    builder.add(KeyboardButton(text="📞 Зв'язок з адміном"))
    builder.adjust(2, 2, 2)
    return builder.as_markup(resize_keyboard=True)

def get_admin_menu():
    """Меню адміністратора"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="➕ Додати товар"))
    builder.add(KeyboardButton(text="📝 Редагувати товар"))
    builder.add(KeyboardButton(text="📊 Замовлення"))
    builder.add(KeyboardButton(text="📋 Предзакази"))
    builder.add(KeyboardButton(text="❓ Керування FAQ"))
    builder.add(KeyboardButton(text="🏠 Головне меню"))
    builder.adjust(2, 2, 2)
    return builder.as_markup(resize_keyboard=True)

def get_product_keyboard(product_id, is_preorder=False):
    """Клавіатура для товару"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="➕ Додати до корзини", callback_data=f"add_to_cart_{product_id}"))
    if is_preorder:
        builder.add(InlineKeyboardButton(text="📋 Оформити предзаказ", callback_data=f"preorder_{product_id}"))
    builder.add(InlineKeyboardButton(text="🔙 Назад до каталогу", callback_data="back_to_catalog"))
    builder.adjust(1)
    return builder.as_markup()

def get_catalog_keyboard(products, page=0, per_page=5):
    """Клавіатура каталогу з пагінацією"""
    builder = InlineKeyboardBuilder()
    
    start = page * per_page
    end = start + per_page
    page_products = products[start:end]
    
    for product in page_products:
        builder.add(InlineKeyboardButton(
            text=f"{product['name']} - {product['price']} грн",
            callback_data=f"product_{product['id']}"
        ))
    
    # Кнопки навігації
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"catalog_page_{page-1}"))
    if end < len(products):
        nav_buttons.append(InlineKeyboardButton(text="Вперед ▶️", callback_data=f"catalog_page_{page+1}"))
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    builder.add(InlineKeyboardButton(text="🔙 Головне меню", callback_data="main_menu"))
    return builder.as_markup()

def get_cart_keyboard(cart_items):
    """Клавіатура корзини"""
    builder = InlineKeyboardBuilder()
    
    for item in cart_items:
        builder.add(InlineKeyboardButton(
            text=f"❌ {item['name']} (x{item['quantity']})",
            callback_data=f"remove_cart_{item['cart_id']}"
        ))
        builder.add(InlineKeyboardButton(
            text=f"➖",
            callback_data=f"dec_cart_{item['cart_id']}"
        ))
        builder.add(InlineKeyboardButton(
            text=f"➕",
            callback_data=f"inc_cart_{item['cart_id']}"
        ))
    
    builder.add(InlineKeyboardButton(text="✅ Оформити замовлення", callback_data="checkout"))
    builder.add(InlineKeyboardButton(text="🗑️ Очистити корзину", callback_data="clear_cart"))
    builder.add(InlineKeyboardButton(text="🔙 Головне меню", callback_data="main_menu"))
    builder.adjust(1, 3)
    return builder.as_markup()

def get_orders_keyboard(orders):
    """Клавіатура замовлень"""
    builder = InlineKeyboardBuilder()
    
    for order in orders:
        status_text = {
            "pending": "⏳ Очікує",
            "processing": "🔄 В обробці",
            "ready": "✅ Готове",
            "shipped": "🚚 Відправлено",
            "delivered": "📦 Доставлено",
            "cancelled": "❌ Скасовано"
        }.get(order['status'], order['status'])
        
        builder.add(InlineKeyboardButton(
            text=f"#{order['id']} - {status_text} - {order['total_price']} грн",
            callback_data=f"order_{order['id']}"
        ))
    
    builder.add(InlineKeyboardButton(text="🔙 Головне меню", callback_data="main_menu"))
    return builder.as_markup()

def get_admin_orders_keyboard(orders):
    """Клавіатура замовлень для адміна"""
    builder = InlineKeyboardBuilder()
    
    for order in orders:
        status_text = {
            "pending": "⏳ Очікує",
            "processing": "🔄 В обробці",
            "ready": "✅ Готове",
            "shipped": "🚚 Відправлено",
            "delivered": "📦 Доставлено",
            "cancelled": "❌ Скасовано"
        }.get(order['status'], order['status'])
        
        builder.add(InlineKeyboardButton(
            text=f"#{order['id']} - {status_text}",
            callback_data=f"admin_order_{order['id']}"
        ))
    
    builder.add(InlineKeyboardButton(text="🔙 Адмін-панель", callback_data="admin_menu"))
    return builder.as_markup()

def get_order_status_keyboard(order_id):
    """Клавіатура для зміни статусу замовлення (адмін)"""
    builder = InlineKeyboardBuilder()
    statuses = [
        ("⏳ Очікує", "pending"),
        ("🔄 В обробці", "processing"),
        ("✅ Готове", "ready"),
        ("🚚 Відправлено", "shipped"),
        ("📦 Доставлено", "delivered"),
        ("❌ Скасувати", "cancelled")
    ]
    
    for text, status in statuses:
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=f"set_status_{order_id}_{status}"
        ))
    
    builder.add(InlineKeyboardButton(text="🔙 До замовлень", callback_data="admin_orders"))
    builder.adjust(2)
    return builder.as_markup()

def get_product_edit_keyboard(product_id):
    """Клавіатура для редагування товару"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="✏️ Змінити назву", callback_data=f"edit_name_{product_id}"))
    builder.add(InlineKeyboardButton(text="✏️ Змінити опис", callback_data=f"edit_desc_{product_id}"))
    builder.add(InlineKeyboardButton(text="💰 Змінити ціну", callback_data=f"edit_price_{product_id}"))
    builder.add(InlineKeyboardButton(text="📷 Змінити фото", callback_data=f"edit_photo_{product_id}"))
    builder.add(InlineKeyboardButton(text="✅ Доступність", callback_data=f"toggle_available_{product_id}"))
    builder.add(InlineKeyboardButton(text="🔙 До товарів", callback_data="admin_products"))
    builder.adjust(2)
    return builder.as_markup()

def get_admin_products_keyboard(products):
    """Клавіатура товарів для адміна"""
    builder = InlineKeyboardBuilder()
    
    for product in products:
        status = "✅" if product['is_available'] else "❌"
        builder.add(InlineKeyboardButton(
            text=f"{status} {product['name']} - {product['price']} грн",
            callback_data=f"admin_product_{product['id']}"
        ))
    
    builder.add(InlineKeyboardButton(text="🔙 Адмін-панель", callback_data="admin_menu"))
    return builder.as_markup()

def get_payment_keyboard(order_id):
    """Клавіатура оплати"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="💳 Оплатити через LiqPay", callback_data=f"pay_liqpay_{order_id}"))
    builder.add(InlineKeyboardButton(text="📸 Прикріпити чек", callback_data=f"attach_receipt_{order_id}"))
    builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu"))
    builder.adjust(1)
    return builder.as_markup()

def get_contact_keyboard():
    """Клавіатура для зв'язку з адміном"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="📞 Написати адміну", callback_data="contact_admin"))
    builder.add(InlineKeyboardButton(text="🔙 Головне меню", callback_data="main_menu"))
    return builder.as_markup()

def get_faq_keyboard(faqs):
    """Клавіатура FAQ"""
    builder = InlineKeyboardBuilder()
    
    for faq in faqs:
        builder.add(InlineKeyboardButton(
            text=f"❓ {faq['question']}",
            callback_data=f"faq_{faq['id']}"
        ))
    
    builder.add(InlineKeyboardButton(text="🔙 Головне меню", callback_data="main_menu"))
    return builder.as_markup()

def get_yes_no_keyboard():
    """Клавіатура так/ні"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="✅ Так", callback_data="yes"))
    builder.add(InlineKeyboardButton(text="❌ Ні", callback_data="no"))
    return builder.as_markup()

