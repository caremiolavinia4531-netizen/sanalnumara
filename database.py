import sqlite3

DB_NAME = "shop.db"


def connect():
    return sqlite3.connect(DB_NAME)


def create_tables():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE,
        username TEXT,
        first_name TEXT,
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER,
        name TEXT NOT NULL,
        description TEXT,
        price REAL,
        stock INTEGER DEFAULT 0,
        FOREIGN KEY(category_id) REFERENCES categories(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product_id INTEGER,
        quantity INTEGER DEFAULT 1,
        status TEXT DEFAULT 'Beklemede',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(product_id) REFERENCES products(id)
    )
    """)

    conn.commit()
    conn.close()


def init_default_products():
    conn = connect()
    cursor = conn.cursor()
    
    # Tüm ülke kategorileri
    countries = [
        "Endonezya", "Hindistan", "Malezya", "Brezilya", 
        "Vietnam", "Filipinler", "Tayland", "Meksika", 
        "Güney Afrika", "Türkiye"
    ]
    
    for country in countries:
        cursor.execute("SELECT id FROM categories WHERE name = ?", (country,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO categories (name) VALUES (?)", (country,))
    
    conn.commit()

    # Ürünler, Açıklamaları, Fiyatları (250 TL) ve Başlangıç Stokları (300)
    products_to_add = [
        ("Endonezya", "Endonezya WhatsApp", "Endonezya numarası", 250.0, 300),
        ("Hindistan", "Hindistan WhatsApp", "Hindistan numarası", 250.0, 300),
        ("Malezya", "Malezya WhatsApp", "Malezya numarası", 250.0, 300),
        ("Brezilya", "Brezilya WhatsApp", "Brezilya numarası", 250.0, 300),
        ("Vietnam", "Vietnam WhatsApp", "Vietnam numarası", 250.0, 300),
        ("Filipinler", "Filipinler WhatsApp", "Filipinler numarası", 250.0, 300),
        ("Tayland", "Tayland WhatsApp", "Tayland numarası", 250.0, 300),
        ("Meksika", "Meksika WhatsApp", "Meksika numarası", 250.0, 300),
        ("Güney Afrika", "Güney Afrika WhatsApp", "Güney Afrika numarası", 250.0, 300),
        ("Türkiye", "Türkiye WhatsApp", "Türkiye numarası", 250.0, 300),
    ]

    for cat_name, prod_name, desc, price, stock in products_to_add:
        cursor.execute("SELECT id FROM categories WHERE name = ?", (cat_name,))
        cat = cursor.fetchone()
        if cat:
            cat_id = cat[0]
            cursor.execute("SELECT id, price, stock FROM products WHERE name = ?", (prod_name,))
            prod = cursor.fetchone()
            
            if not prod:
                # Ürün hiç yoksa fiyatı ve stoğuyla beraber ekle
                cursor.execute("""
                INSERT INTO products (category_id, name, description, price, stock)
                VALUES (?, ?, ?, ?, ?)
                """, (cat_id, prod_name, desc, price, stock))
            else:
                # Ürün zaten varsa fiyatını ve stoğunu güncelle (Fiyatların her zaman 250 TL kalmasını sağlar)
                cursor.execute("""
                UPDATE products 
                SET price = ?, stock = CASE WHEN stock = 0 THEN ? ELSE stock END 
                WHERE name = ?
                """, (price, stock, prod_name))

    conn.commit()
    conn.close()


def add_user(telegram_id, username, first_name):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR IGNORE INTO users (telegram_id, username, first_name)
    VALUES (?, ?, ?)
    """, (telegram_id, username, first_name))
    conn.commit()
    conn.close()


def get_product(name):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, name, description, price, stock
    FROM products
    WHERE name=?
    """, (name,))
    product = cursor.fetchone()
    conn.close()
    return product


def add_order(user_id, product_id, quantity=1):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO orders (user_id, product_id, quantity)
    VALUES (?, ?, ?)
    """, (user_id, product_id, quantity))
    conn.commit()
    conn.close()


def get_orders(user_id):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT 
        orders.id,
        products.name,
        orders.quantity,
        orders.status,
        orders.created_at
    FROM orders
    INNER JOIN products ON products.id = orders.product_id
    WHERE orders.user_id=?
    ORDER BY orders.id DESC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def update_stock(product_id, quantity=1):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE products
    SET stock = stock - ?
    WHERE id=? AND stock>=?
    """, (quantity, product_id, quantity))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success


def get_user_db_id(telegram_id):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE telegram_id=?", (telegram_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


create_tables()
init_default_products()