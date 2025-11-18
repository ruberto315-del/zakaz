import aiosqlite
from datetime import datetime
from config import DATABASE_NAME, ORDER_STATUSES

class Database:
    def __init__(self):
        self.db_name = DATABASE_NAME
    
    async def init_db(self):
        """Ініціалізація бази даних"""
        async with aiosqlite.connect(self.db_name) as db:
            # Таблиця користувачів
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    phone TEXT,
                    address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблиця товарів
            await db.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    price REAL NOT NULL,
                    photo_id TEXT,
                    category TEXT,
                    is_available BOOLEAN DEFAULT 1,
                    is_preorder BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблиця корзини
            await db.execute("""
                CREATE TABLE IF NOT EXISTS cart (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER DEFAULT 1,
                    FOREIGN KEY (product_id) REFERENCES products(id)
                )
            """)
            
            # Таблиця замовлень
            await db.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    status TEXT DEFAULT 'pending',
                    total_price REAL NOT NULL,
                    phone TEXT,
                    address TEXT,
                    receipt_photo_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # Таблиця позицій замовлення
            await db.execute("""
                CREATE TABLE IF NOT EXISTS order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL,
                    FOREIGN KEY (order_id) REFERENCES orders(id),
                    FOREIGN KEY (product_id) REFERENCES products(id)
                )
            """)
            
            # Таблиця предзаказів
            await db.execute("""
                CREATE TABLE IF NOT EXISTS preorders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER DEFAULT 1,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (product_id) REFERENCES products(id)
                )
            """)
            
            # Таблиця FAQ
            await db.execute("""
                CREATE TABLE IF NOT EXISTS faq (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    order_index INTEGER DEFAULT 0
                )
            """)
            
            await db.commit()
    
    # Користувачі
    async def add_user(self, user_id, username=None, first_name=None):
        """Додати користувача"""
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute("""
                INSERT OR IGNORE INTO users (user_id, username, first_name)
                VALUES (?, ?, ?)
            """, (user_id, username, first_name))
            await db.commit()
    
    async def update_user_data(self, user_id, phone=None, address=None):
        """Оновити дані користувача"""
        async with aiosqlite.connect(self.db_name) as db:
            updates = []
            params = []
            if phone:
                updates.append("phone = ?")
                params.append(phone)
            if address:
                updates.append("address = ?")
                params.append(address)
            if updates:
                params.append(user_id)
                await db.execute(f"""
                    UPDATE users SET {', '.join(updates)}
                    WHERE user_id = ?
                """, params)
                await db.commit()
    
    async def get_user(self, user_id):
        """Отримати користувача"""
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        'user_id': row[0],
                        'username': row[1],
                        'first_name': row[2],
                        'phone': row[3],
                        'address': row[4],
                        'created_at': row[5]
                    }
                return None
    
    # Товари
    async def add_product(self, name, description, price, photo_id, category=None, is_preorder=False):
        """Додати товар"""
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute("""
                INSERT INTO products (name, description, price, photo_id, category, is_preorder)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, description, price, photo_id, category, is_preorder))
            await db.commit()
            return cursor.lastrowid
    
    async def get_products(self, category=None, available_only=True):
        """Отримати товари"""
        async with aiosqlite.connect(self.db_name) as db:
            query = "SELECT * FROM products WHERE 1=1"
            params = []
            if available_only:
                query += " AND is_available = 1"
            if category:
                query += " AND category = ?"
                params.append(category)
            query += " ORDER BY created_at DESC"
            
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                products = []
                for row in rows:
                    products.append({
                        'id': row[0],
                        'name': row[1],
                        'description': row[2],
                        'price': row[3],
                        'photo_id': row[4],
                        'category': row[5],
                        'is_available': row[6],
                        'is_preorder': row[7],
                        'created_at': row[8]
                    })
                return products
    
    async def get_product(self, product_id):
        """Отримати товар"""
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute("SELECT * FROM products WHERE id = ?", (product_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'name': row[1],
                        'description': row[2],
                        'price': row[3],
                        'photo_id': row[4],
                        'category': row[5],
                        'is_available': row[6],
                        'is_preorder': row[7],
                        'created_at': row[8]
                    }
                return None
    
    async def update_product(self, product_id, name=None, description=None, price=None, photo_id=None, is_available=None):
        """Оновити товар"""
        async with aiosqlite.connect(self.db_name) as db:
            updates = []
            params = []
            if name:
                updates.append("name = ?")
                params.append(name)
            if description:
                updates.append("description = ?")
                params.append(description)
            if price is not None:
                updates.append("price = ?")
                params.append(price)
            if photo_id:
                updates.append("photo_id = ?")
                params.append(photo_id)
            if is_available is not None:
                updates.append("is_available = ?")
                params.append(is_available)
            if updates:
                params.append(product_id)
                await db.execute(f"""
                    UPDATE products SET {', '.join(updates)}
                    WHERE id = ?
                """, params)
                await db.commit()
    
    # Корзина
    async def add_to_cart(self, user_id, product_id, quantity=1):
        """Додати товар до корзини"""
        async with aiosqlite.connect(self.db_name) as db:
            # Перевірити чи вже є товар в корзині
            async with db.execute("""
                SELECT id, quantity FROM cart 
                WHERE user_id = ? AND product_id = ?
            """, (user_id, product_id)) as cursor:
                row = await cursor.fetchone()
                if row:
                    # Оновити кількість
                    await db.execute("""
                        UPDATE cart SET quantity = quantity + ?
                        WHERE id = ?
                    """, (quantity, row[0]))
                else:
                    # Додати новий товар
                    await db.execute("""
                        INSERT INTO cart (user_id, product_id, quantity)
                        VALUES (?, ?, ?)
                    """, (user_id, product_id, quantity))
                await db.commit()
    
    async def get_cart(self, user_id):
        """Отримати корзину"""
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute("""
                SELECT c.id, c.product_id, c.quantity, p.name, p.price, p.photo_id
                FROM cart c
                JOIN products p ON c.product_id = p.id
                WHERE c.user_id = ?
            """, (user_id,)) as cursor:
                rows = await cursor.fetchall()
                cart_items = []
                for row in rows:
                    cart_items.append({
                        'cart_id': row[0],
                        'product_id': row[1],
                        'quantity': row[2],
                        'name': row[3],
                        'price': row[4],
                        'photo_id': row[5]
                    })
                return cart_items
    
    async def remove_from_cart(self, cart_id):
        """Видалити товар з корзини"""
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute("DELETE FROM cart WHERE id = ?", (cart_id,))
            await db.commit()
    
    async def clear_cart(self, user_id):
        """Очистити корзину"""
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
            await db.commit()
    
    async def update_cart_quantity(self, cart_id, quantity):
        """Оновити кількість товару в корзині"""
        async with aiosqlite.connect(self.db_name) as db:
            if quantity <= 0:
                await self.remove_from_cart(cart_id)
            else:
                await db.execute("UPDATE cart SET quantity = ? WHERE id = ?", (quantity, cart_id))
                await db.commit()
    
    # Замовлення
    async def create_order(self, user_id, total_price, phone, address, receipt_photo_id=None):
        """Створити замовлення"""
        async with aiosqlite.connect(self.db_name) as db:
            # Отримати товари з корзини
            cart_items = await self.get_cart(user_id)
            
            # Створити замовлення
            cursor = await db.execute("""
                INSERT INTO orders (user_id, total_price, phone, address, receipt_photo_id)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, total_price, phone, address, receipt_photo_id))
            order_id = cursor.lastrowid
            
            # Додати позиції замовлення
            for item in cart_items:
                await db.execute("""
                    INSERT INTO order_items (order_id, product_id, quantity, price)
                    VALUES (?, ?, ?, ?)
                """, (order_id, item['product_id'], item['quantity'], item['price']))
            
            # Очистити корзину
            await self.clear_cart(user_id)
            
            await db.commit()
            return order_id
    
    async def get_orders(self, user_id=None):
        """Отримати замовлення"""
        async with aiosqlite.connect(self.db_name) as db:
            if user_id:
                query = "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC"
                params = (user_id,)
            else:
                query = "SELECT * FROM orders ORDER BY created_at DESC"
                params = ()
            
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                orders = []
                for row in rows:
                    orders.append({
                        'id': row[0],
                        'user_id': row[1],
                        'status': row[2],
                        'total_price': row[3],
                        'phone': row[4],
                        'address': row[5],
                        'receipt_photo_id': row[6],
                        'created_at': row[7],
                        'updated_at': row[8]
                    })
                return orders
    
    async def get_order(self, order_id):
        """Отримати замовлення"""
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'user_id': row[1],
                        'status': row[2],
                        'total_price': row[3],
                        'phone': row[4],
                        'address': row[5],
                        'receipt_photo_id': row[6],
                        'created_at': row[7],
                        'updated_at': row[8]
                    }
                return None
    
    async def get_order_items(self, order_id):
        """Отримати позиції замовлення"""
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute("""
                SELECT oi.*, p.name
                FROM order_items oi
                JOIN products p ON oi.product_id = p.id
                WHERE oi.order_id = ?
            """, (order_id,)) as cursor:
                rows = await cursor.fetchall()
                items = []
                for row in rows:
                    items.append({
                        'id': row[0],
                        'order_id': row[1],
                        'product_id': row[2],
                        'quantity': row[3],
                        'price': row[4],
                        'name': row[5]
                    })
                return items
    
    async def update_order_status(self, order_id, status):
        """Оновити статус замовлення"""
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute("""
                UPDATE orders SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, order_id))
            await db.commit()
    
    # Предзакази
    async def create_preorder(self, user_id, product_id, quantity=1):
        """Створити предзаказ"""
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute("""
                INSERT INTO preorders (user_id, product_id, quantity)
                VALUES (?, ?, ?)
            """, (user_id, product_id, quantity))
            await db.commit()
            return cursor.lastrowid
    
    async def get_preorders(self, user_id=None):
        """Отримати предзакази"""
        async with aiosqlite.connect(self.db_name) as db:
            if user_id:
                query = """
                    SELECT po.*, p.name, p.price
                    FROM preorders po
                    JOIN products p ON po.product_id = p.id
                    WHERE po.user_id = ?
                    ORDER BY po.created_at DESC
                """
                params = (user_id,)
            else:
                query = """
                    SELECT po.*, p.name, p.price
                    FROM preorders po
                    JOIN products p ON po.product_id = p.id
                    ORDER BY po.created_at DESC
                """
                params = ()
            
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                preorders = []
                for row in rows:
                    preorders.append({
                        'id': row[0],
                        'user_id': row[1],
                        'product_id': row[2],
                        'quantity': row[3],
                        'status': row[4],
                        'created_at': row[5],
                        'name': row[6],
                        'price': row[7]
                    })
                return preorders
    
    async def update_preorder_status(self, preorder_id, status):
        """Оновити статус предзаказу"""
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute("UPDATE preorders SET status = ? WHERE id = ?", (status, preorder_id))
            await db.commit()
    
    # FAQ
    async def add_faq(self, question, answer, order_index=0):
        """Додати FAQ"""
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute("""
                INSERT INTO faq (question, answer, order_index)
                VALUES (?, ?, ?)
            """, (question, answer, order_index))
            await db.commit()
            return cursor.lastrowid
    
    async def get_faq(self):
        """Отримати FAQ"""
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute("SELECT * FROM faq ORDER BY order_index, id") as cursor:
                rows = await cursor.fetchall()
                faqs = []
                for row in rows:
                    faqs.append({
                        'id': row[0],
                        'question': row[1],
                        'answer': row[2],
                        'order_index': row[3]
                    })
                return faqs

db = Database()

