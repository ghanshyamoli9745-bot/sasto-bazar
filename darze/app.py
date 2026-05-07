import threading
import schedule
import time
from functools import wraps
from flask import Flask, jsonify, request, render_template
from database import setup_db, get_products, get_product, record_click, add_to_wishlist, get_categories, generate_api_key, validate_api_key, get_api_key_by_owner, get_revenue_stats
from scraper import run_scraper_sync
from fake_generator import generate_trending_scores

app = Flask(__name__)

setup_db()

# Admin Credentials
ADMIN_EMAIL = "ghanshyamoli922@gmail.com"
ADMIN_PASS = "9744556050"

def api_key_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-KEY')
        if not api_key:
            return jsonify({'error': 'API key is missing'}), 401
        owner = validate_api_key(api_key)
        if not owner:
            return jsonify({'error': 'Invalid API key'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/api/generate-key', methods=['POST'])
def api_gen_key():
    data = request.get_json()
    if not data or data.get('email') != ADMIN_EMAIL or data.get('password') != ADMIN_PASS:
        return jsonify({'error': 'Invalid credentials'}), 403
    
    # If regen is true, create new, else return existing if found
    if data.get('regen') == True:
        key = generate_api_key(ADMIN_EMAIL)
    else:
        key = get_api_key_by_owner(ADMIN_EMAIL)
        if not key: key = generate_api_key(ADMIN_EMAIL)
        
    return jsonify({'api_key': key, 'owner': ADMIN_EMAIL})

# Public API v1 (Protected by API Key)
@app.route('/api/v1/deals')
@api_key_required
def v1_deals():
    return jsonify(get_products(order_by='discount', limit=100))

@app.route('/api/v1/categories')
@api_key_required
def v1_categories():
    return jsonify(get_categories())

@app.route('/api/v1/mega-deals')
@api_key_required
def v1_mega_deals():
    products = get_products(order_by='discount', limit=50)
    products.sort(key=lambda x: x.get('trending_score', 0), reverse=True)
    return jsonify(products[:12])

@app.route('/api/revenue-stats')
@api_key_required
def api_revenue_stats():
    return jsonify(get_revenue_stats())

def bg_task():
    schedule.every(30).minutes.do(run_scraper_sync)
    schedule.every(30).minutes.do(generate_trending_scores)
    while True:
        schedule.run_pending()
        time.sleep(1)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/favorites')
def favorites_page():
    return render_template('favorites.html')

@app.route('/api/products')
def api_products():
    # Use SQL sorting for efficiency
    return jsonify(get_products(order_by='discount', limit=500))

@app.route('/api/featured')
def api_featured():
    # Use SQL to get top discounted, then pick trending in Python
    products = get_products(order_by='discount', limit=100)
    products.sort(key=lambda x: x.get('trending_score', 0), reverse=True)
    return jsonify(products[:12])

@app.route('/api/trending')
def api_trending():
    return jsonify(get_products(order_by='trending_score DESC', limit=20))

@app.route('/api/flash-sale')
def api_flash_sale():
    return jsonify(get_products(order_by='discount', limit=30))

@app.route('/api/search')
def api_search():
    q = request.args.get('q', '')
    return jsonify(get_products(search=q, order_by='discount'))

@app.route('/api/category/<name>')
def api_category(name):
    return jsonify(get_products(category=name, order_by='discount', limit=100))

@app.route('/api/categories')
def api_categories():
    return jsonify(get_categories())

@app.route('/api/product/<int:id>')
def api_product_data(id):
    product = get_product(id)
    if product:
        return jsonify(product)
    return jsonify({'error': 'Not found'}), 404

@app.route('/product/<int:id>')
def product_detail(id):
    return render_template('detail.html', product_id=id)

@app.route('/api/click/<int:id>', methods=['POST'])
def api_click(id):
    record_click(id)
    return jsonify({'status': 'success'})

@app.route('/api/wishlist/<int:id>', methods=['POST'])
def api_wishlist(id):
    add_to_wishlist(id)
    return jsonify({'status': 'success'})

@app.route('/api/stats')
def api_stats():
    return jsonify({'total_products': len(get_products())})

if __name__ == '__main__':
    import os
    if not os.environ.get('WERKZEUG_RUN_MAIN'):
        threading.Thread(target=run_scraper_sync, daemon=True).start()
        threading.Thread(target=bg_task, daemon=True).start()
    app.run(port=5000, debug=True)
