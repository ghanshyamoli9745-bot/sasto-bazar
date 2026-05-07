import sqlite3
import datetime

DB_NAME = 'products.db'

def get_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.execute('PRAGMA journal_mode=WAL') # Enable Write-Ahead Logging
    conn.row_factory = sqlite3.Row
    return conn

def setup_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT UNIQUE,
            image TEXT,
            old_price TEXT,
            new_price TEXT,
            discount_percent TEXT,
            rating TEXT,
            category TEXT,
            product_link TEXT,
            affiliate_link TEXT,
            clicks INTEGER DEFAULT 0,
            trending_score INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            clicks INTEGER DEFAULT 1,
            viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE,
            owner TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def generate_api_key(owner):
    import secrets
    key = f"ds_{secrets.token_urlsafe(32)}"
    conn = get_connection()
    c = conn.cursor()
    # Delete old key for this owner before creating new one
    c.execute("DELETE FROM api_keys WHERE owner = ?", (owner,))
    c.execute("INSERT INTO api_keys (key, owner) VALUES (?, ?)", (key, owner))
    conn.commit()
    conn.close()
    return key

def get_api_key_by_owner(owner):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT key FROM api_keys WHERE owner = ?", (owner,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def validate_api_key(key):
    if not key: return None
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT owner FROM api_keys WHERE key = ?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def insert_product(product, conn=None):
    if conn is None:
        conn = get_connection()
        should_close = True
    else:
        should_close = False
        
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO products (title, image, old_price, new_price, discount_percent, rating, category, product_link, affiliate_link)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (product['title'], product['image'], product.get('old_price', ''), product['new_price'], product.get('discount_percent', ''), product.get('rating', ''), product.get('category', ''), product['product_link'], product['affiliate_link']))
        conn.commit()
    except sqlite3.IntegrityError:
        c.execute('''
            UPDATE products 
            SET image = ?, old_price = ?, new_price = ?, discount_percent = ?, rating = ?, category = ?, product_link = ?, affiliate_link = ?
            WHERE title = ?
        ''', (product['image'], product.get('old_price', ''), product['new_price'], product.get('discount_percent', ''), product.get('rating', ''), product.get('category', ''), product['product_link'], product['affiliate_link'], product['title']))
        conn.commit()
    finally:
        if should_close:
            conn.close()

def get_products(category=None, search=None, order_by='id DESC', limit=50):
    conn = get_connection()
    c = conn.cursor()
    query = "SELECT * FROM products WHERE 1=1"
    params = []
    if category:
        query += " AND category = ?"
        params.append(category)
    if search:
        query += " AND title LIKE ?"
        params.append(f'%{search}%')
    
    # Special handling for discount sorting in SQL
    if 'discount' in order_by.lower():
        # Extracts number from "50% Off" or "-50%"
        order_by = "CAST(REPLACE(REPLACE(discount_percent, '% Off', ''), '-', '') AS INTEGER) DESC"
        
    query += f" ORDER BY {order_by} LIMIT ?"
    params.append(limit)
    
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_product(product_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def record_click(product_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE products SET clicks = clicks + 1, trending_score = trending_score + 5 WHERE id = ?", (product_id,))
    c.execute("INSERT INTO analytics (product_id) VALUES (?)", (product_id,))
    conn.commit()
    conn.close()

def add_to_wishlist(product_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO wishlist (product_id) VALUES (?)", (product_id,))
    conn.commit()
    conn.close()

def get_categories():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT DISTINCT category FROM products WHERE category IS NOT NULL AND category != ''")
    rows = c.fetchall()
    conn.close()
    return [row[0] for row in rows]

def get_revenue_stats():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM products")
    total_products = c.fetchone()[0] or 0
    c.execute("SELECT COALESCE(SUM(clicks), 0) FROM products")
    total_clicks = c.fetchone()[0] or 0
    c.execute("SELECT COUNT(*) FROM analytics WHERE date(viewed_at) = date('now')")
    today_clicks = c.fetchone()[0] or 0
    c.execute("SELECT COUNT(*) FROM analytics WHERE viewed_at >= datetime('now', '-7 days')")
    week_clicks = c.fetchone()[0] or 0
    c.execute("""
        SELECT COALESCE(SUM(
            CAST(REPLACE(REPLACE(REPLACE(COALESCE(new_price,'0'), 'Rs. ', ''), ',', ''), ' ', '') AS FLOAT)
            * clicks * 0.05
        ), 0) FROM products WHERE clicks > 0
    """)
    estimated_revenue = c.fetchone()[0] or 0
    c.execute("""
        SELECT id, title, new_price, clicks, category, image
        FROM products WHERE clicks > 0 ORDER BY clicks DESC LIMIT 5
    """)
    top_products = [dict(row) for row in c.fetchall()]
    c.execute("""
        SELECT category, SUM(clicks) as total_clicks
        FROM products WHERE clicks > 0 AND category IS NOT NULL AND category != ''
        GROUP BY category ORDER BY total_clicks DESC LIMIT 6
    """)
    category_stats = [dict(row) for row in c.fetchall()]
    conn.close()
    return {
        'total_products': total_products,
        'total_clicks': int(total_clicks),
        'today_clicks': int(today_clicks),
        'week_clicks': int(week_clicks),
        'estimated_revenue_npr': round(float(estimated_revenue)),
        'top_products': top_products,
        'category_stats': category_stats
    }
