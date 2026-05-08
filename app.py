import threading
import schedule
import time
import os
from dotenv import load_dotenv
from functools import wraps
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from database import setup_db, get_products, get_product, record_click, add_to_wishlist, get_categories, generate_api_key, validate_api_key, get_api_key_by_owner, get_revenue_stats, get_connection
from scraper import run_scraper_sync
from fake_generator import generate_trending_scores
from firebase_manager import sync_from_firebase, push_stats_to_firebase, verify_admin_firebase

load_dotenv()

app = Flask(__name__)
CORS(app)

setup_db()

# Admin Credentials (Move to .env for production)
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "ghanshyamoli922@gmail.com")
ADMIN_PASS = os.getenv("ADMIN_PASS", "9744556050")

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
    print("DEBUG: Received Login Request")
    try:
        data = request.get_json()
        print(f"DEBUG: Login Data: {data}")
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        email = data.get('email')
        password = data.get('password')
        
        # Priority 1: Hardcoded Local Check (Instant)
        target_email = "ghanshyamoli922@gmail.com"
        target_pass = "9744556050"
        local_ok = (email == target_email and password == target_pass)

        # Priority 2: Firebase Check (Async-like)
        firebase_ok = False
        if not local_ok:
            try:
                firebase_ok = verify_admin_firebase(email, password)
            except: pass

        if local_ok or firebase_ok:
            print(f"DEBUG: Login Success (Local: {local_ok}, Firebase: {firebase_ok})")
            try:
                owner = email
                key = get_api_key_by_owner(owner)
                if not key:
                    key = generate_api_key(owner)
                return jsonify({'api_key': key, 'status': 'success'})
            except Exception as db_err:
                print(f"DEBUG: DB Error: {db_err}")
                return jsonify({'api_key': 'ds_emergency_key_123', 'status': 'success'})
        else:
            print(f"DEBUG: Login Failed for {email}")
            return jsonify({'error': 'Invalid Credentials'}), 401
    except Exception as e:
        print(f"DEBUG: CRITICAL LOGIN ERROR: {e}")
        return jsonify({'error': 'Internal Server Error', 'details': str(e)}), 500

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
    # Initial Sync on Start
    try:
        sync_from_firebase()
    except: pass
    
    schedule.every(30).minutes.do(run_scraper_sync)
    schedule.every(30).minutes.do(generate_trending_scores)
    schedule.every(5).minutes.do(sync_from_firebase) # Sync from cloud every 5 mins
    
    while True:
        schedule.run_pending()
        # Push current stats to Firebase for remote monitoring
        try:
            stats = get_revenue_stats()
            push_stats_to_firebase(stats)
        except: pass
        time.sleep(1)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin_page():
    # Pointing to the new secure template to bypass cache
    response = render_template('admin_secure.html')
    from flask import make_response
    resp = make_response(response)
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return resp

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
    if not q: return jsonify([])
    
    products = get_products(search=q, order_by='discount')
    
    # If fewer than 5 results, trigger a background scrape for this keyword
    if len(products) < 5:
        threading.Thread(target=run_scraper_sync, args=(q,)).start()
        
    return jsonify(products)

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

@app.route('/api/admin/update-link', methods=['POST'])
@api_key_required
def api_update_link():
    data = request.json
    p_id = data.get('id')
    new_link = data.get('link')
    custom_id = data.get('custom_id')
    
    if p_id:
        conn = get_connection()
        c = conn.cursor()
        if new_link:
            c.execute("UPDATE products SET affiliate_link = ?, is_custom = 1 WHERE id = ?", (new_link, p_id))
        if custom_id:
            c.execute("UPDATE products SET custom_id = ? WHERE id = ?", (custom_id, p_id))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success'})
    return jsonify({'error': 'Invalid data'}), 400

# Initialize Background Tasks for Production (Gunicorn)
def start_background_tasks():
    # Only start threads in the main process
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        print("Starting background scraper and scheduler...")
        threading.Thread(target=run_scraper_sync, daemon=True).start()
        threading.Thread(target=bg_task, daemon=True).start()

start_background_tasks()

if __name__ == '__main__':
    app.run(port=5000, debug=True)
