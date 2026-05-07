import sqlite3
try:
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM products;")
    count = cursor.fetchone()[0]
    print(f"Total products: {count}")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
