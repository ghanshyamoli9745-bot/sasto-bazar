import requests

# Use the credentials provided by the user
ADMIN_EMAIL = "ghanshyamoli922@gmail.com"
ADMIN_PASS = "9744556050"
BASE_URL = "http://127.0.0.1:5000"

def test_api():
    print("--- ⚡ Testing SastoBazar API Access ---")
    
    # 1. Login to get API Key
    print(f"[1] Authenticating as {ADMIN_EMAIL}...")
    login_res = requests.post(f"{BASE_URL}/api/generate-key", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASS
    })
    
    if login_res.status_code != 200:
        print(f"❌ Login failed! {login_res.text}")
        return

    api_key = login_res.json().get('api_key')
    print(f"✅ Authenticated! API Key: {api_key[:10]}...")

    # 2. Test Revenue Stats with the Key
    print("[2] Fetching Analytics with API Key...")
    stats_res = requests.get(f"{BASE_URL}/api/revenue-stats", headers={
        "X-API-KEY": api_key
    })

    if stats_res.status_code == 200:
        stats = stats_res.json()
        print("✅ API Success! Real Data Fetched:")
        print(f"   - Total Products: {stats.get('total_products')}")
        print(f"   - Total Clicks: {stats.get('total_clicks')}")
        print(f"   - Est. Revenue: Rs. {stats.get('estimated_revenue_npr')}")
    else:
        print(f"❌ API Request failed! {stats_res.status_code}: {stats_res.text}")

if __name__ == "__main__":
    try:
        test_api()
    except Exception as e:
        print(f"❌ Connection Error: {e}. (Make sure app.py is running)")
