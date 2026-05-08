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
            is_custom INTEGER DEFAULT 0,
            custom_id TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_cat ON products(category)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_tit ON products(title)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_clks ON products(clicks)')
    
    # Create Virtual Table for Ultra-Fast Search (FTS5)
    try:
        c.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS products_fts USING fts5(
                id UNINDEXED,
                title,
                category,
                content='products',
                content_rowid='id'
            )
        ''')
        # Sync FTS table
        c.execute("INSERT INTO products_fts(products_fts) VALUES('rebuild')")
    except: pass
    # Create analytics table
    c.execute('''
        CREATE TABLE IF NOT EXISTS analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            clicks INTEGER DEFAULT 1,
            viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')
    # Create API keys table
    c.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE,
            owner TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Create wishlist table
    c.execute('''
        CREATE TABLE IF NOT EXISTS wishlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id)
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
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT key FROM api_keys WHERE owner = ?", (owner,))
        row = c.fetchone()
        conn.close()
        return row[0] if row else None
    except Exception as e:
        print(f"DB Error (get_api_key): {e}")
        return None

def validate_api_key(key):
    if not key: return None
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT owner FROM api_keys WHERE key = ?", (key,))
        row = c.fetchone()
        conn.close()
        return row[0] if row else None
    except Exception as e:
        print(f"DB Error (validate_api_key): {e}")
        return None

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
    
    # Special handling for discount sorting in SQL
    if 'discount' in order_by.lower():
        # Extracts number from "50% Off" or "-50%"
        order_by = "CAST(REPLACE(REPLACE(discount_percent, '% Off', ''), '-', '') AS INTEGER) DESC"
    query = "SELECT p.* FROM products p"
    params = []
    
    if search:
        # Use FTS5 for smart search with Prefix Match (*) for fuzzy feel
        query = """
            SELECT p.* FROM products p
            JOIN products_fts f ON p.id = f.rowid
            WHERE (f.products_fts MATCH ? OR p.custom_id = ? OR p.id = ?)
        """
        # Append * to words for partial matching (e.g. mob* matches mobile)
        fts_search = " ".join([f"{w}*" for w in search.split()])
        params = [fts_search, search, search]
    else:
        query = "SELECT * FROM products WHERE 1=1"
        
    if category and category.lower() != 'all':
        query += " AND category = ?"
        params.append(category)
        
    # Ordering
    query += f" ORDER BY {order_by} LIMIT ?"
    params.append(limit)
    
    try:
        c.execute(query, params)
    except:
        # Last resort fallback if FTS fails
        c.execute("SELECT * FROM products WHERE title LIKE ? ORDER BY " + order_by + " LIMIT ?", (f'%{search}%', limit))
    
    rows = c.fetchall()
    conn.close()
    
    products = []
    for row in rows:
        p = dict(row)
        # Format Rating to 1 decimal place
        if p['rating'] and p['rating'] != '0':
            try:
                # Extract numbers from string like "4.5079 (12 reviews)"
                import re
                nums = re.findall(r"\d+\.\d+|\d+", p['rating'])
                if nums:
                    val = float(nums[0])
                    p['rating'] = f"{round(val, 1)}"
                    if len(nums) > 1: p['rating'] += f" ({nums[1]} reviews)"
            except: pass
        products.append(p)
    return products

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
def update_product_link(product_id, new_link):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE products SET affiliate_link = ?, is_custom = 1 WHERE id = ?", (new_link, product_id))
    conn.commit()
    conn.close()
    return True
