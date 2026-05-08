import pyrebase
import json
from database import insert_product, get_connection

# User's Firebase Configuration
firebaseConfig = {
  "apiKey": "AIzaSyAgwk1f1jGKICbuExi4o-dErMQIxImWmLw",
  "authDomain": "loan-management-apps.firebaseapp.com",
  "databaseURL": "https://loan-management-apps-default-rtdb.firebaseio.com",
  "projectId": "loan-management-apps",
  "storageBucket": "loan-management-apps.firebasestorage.app",
  "messagingSenderId": "167835472146",
  "appId": "1:167835472146:web:d803067a054fb1b8a1e3cb",
  "measurementId": "G-L6W1GW15BV"
}

firebase = pyrebase.initialize_app(firebaseConfig)
db = firebase.database()

def sync_from_firebase():
    """Pulls data from Firebase and updates Local SQLite (File Base)"""
    print("🔄 Syncing from Firebase to Local Storage...")
    try:
        products = db.child("products").get().val()
        if products:
            conn = get_connection()
            # If products is a dict (likely), iterate through it
            if isinstance(products, dict):
                for p_id in products:
                    insert_product(products[p_id], conn=conn)
            print(f"✅ Successfully synced {len(products)} products from Firebase.")
        else:
            print("ℹ️ No products found in Firebase to sync.")
    except Exception as e:
        print(f"❌ Firebase Sync Error: {e}")

def push_to_firebase(product_data):
    """Pushes a single product to Firebase for Real-time consistency"""
    try:
        # Use title as a unique-ish key or a sanitized version of it
        clean_title = "".join(filter(str.isalnum, product_data['title']))[:50]
        db.child("products").child(clean_title).set(product_data)
    except Exception as e:
        print(f"❌ Firebase Push Error: {e}")

def push_stats_to_firebase(stats):
    """Pushes analytics to Firebase so you can monitor from anywhere"""
    try:
        db.child("admin_stats").set(stats)
    except Exception as e:
        print(f"❌ Firebase Stats Error: {e}")

def verify_admin_firebase(email, password):
    """Checks credentials against Firebase Realtime DB"""
    try:
        # Check in 'admins' node
        # Note: In a real app, you'd store hashed passwords
        admins = db.child("admins").get().val()
        if admins:
            for uid, info in admins.items():
                if info.get('email') == email and info.get('password') == password:
                    return True
        return False
    except Exception as e:
        print(f"❌ Firebase Auth Error: {e}")
        return False
