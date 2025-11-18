"""
Інтеграція з LiqPay для оплати замовлень
Потрібно встановити: pip install liqpay
"""
import hashlib
import base64
import json
from config import LIQPAY_PUBLIC_KEY, LIQPAY_PRIVATE_KEY

try:
    from liqpay import LiqPay
    LIQPAY_AVAILABLE = True
except ImportError:
    LIQPAY_AVAILABLE = False
    print("LiqPay не встановлено. Встановіть: pip install liqpay")


def generate_liqpay_data(order_id: int, amount: float, description: str = "Оплата замовлення") -> dict:
    """
    Генерувати дані для LiqPay
    
    Args:
        order_id: ID замовлення
        amount: Сума оплати
        description: Опис платежу
    
    Returns:
        dict: Дані для форми оплати
    """
    if not LIQPAY_AVAILABLE or not LIQPAY_PUBLIC_KEY or not LIQPAY_PRIVATE_KEY:
        return None
    
    liqpay = LiqPay(LIQPAY_PUBLIC_KEY, LIQPAY_PRIVATE_KEY)
    
    params = {
        'action': 'pay',
        'amount': amount,
        'currency': 'UAH',
        'description': f"{description} #{order_id}",
        'order_id': str(order_id),
        'version': '3',
        'result_url': 'https://your-site.com/payment-result',  # Замініть на ваш URL
        'server_url': 'https://your-site.com/payment-callback',  # Замініть на ваш URL
    }
    
    return liqpay.cnb_form(params)


def create_payment_link(order_id: int, amount: float, description: str = "Оплата замовлення") -> str:
    """
    Створити посилання для оплати через LiqPay
    
    Args:
        order_id: ID замовлення
        amount: Сума оплати
        description: Опис платежу
    
    Returns:
        str: HTML форма або посилання для оплати
    """
    if not LIQPAY_AVAILABLE or not LIQPAY_PUBLIC_KEY or not LIQPAY_PRIVATE_KEY:
        return None
    
    liqpay = LiqPay(LIQPAY_PUBLIC_KEY, LIQPAY_PRIVATE_KEY)
    
    params = {
        'action': 'pay',
        'amount': amount,
        'currency': 'UAH',
        'description': f"{description} #{order_id}",
        'order_id': str(order_id),
        'version': '3',
    }
    
    # Генеруємо сигнатуру
    data = base64.b64encode(json.dumps(params).encode('utf-8')).decode('utf-8')
    signature_string = LIQPAY_PRIVATE_KEY + data + LIQPAY_PRIVATE_KEY
    signature = base64.b64encode(hashlib.sha1(signature_string.encode('utf-8')).digest()).decode('utf-8')
    
    # Формуємо URL для оплати
    payment_url = f"https://www.liqpay.ua/api/3/checkout?data={data}&signature={signature}"
    
    return payment_url


def verify_payment_signature(data: str, signature: str) -> bool:
    """
    Перевірити підпис платежу від LiqPay
    
    Args:
        data: Дані від LiqPay (base64)
        signature: Підпис від LiqPay
    
    Returns:
        bool: True якщо підпис валідний
    """
    if not LIQPAY_PRIVATE_KEY:
        return False
    
    # Генеруємо очікуваний підпис
    signature_string = LIQPAY_PRIVATE_KEY + data + LIQPAY_PRIVATE_KEY
    expected_signature = base64.b64encode(
        hashlib.sha1(signature_string.encode('utf-8')).digest()
    ).decode('utf-8')
    
    return signature == expected_signature


def parse_payment_data(data: str) -> dict:
    """
    Розпарсити дані платежу від LiqPay
    
    Args:
        data: Дані від LiqPay (base64)
    
    Returns:
        dict: Розпарсені дані
    """
    try:
        decoded_data = base64.b64decode(data).decode('utf-8')
        return json.loads(decoded_data)
    except Exception as e:
        print(f"Помилка парсингу даних LiqPay: {e}")
        return None

