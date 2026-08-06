import os
import psycopg2

# Render üzerindeki DATABASE_URL ortam değişkenini alır
DATABASE_URL = os.environ.get("DATABASE_URL")


def connect():
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL ortam değişkeni bulunamadı! Render Environment ayarlarına eklediğinizden emin olun.")
    return psycopg2.connect(DATABASE_URL, sslmode="require")


def create_tables():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        telegram_id BIGINT UNIQUE,
        username VARCHAR(255),
        first_name VARCHAR(255),
        balance DOUBLE PRECISION DEFAULT 0.0,
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id SERIAL PRIMARY KEY,
        category_id INTEGER REFERENCES categories(id),
        name VARCHAR(255) NOT NULL,
        description TEXT,
        price DOUBLE PRECISION,
        stock INTEGER DEFAULT 0
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id),
        product_id INTEGER REFERENCES products(id),
        quantity INTEGER DEFAULT 1,
        status VARCHAR(100) DEFAULT 'Beklemede',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    cursor.close()
    conn.close()


def init_default_products():
    """Ürünler veritabanında yoksa oluşturur, var olan stoklara ve fiyatlara dokunmaz."""
    conn = connect()
    cursor = conn.cursor()
    
    countries = [
        "Endonezya", "Hindistan", "Malezya", "Brezilya", 
        "Vietnam", "Filipinler", "Tayland", "Meksika", 
        "Güney Afrika", "Türkiye"
    ]
    
    for country in countries:
        cursor.execute("SELECT id FROM categories WHERE name = %s", (country,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO categories (name) VALUES (%s)", (country,))
    
    conn.commit()

    products_to_add = [
        ("Endonezya", "Endonezya WhatsApp", "Endonezya numarası", 250.0, 0),
        ("Hindistan", "Hindistan WhatsApp", "Hindistan numarası", 250.0, 0),
        ("Malezya", "Malezya WhatsApp", "Malezya numarası", 250.0, 0),
        ("Brezilya", "Brezilya WhatsApp", "Brezilya numarası", 250.0, 0),
        ("Vietnam", "Vietnam WhatsApp", "Vietnam numarası", 250.0, 0),
        ("Filipinler", "Filipinler WhatsApp", "Filipinler numarası", 250.0, 0),
        ("Tayland", "Tayland WhatsApp", "Tayland numarası", 250.0, 0),
        ("Meksika", "Meksika WhatsApp", "Meksika numarası", 250.0, 0),
        ("Güney Afrika", "Güney Afrika WhatsApp", "Güney Afrika numarası", 250.0, 0),
        ("Türkiye", "Türkiye WhatsApp", "Türkiye numarası", 250.0, 0),
    ]

    for cat_name, prod_name, desc, price, default_stock in products_to_add:
        cursor.execute("SELECT id FROM categories WHERE name = %s", (cat_name,))
        cat = cursor.fetchone()
        if cat:
            cat_id = cat[0]
            cursor.execute("SELECT id FROM products WHERE name = %s", (prod_name,))
            prod = cursor.fetchone()
            
            if not prod:
                cursor.execute("""
                INSERT INTO products (category_id, name, description, price, stock)
                VALUES (%s, %s, %s, %s, %s)
                """, (cat_id, prod_name, desc, price, default_stock))

    conn.commit()
    cursor.close()
    conn.close()


def add_user(telegram_id, username, first_name):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO users (telegram_id, username, first_name)
    VALUES (%s, %s, %s)
    ON CONFLICT (telegram_id) DO NOTHING;
    """, (int(telegram_id), username, first_name))
    conn.commit()
    cursor.close()
    conn.close()


def get_product(name):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, name, description, price, stock
    FROM products
    WHERE name=%s
    """, (name,))
    product = cursor.fetchone()
    cursor.close()
    conn.close()
    return product


def add_order(user_id, product_id, quantity=1):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO orders (user_id, product_id, quantity)
    VALUES (%s, %s, %s)
    """, (user_id, product_id, quantity))
    conn.commit()
    cursor.close()
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
    WHERE orders.user_id=%s
    ORDER BY orders.id DESC
    """, (user_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def update_stock(product_id, quantity=1):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE products
    SET stock = stock - %s
    WHERE id=%s AND stock>=%s
    """, (quantity, product_id, quantity))
    conn.commit()
    success = cursor.rowcount > 0
    cursor.close()
    conn.close()
    return success


def get_user_db_id(telegram_id):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE telegram_id=%s", (int(telegram_id),))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row[0] if row else None


def update_order_status(order_id, status):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE orders
    SET status = %s
    WHERE id = %s
    """, (status, int(order_id)))
    conn.commit()
    cursor.close()
    conn.close()


# --- BAKİYE VE İADE FONKSİYONLARI ---

def get_user_balance(telegram_id):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE telegram_id=%s", (int(telegram_id),))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return float(row[0]) if row and row[0] is not None else 0.0


def add_user_balance(telegram_id, amount):
    conn = connect()
    cursor = conn.cursor()
    t_id = int(telegram_id)
    amt = float(amount)
    
    cursor.execute("SELECT balance FROM users WHERE telegram_id=%s", (t_id,))
    row = cursor.fetchone()
    
    if row is None:
        cursor.execute(
            "INSERT INTO users (telegram_id, balance) VALUES (%s, %s)", 
            (t_id, amt)
        )
    else:
        cursor.execute(
            "UPDATE users SET balance = balance + %s WHERE telegram_id=%s", 
            (amt, t_id)
        )
        
    conn.commit()
    cursor.close()
    conn.close()


def deduct_user_balance(telegram_id, amount):
    t_id = int(telegram_id)
    amt = float(amount)
    current_balance = get_user_balance(t_id)
    
    if current_balance >= amt:
        conn = connect()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET balance = balance - %s WHERE telegram_id=%s", 
            (amt, t_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    return False


create_tables()
init_default_products()
    
