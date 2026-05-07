# DealSathi - Premium Daraz Affiliate Dashboard 🚀

DealSathi is an automated deal-hunting and affiliate marketing dashboard for Daraz. It automatically scrapes high-discount products, tracks trending deals, and provides a sleek interface for users to browse and save their favorite products.

![Dashboard Preview](https://via.placeholder.com/1200x600?text=DealSathi+Dashboard)

## ✨ Features

- **Automated Scraping**: Periodically fetches real-time deals from Daraz across multiple categories.
- **Revenue Dashboard**: (Admin) Track clicks, estimated revenue (5% commission), and category performance.
- **Premium Favorites**: A dedicated wishlist section with savings analytics and advanced sorting.
- **Smart Trending**: Products are ranked based on a combination of discount percentage and user click activity.
- **Search Engine**: Fast, category-filtered search for thousands of products.
- **Mobile First**: Fully responsive design with a native-app-like navigation for mobile users.

## 🛠️ Tech Stack

- **Backend**: Python, Flask, SQLite
- **Automation**: `schedule` for background tasks, `urllib` for high-performance scraping
- **Frontend**: Vanilla JS (ES6+), CSS3 (Modern Flex/Grid), HTML5
- **Icons**: FontAwesome 6

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Pip

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/dealsathi.git
   cd dealsathi
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Fill in your admin credentials.

4. Run the application:
   ```bash
   python app.py
   ```

5. Access the app:
   - **Frontend**: [http://localhost:5000](http://localhost:5000)
   - **Admin Dashboard**: Click the "DealSathi" logo 5 times to reveal the login modal.

## 📁 Project Structure

```text
├── app.py              # Main Flask application & background tasks
├── database.py         # SQLite schema & data access layer
├── scraper.py          # Daraz deal aggregation logic
├── static/
│   ├── app.js          # Frontend logic & state management
│   └── style.css       # Premium design system
├── templates/
│   ├── index.html      # Main dashboard
│   ├── favorites.html  # Wishlist & analytics
│   └── detail.html     # Product landing page
└── products.db         # Local database (gitignored)
```

## 🔒 Security

- Sensitive credentials are managed via environment variables.
- API endpoints for analytics are protected by X-API-KEY headers.
- Local storage is used for user-specific wishlist persistence.

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---
Created with ❤️ for smart shoppers.
