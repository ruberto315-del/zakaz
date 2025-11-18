import asyncpg
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

# Умовний імпорт aiosqlite тільки для SQLite (спочатку встановлюємо None)
aiosqlite = None

# Імпортуємо змінні з config
from config import DATABASE_NAME, ORDER_STATUSES, USE_POSTGRES, DATABASE_URL

# Тепер імпортуємо aiosqlite тільки якщо потрібен SQLite
if not USE_POSTGRES:
    try:
        import aiosqlite
    except ImportError:
        logger.warning("aiosqlite не встановлено. Встановіть для використання SQLite: pip install aiosqlite")

def _check_aiosqlite():
    """Перевірити чи aiosqlite доступний"""
    if aiosqlite is None:
        raise ImportError("aiosqlite не встановлено. Встановіть для використання SQLite: pip install aiosqlite")

class Database:
    def __init__(self):
        self.use_postgres = USE_POSTGRES
        self.db_url = DATABASE_URL if USE_POSTGRES else None
        self.db_name = DATABASE_NAME
        self.pool = None
    
    async def init_db(self):
        """Ініціалізація бази даних"""
        logger.info(f"Ініціалізація БД: USE_POSTGRES={self.use_postgres}, DATABASE_URL={'встановлено' if self.db_url else 'не встановлено'}")
        if self.use_postgres:
            if not self.db_url:
                logger.error("USE_POSTGRES=True, але DATABASE_URL не встановлено! Перевірте змінні оточення.")
                raise ValueError("DATABASE_URL не встановлено для PostgreSQL")
            await self._init_postgres()
        else:
            logger.info("Використовується SQLite")
            await self._init_sqlite()
    
    async def _init_postgres(self):
        """Ініціалізація PostgreSQL"""
        try:
            # Створюємо connection pool
            self.pool = await asyncpg.create_pool(self.db_url, min_size=1, max_size=10)
            logger.info("Підключено до PostgreSQL")
            
            async with self.pool.acquire() as conn:
                # Таблиця користувачів
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id BIGINT PRIMARY KEY,
                        username VARCHAR(255),
                        first_name VARCHAR(255),
                        phone VARCHAR(50),
                        address TEXT,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """)
                
                # Таблиця товарів
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS products (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        description TEXT,
                        price DECIMAL(10, 2) NOT NULL,
                        photo_id VARCHAR(255),
                        category VARCHAR(100),
                        is_available BOOLEAN DEFAULT TRUE,
                        is_preorder BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """)
                
                # Таблиця корзини
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS cart (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        product_id INTEGER NOT NULL,
                        quantity INTEGER DEFAULT 1,
                        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
                    )
                """)
                
                # Таблиця замовлень
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS orders (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        status VARCHAR(50) DEFAULT 'pending',
                        total_price DECIMAL(10, 2) NOT NULL,
                        phone VARCHAR(50),
                        address TEXT,
                        receipt_photo_id VARCHAR(255),
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW(),
                        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                    )
                """)
                
                # Таблиця позицій замовлення
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS order_items (
                        id SERIAL PRIMARY KEY,
                        order_id INTEGER NOT NULL,
                        product_id INTEGER NOT NULL,
                        quantity INTEGER NOT NULL,
                        price DECIMAL(10, 2) NOT NULL,
                        FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
                    )
                """)
                
                # Таблиця предзаказів
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS preorders (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        product_id INTEGER NOT NULL,
                        quantity INTEGER DEFAULT 1,
                        status VARCHAR(50) DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT NOW(),
                        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
                    )
                """)
                
                # Таблиця FAQ
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS faq (
                        id SERIAL PRIMARY KEY,
                        question TEXT NOT NULL,
                        answer TEXT NOT NULL,
                        order_index INTEGER DEFAULT 0
                    )
                """)
                
                logger.info("Таблиці PostgreSQL створені/перевірені")
        except Exception as e:
            logger.error(f"Помилка ініціалізації PostgreSQL: {e}")
            raise
    
    async def _init_sqlite(self):
        """Ініціалізація SQLite (для локальної розробки)"""
        _check_aiosqlite()
        # Налаштування для уникнення блокування бази даних
        async with aiosqlite.connect(self.db_name, timeout=30.0) as db:
            # Увімкнути WAL режим для кращої продуктивності та уникнення блокувань
            await db.execute("PRAGMA journal_mode=WAL")
            await db.execute("PRAGMA busy_timeout=30000")
            await db.execute("PRAGMA synchronous=NORMAL")
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
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO users (user_id, username, first_name)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (user_id) DO NOTHING
                """, user_id, username, first_name)
        else:
            _check_aiosqlite()
            async with aiosqlite.connect(self.db_name, timeout=30.0) as db:
                await db.execute("PRAGMA busy_timeout=30000")
                await db.execute("""
                    INSERT OR IGNORE INTO users (user_id, username, first_name)
                    VALUES (?, ?, ?)
                """, (user_id, username, first_name))
                await db.commit()
    
    async def update_user_data(self, user_id, phone=None, address=None):
        """Оновити дані користувача"""
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                updates = []
                params = []
                param_num = 1
                if phone:
                    updates.append(f"phone = ${param_num}")
                    params.append(phone)
                    param_num += 1
                if address:
                    updates.append(f"address = ${param_num}")
                    params.append(address)
                    param_num += 1
                if updates:
                    params.append(user_id)
                    await conn.execute(f"""
                        UPDATE users SET {', '.join(updates)}
                        WHERE user_id = ${param_num}
                    """, *params)
        else:
            _check_aiosqlite()
            async with aiosqlite.connect(self.db_name, timeout=30.0) as db:
                await db.execute("PRAGMA busy_timeout=30000")
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
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
                if row:
                    return dict(row)
                return None
        else:
            _check_aiosqlite()
            async with aiosqlite.connect(self.db_name, timeout=30.0) as db:
                await db.execute("PRAGMA busy_timeout=30000")
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
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                product_id = await conn.fetchval("""
                    INSERT INTO products (name, description, price, photo_id, category, is_preorder)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING id
                """, name, description, float(price), photo_id, category, is_preorder)
                return product_id
        else:
            _check_aiosqlite()
            async with aiosqlite.connect(self.db_name, timeout=30.0) as db:
                await db.execute("PRAGMA busy_timeout=30000")
                cursor = await db.execute("""
                    INSERT INTO products (name, description, price, photo_id, category, is_preorder)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (name, description, price, photo_id, category, is_preorder))
                await db.commit()
                return cursor.lastrowid
    
    async def get_products(self, category=None, available_only=True):
        """Отримати товари"""
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                query = "SELECT * FROM products WHERE 1=1"
                params = []
                param_num = 1
                if available_only:
                    query += " AND is_available = TRUE"
                if category:
                    query += f" AND category = ${param_num}"
                    params.append(category)
                    param_num += 1
                query += " ORDER BY created_at DESC"
                
                rows = await conn.fetch(query, *params)
                products = [dict(row) for row in rows]
                # Конвертуємо Decimal в float для сумісності
                for p in products:
                    if 'price' in p and hasattr(p['price'], '__float__'):
                        p['price'] = float(p['price'])
                return products
        else:
            _check_aiosqlite()
            async with aiosqlite.connect(self.db_name, timeout=30.0) as db:
                await db.execute("PRAGMA busy_timeout=30000")
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
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow("SELECT * FROM products WHERE id = $1", product_id)
                if row:
                    product = dict(row)
                    if 'price' in product and hasattr(product['price'], '__float__'):
                        product['price'] = float(product['price'])
                    return product
                return None
        else:
            _check_aiosqlite()
            async with aiosqlite.connect(self.db_name, timeout=30.0) as db:
                await db.execute("PRAGMA busy_timeout=30000")
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
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                updates = []
                params = []
                param_num = 1
                if name:
                    updates.append(f"name = ${param_num}")
                    params.append(name)
                    param_num += 1
                if description:
                    updates.append(f"description = ${param_num}")
                    params.append(description)
                    param_num += 1
                if price is not None:
                    updates.append(f"price = ${param_num}")
                    params.append(float(price))
                    param_num += 1
                if photo_id:
                    updates.append(f"photo_id = ${param_num}")
                    params.append(photo_id)
                    param_num += 1
                if is_available is not None:
                    updates.append(f"is_available = ${param_num}")
                    params.append(is_available)
                    param_num += 1
                if updates:
                    params.append(product_id)
                    await conn.execute(f"""
                        UPDATE products SET {', '.join(updates)}
                        WHERE id = ${param_num}
                    """, *params)
        else:
            _check_aiosqlite()
            async with aiosqlite.connect(self.db_name, timeout=30.0) as db:
                await db.execute("PRAGMA busy_timeout=30000")
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
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT id, quantity FROM cart 
                    WHERE user_id = $1 AND product_id = $2
                """, user_id, product_id)
                if row:
                    await conn.execute("""
                        UPDATE cart SET quantity = quantity + $1
                        WHERE id = $2
                    """, quantity, row['id'])
                else:
                    await conn.execute("""
                        INSERT INTO cart (user_id, product_id, quantity)
                        VALUES ($1, $2, $3)
                    """, user_id, product_id, quantity)
        else:
            _check_aiosqlite()
            async with aiosqlite.connect(self.db_name, timeout=30.0) as db:
                await db.execute("PRAGMA busy_timeout=30000")
                async with db.execute("""
                    SELECT id, quantity FROM cart 
                    WHERE user_id = ? AND product_id = ?
                """, (user_id, product_id)) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        await db.execute("""
                            UPDATE cart SET quantity = quantity + ?
                            WHERE id = ?
                        """, (quantity, row[0]))
                    else:
                        await db.execute("""
                            INSERT INTO cart (user_id, product_id, quantity)
                            VALUES (?, ?, ?)
                        """, (user_id, product_id, quantity))
                    await db.commit()
    
    async def get_cart(self, user_id):
        """Отримати корзину"""
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT c.id, c.product_id, c.quantity, p.name, p.price, p.photo_id
                    FROM cart c
                    JOIN products p ON c.product_id = p.id
                    WHERE c.user_id = $1
                """, user_id)
                cart_items = []
                for row in rows:
                    price = float(row['price']) if hasattr(row['price'], '__float__') else row['price']
                    cart_items.append({
                        'cart_id': row['id'],
                        'product_id': row['product_id'],
                        'quantity': row['quantity'],
                        'name': row['name'],
                        'price': price,
                        'photo_id': row['photo_id']
                    })
                return cart_items
        else:
            _check_aiosqlite()
            async with aiosqlite.connect(self.db_name, timeout=30.0) as db:
                await db.execute("PRAGMA busy_timeout=30000")
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
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                await conn.execute("DELETE FROM cart WHERE id = $1", cart_id)
        else:
            _check_aiosqlite()
            async with aiosqlite.connect(self.db_name, timeout=30.0) as db:
                await db.execute("PRAGMA busy_timeout=30000")
                await db.execute("DELETE FROM cart WHERE id = ?", (cart_id,))
                await db.commit()
    
    async def clear_cart(self, user_id):
        """Очистити корзину"""
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                await conn.execute("DELETE FROM cart WHERE user_id = $1", user_id)
        else:
            _check_aiosqlite()
            async with aiosqlite.connect(self.db_name, timeout=30.0) as db:
                await db.execute("PRAGMA busy_timeout=30000")
                await db.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
                await db.commit()
    
    async def update_cart_quantity(self, cart_id, quantity):
        """Оновити кількість товару в корзині"""
        if quantity <= 0:
            await self.remove_from_cart(cart_id)
        else:
            if self.use_postgres:
                async with self.pool.acquire() as conn:
                    await conn.execute("UPDATE cart SET quantity = $1 WHERE id = $2", quantity, cart_id)
            else:
                async with aiosqlite.connect(self.db_name, timeout=30.0) as db:
                    await db.execute("PRAGMA busy_timeout=30000")
                    await db.execute("UPDATE cart SET quantity = ? WHERE id = ?", (quantity, cart_id))
                    await db.commit()
    
    # Замовлення
    async def create_order(self, user_id, total_price, phone, address, receipt_photo_id=None):
        """Створити замовлення"""
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    cart_items = await self.get_cart(user_id)
                    
                    order_id = await conn.fetchval("""
                        INSERT INTO orders (user_id, total_price, phone, address, receipt_photo_id)
                        VALUES ($1, $2, $3, $4, $5)
                        RETURNING id
                    """, user_id, float(total_price), phone, address, receipt_photo_id)
                    
                    for item in cart_items:
                        await conn.execute("""
                            INSERT INTO order_items (order_id, product_id, quantity, price)
                            VALUES ($1, $2, $3, $4)
                        """, order_id, item['product_id'], item['quantity'], float(item['price']))
                    
                    await self.clear_cart(user_id)
                    return order_id
        else:
            _check_aiosqlite()
            async with aiosqlite.connect(self.db_name, timeout=30.0) as db:
                await db.execute("PRAGMA busy_timeout=30000")
                cart_items = await self.get_cart(user_id)
                
                cursor = await db.execute("""
                    INSERT INTO orders (user_id, total_price, phone, address, receipt_photo_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, total_price, phone, address, receipt_photo_id))
                order_id = cursor.lastrowid
                
                for item in cart_items:
                    await db.execute("""
                        INSERT INTO order_items (order_id, product_id, quantity, price)
                        VALUES (?, ?, ?, ?)
                    """, (order_id, item['product_id'], item['quantity'], item['price']))
                
                await self.clear_cart(user_id)
                await db.commit()
                return order_id
    
    async def get_orders(self, user_id=None):
        """Отримати замовлення"""
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                if user_id:
                    rows = await conn.fetch("SELECT * FROM orders WHERE user_id = $1 ORDER BY created_at DESC", user_id)
                else:
                    rows = await conn.fetch("SELECT * FROM orders ORDER BY created_at DESC")
                
                orders = []
                for row in rows:
                    order = dict(row)
                    if 'total_price' in order and hasattr(order['total_price'], '__float__'):
                        order['total_price'] = float(order['total_price'])
                    orders.append(order)
                return orders
        else:
            _check_aiosqlite()
            async with aiosqlite.connect(self.db_name, timeout=30.0) as db:
                await db.execute("PRAGMA busy_timeout=30000")
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
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow("SELECT * FROM orders WHERE id = $1", order_id)
                if row:
                    order = dict(row)
                    if 'total_price' in order and hasattr(order['total_price'], '__float__'):
                        order['total_price'] = float(order['total_price'])
                    return order
                return None
        else:
            _check_aiosqlite()
            async with aiosqlite.connect(self.db_name, timeout=30.0) as db:
                await db.execute("PRAGMA busy_timeout=30000")
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
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT oi.*, p.name
                    FROM order_items oi
                    JOIN products p ON oi.product_id = p.id
                    WHERE oi.order_id = $1
                """, order_id)
                items = []
                for row in rows:
                    item = dict(row)
                    if 'price' in item and hasattr(item['price'], '__float__'):
                        item['price'] = float(item['price'])
                    items.append(item)
                return items
        else:
            _check_aiosqlite()
            async with aiosqlite.connect(self.db_name, timeout=30.0) as db:
                await db.execute("PRAGMA busy_timeout=30000")
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
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    UPDATE orders SET status = $1, updated_at = NOW()
                    WHERE id = $2
                """, status, order_id)
        else:
            _check_aiosqlite()
            async with aiosqlite.connect(self.db_name, timeout=30.0) as db:
                await db.execute("PRAGMA busy_timeout=30000")
                await db.execute("""
                    UPDATE orders SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (status, order_id))
                await db.commit()
    
    # Предзакази
    async def create_preorder(self, user_id, product_id, quantity=1):
        """Створити предзаказ"""
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                preorder_id = await conn.fetchval("""
                    INSERT INTO preorders (user_id, product_id, quantity)
                    VALUES ($1, $2, $3)
                    RETURNING id
                """, user_id, product_id, quantity)
                return preorder_id
        else:
            _check_aiosqlite()
            async with aiosqlite.connect(self.db_name, timeout=30.0) as db:
                await db.execute("PRAGMA busy_timeout=30000")
                cursor = await db.execute("""
                    INSERT INTO preorders (user_id, product_id, quantity)
                    VALUES (?, ?, ?)
                """, (user_id, product_id, quantity))
                await db.commit()
                return cursor.lastrowid
    
    async def get_preorders(self, user_id=None):
        """Отримати предзакази"""
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                if user_id:
                    rows = await conn.fetch("""
                        SELECT po.*, p.name, p.price
                        FROM preorders po
                        JOIN products p ON po.product_id = p.id
                        WHERE po.user_id = $1
                        ORDER BY po.created_at DESC
                    """, user_id)
                else:
                    rows = await conn.fetch("""
                        SELECT po.*, p.name, p.price
                        FROM preorders po
                        JOIN products p ON po.product_id = p.id
                        ORDER BY po.created_at DESC
                    """)
                
                preorders = []
                for row in rows:
                    preorder = dict(row)
                    if 'price' in preorder and hasattr(preorder['price'], '__float__'):
                        preorder['price'] = float(preorder['price'])
                    preorders.append(preorder)
                return preorders
        else:
            _check_aiosqlite()
            async with aiosqlite.connect(self.db_name, timeout=30.0) as db:
                await db.execute("PRAGMA busy_timeout=30000")
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
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                await conn.execute("UPDATE preorders SET status = $1 WHERE id = $2", status, preorder_id)
        else:
            _check_aiosqlite()
            async with aiosqlite.connect(self.db_name, timeout=30.0) as db:
                await db.execute("PRAGMA busy_timeout=30000")
                await db.execute("UPDATE preorders SET status = ? WHERE id = ?", (status, preorder_id))
                await db.commit()
    
    # FAQ
    async def add_faq(self, question, answer, order_index=0):
        """Додати FAQ"""
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                faq_id = await conn.fetchval("""
                    INSERT INTO faq (question, answer, order_index)
                    VALUES ($1, $2, $3)
                    RETURNING id
                """, question, answer, order_index)
                return faq_id
        else:
            _check_aiosqlite()
            async with aiosqlite.connect(self.db_name, timeout=30.0) as db:
                await db.execute("PRAGMA busy_timeout=30000")
                cursor = await db.execute("""
                    INSERT INTO faq (question, answer, order_index)
                    VALUES (?, ?, ?)
                """, (question, answer, order_index))
                await db.commit()
                return cursor.lastrowid
    
    async def get_faq(self):
        """Отримати FAQ"""
        if self.use_postgres:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("SELECT * FROM faq ORDER BY order_index, id")
                return [dict(row) for row in rows]
        else:
            _check_aiosqlite()
            async with aiosqlite.connect(self.db_name, timeout=30.0) as db:
                await db.execute("PRAGMA busy_timeout=30000")
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
    
    async def close(self):
        """Закрити підключення"""
        if self.use_postgres and self.pool:
            await self.pool.close()

db = Database()
