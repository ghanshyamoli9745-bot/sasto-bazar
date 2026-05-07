import random
from database import get_connection

def generate_trending_scores():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM products")
    products = c.fetchall()
    for product in products:
        score = random.randint(1, 100)
        c.execute("UPDATE products SET trending_score = ? WHERE id = ?", (score, product['id']))
    conn.commit()
    conn.close()

def fake_ai_recommendation(products):
    if not products:
        return []
    return random.sample(products, min(5, len(products)))
