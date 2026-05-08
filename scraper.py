import json
import time
import urllib.request
import urllib.parse
from database import insert_product
from affiliate import generate_affiliate_link

def fetch_daraz_category(category_name):
    """
    Fetches ONLY discounted product data for a given category.
    """
    search_query = category_name.replace('-', ' ')
    url = f"https://www.daraz.com.np/catalog/?q={urllib.parse.quote(search_query)}&ajax=true"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://www.daraz.com.np/'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            if 'mods' in data and 'listItems' in data['mods']:
                items = data['mods']['listItems']
                count = 0
                
                from database import get_connection
                conn = get_connection()
                try:
                    for item in items:
                        discount = item.get('discount', '')
                        if not discount: continue
                            
                        name = item.get('name')
                        price = item.get('price')
                        original_price = item.get('originalPrice')
                        if original_price: original_price = f"Rs. {original_price}"
                        
                        image = item.get('image')
                        item_url = item.get('itemUrl')
                        if item_url and item_url.startswith('//'): item_url = 'https:' + item_url
                        
                        if name and price:
                            affiliate_link = generate_affiliate_link(item_url)
                            rating = item.get('ratingScore')
                            reviews = item.get('review', '0') # Some APIs use 'review', some 'reviewCount'
                            
                            product_data = {
                                'title': name, 'image': image, 'old_price': original_price,
                                'new_price': f"Rs. {price}", 'discount_percent': discount,
                                'rating': str(rating) if rating else "0",
                                'category': category_name, 'product_link': item_url,
                                'affiliate_link': affiliate_link
                            }
                            insert_product(product_data, conn=conn)
                            
                            # Push to Firebase
                            try:
                                from firebase_manager import push_to_firebase
                                push_to_firebase(product_data)
                            except: pass
                            
                            count += 1
                            if count >= 100: break
                finally:
                    conn.close()
                return count
    except Exception as e:
        print(f"Error fetching category {category_name}: {e}")
    return 0

def scrape_daraz():
    """
    Main entry point for scraping all major Daraz categories.
    """
    categories = [
        'smartphones', 'laptops', 'tablets', 'monitors', 'cameras', 'gaming-consoles', 
        'headphones', 'smart-watches', 'pc-components', 'storage', 'projectors',
        'televisions', 'home-appliances', 'kitchen-appliances', 'ac-cooling', 'vacuums',
        'men-clothing', 'women-clothing', 'men-shoes', 'women-shoes', 
        'men-watches', 'women-watches', 'jewelry', 'bags-travel',
        # Health & Beauty
        'skincare', 'makeup', 'hair-care', 'personal-care', 'fragrances',
        # Home & Lifestyle
        'furniture', 'bedding', 'kitchenware', 'lighting', 'stationery', 'home-decor',
        # Babies & Toys
        'baby-care', 'toys-games', 'baby-clothing',
        # Groceries
        'groceries', 'beverages', 'breakfast', 'snacks', 'cleaning-supplies',
        # Sports & Motors
        'fitness-equipment', 'sports-gear', 'motors', 'tools-diy'
    ]
    total_new = 0
    for cat in categories:
        print(f"Scraping DEALS for: {cat}...")
        count = fetch_daraz_category(cat)
        total_new += count
        time.sleep(2) 
    print(f"Scraping completed. Found {total_new} total deals.")

def run_scraper_sync():
    """
    Wrapper for background task.
    """
    try:
        scrape_daraz()
    except Exception as e:
        print(f"Scraper error: {e}")

if __name__ == "__main__":
    run_scraper_sync()
