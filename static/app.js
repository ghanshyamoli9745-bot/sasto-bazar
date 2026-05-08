document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('products-container')) {
        loadProducts();
        startTimer();
    }
    loadCategories();
    updateFavCount();
});

// Favorites (Wishlist) Logic
let favorites = JSON.parse(localStorage.getItem('daraz_favorites')) || [];

function updateFavCount() {
    const badge = document.getElementById('fav-count');
    if (badge) badge.textContent = favorites.length;
}

function toggleFavorite(product) {
    const isNowFav = favorites.findIndex(p => p.title === product.title) === -1;
    if (isNowFav) {
        favorites.push(product);
    } else {
        favorites = favorites.filter(p => p.title !== product.title);
    }
    localStorage.setItem('daraz_favorites', JSON.stringify(favorites));
    updateFavCount();
    
    // If we are on favorites page, re-render
    if (typeof renderFavoritesPage === 'function') renderFavoritesPage();
    
    // Update all heart icons on the page (Grid + Detail Page)
    syncHeartIcons(product.title, isNowFav);
}

function syncHeartIcons(productTitle, isFav) {
    // 1. Update Grid Cards
    const cards = document.querySelectorAll('.card, .fav-card');
    cards.forEach(card => {
        const titleEl = card.querySelector('h3');
        if (titleEl && titleEl.textContent === productTitle) {
            const btn = card.querySelector('.btn-wishlist, .btn-fav-large, .fav-del-btn');
            if (btn) {
                btn.classList.toggle('active', isFav);
                const icon = btn.querySelector('i');
                if (icon) icon.className = `fa${isFav ? 's' : 'r'} fa-heart`;
            }
        }
    });

    // 2. Update Detail Page Button (if visible)
    const detailBtn = document.getElementById('detail-fav-btn');
    if (detailBtn) {
        const detailTitle = document.querySelector('.detail-info h2');
        if (detailTitle && detailTitle.textContent === productTitle) {
            detailBtn.classList.toggle('active', isFav);
            const icon = detailBtn.querySelector('i');
            if (icon) icon.className = `fa${isFav ? 's' : 'r'} fa-heart`;
        }
    }
}

function clearFavorites() {
    if (confirm('Clear all items from your favorites?')) {
        favorites = [];
        localStorage.setItem('daraz_favorites', JSON.stringify(favorites));
        updateFavCount();
        if (typeof renderFavoritesPage === 'function') renderFavoritesPage();
        else location.reload();
    }
}

let timerInterval;
function startTimer() {
    const display = document.getElementById('timer-display');
    if (!display) return;

    // Use localStorage to persist timer across refreshes
    let startTime = localStorage.getItem('daraz_timer_start');
    const now = Math.floor(Date.now() / 1000);
    const duration = 3600; // 1 hour

    if (!startTime || (now - startTime) >= duration) {
        startTime = now;
        localStorage.setItem('daraz_timer_start', startTime);
    }

    if (timerInterval) clearInterval(timerInterval);

    timerInterval = setInterval(() => {
        const currentNow = Math.floor(Date.now() / 1000);
        const elapsed = currentNow - startTime;
        let timeLeft = duration - elapsed;

        if (timeLeft <= 0) {
            startTime = Math.floor(Date.now() / 1000);
            localStorage.setItem('daraz_timer_start', startTime);
            timeLeft = duration;
            loadProducts(); // Refresh deals
        }

        const min = Math.floor(timeLeft / 60);
        const sec = timeLeft % 60;
        display.textContent = `${min.toString().padStart(2,'0')}:${sec.toString().padStart(2,'0')}`;
    }, 1000);
}

async function fetchAndRender(url) {
    try {
        const container = document.getElementById('products-container');
        if (!container) return;
        container.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 100px 0;">Searching for best deals...</div>';
        const response = await fetch(url);
        const products = await response.json();
        renderProducts(products);
    } catch (error) { console.error(error); }
}

async function loadProducts() {
    const megaContainer = document.getElementById('mega-deals-container');
    const gridTitle = document.getElementById('grid-title');
    const mainContainer = document.getElementById('products-container');
    
    // Reset Search Input
    const searchInput = document.getElementById('searchInput');
    if (searchInput) searchInput.value = '';

    clearCategoryActive();
    setActiveFilter(0);
    
    if (megaContainer) megaContainer.style.display = 'block';
    if (gridTitle) gridTitle.textContent = 'All Discounted Products';
    if (mainContainer) mainContainer.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 100px 0;">Loading fresh deals...</div>';
    
    try {
        const [featRes, prodRes] = await Promise.all([fetch('/api/featured'), fetch('/api/products')]);
        if (!featRes.ok || !prodRes.ok) throw new Error('API Error');
        const featured = await featRes.json();
        const products = await prodRes.json();
        renderMegaDeals(featured);
        const featuredIds = featured.map(p => p.id);
        renderProducts(products.filter(p => !featuredIds.includes(p.id)));
    } catch (error) {
        if (mainContainer) mainContainer.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 100px 0; color: #ff4d4d;">Failed to load. ${error.message}</div>`;
    }
}

function renderMegaDeals(products) {
    const container = document.getElementById('mega-deals-grid');
    if (!container) return;
    container.innerHTML = '';
    products.forEach(product => container.appendChild(createProductCard(product)));
}

function searchProducts() {
    const q = document.getElementById('searchInput').value.trim();
    const megaContainer = document.getElementById('mega-deals-container');
    const gridTitle = document.getElementById('grid-title');
    
    if (!q) {
        loadProducts();
        return;
    }

    if (megaContainer) megaContainer.style.display = 'none';
    if (gridTitle) gridTitle.textContent = `Search: ${q}`;
    
    fetchAndRender(`/api/search?q=${encodeURIComponent(q)}`);
}

// Add Enter key support for search
document.getElementById('searchInput')?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') searchProducts();
});

function renderProducts(products) {
    const container = document.getElementById('products-container');
    if (!container) return;
    const title = document.getElementById('grid-title');
    container.innerHTML = '';
    if (title) container.appendChild(title);
    
    if (products.length === 0) {
        container.innerHTML += '<div style="grid-column: 1/-1; text-align: center; padding: 100px 20px; color: #666;">No products found matching your search.</div>';
        return;
    }
    
    products.forEach(product => container.appendChild(createProductCard(product)));
}

function createProductCard(product) {
    const isFav = favorites.some(p => p.title === product.title);
    const card = document.createElement('div');
    card.className = 'card';
    const discountBadge = product.discount_percent ? `<div class="discount-badge">${product.discount_percent} Off</div>` : '';
    
    // Stringify product safely for the onclick attribute
    const prodStr = JSON.stringify(product).replace(/'/g, "&apos;").replace(/"/g, '&quot;');

    // Format Rating to 1 decimal place safely
    let ratingVal = "0.0";
    if (product.rating) {
        const match = String(product.rating).match(/(\d+(\.\d+)?)/);
        if (match) ratingVal = parseFloat(match[0]).toFixed(1);
    }

    card.innerHTML = `
        <div class="card-img-container" onclick="window.location.href='/product/${product.id}'">
            ${discountBadge}
            <img src="${product.image}" alt="${product.title}" loading="lazy">
        </div>
        <div class="card-content">
            <h3 onclick="window.location.href='/product/${product.id}'">${product.title}</h3>
            <div class="card-meta-row">
                <div class="card-rating">
                    ${parseFloat(ratingVal) > 0 
                        ? `<i class="fas fa-star" style="color:#f9cb28"></i> <span>${ratingVal}</span>` 
                        : `<span style="color:#555; font-size:0.75rem">No reviews</span>`}
                </div>
                <div class="card-cat-badge">${product.category.replace('-',' ')}</div>
            </div>
            <div class="price-container">
                <span class="price">${product.new_price}</span>
                ${product.old_price ? `<span class="old-price">${product.old_price}</span>` : ''}
            </div>
            <div class="card-actions">
                <a href="${product.affiliate_link}" target="_blank" class="btn-buy" onclick="trackClick(${product.id})">Grab Deal</a>
                <button onclick='toggleFavorite(${prodStr})' class="btn-wishlist ${isFav ? 'active' : ''}">
                    <i class="fa${isFav ? 's' : 'r'} fa-heart"></i>
                </button>
            </div>
        </div>
    `;
    return card;
}

function trackClick(id) { fetch(`/api/click/${id}`, { method: 'POST' }); }
function loadTrending() { /* ... similar logic ... */ fetchAndRender('/api/trending'); }
function loadFlashSale() { /* ... similar logic ... */ fetchAndRender('/api/flash-sale'); }
function clearCategoryActive() { document.querySelectorAll('.categories-list button').forEach(b => b.classList.remove('active')); }
function searchProducts() { const q = document.getElementById('searchInput').value; fetchAndRender(`/api/search?q=${q}`); }
function setActiveFilter(i) { document.querySelectorAll('.filters button').forEach((b,idx) => b.classList.toggle('active', i===idx)); }
async function loadCategories() { const r = await fetch('/api/categories'); const c = await r.json(); renderCategories(c); }
function renderCategories(c) {
    const container = document.getElementById('categories-container');
    if (!container) return;
    const label = container.querySelector('.category-label');
    container.innerHTML = ''; if (label) container.appendChild(label);
    c.forEach(cat => {
        const b = document.createElement('button');
        b.textContent = cat.charAt(0).toUpperCase() + cat.slice(1).replace('-',' ');
        b.onclick = () => loadByCategory(cat);
        container.appendChild(b);
    });
}
function loadByCategory(n) { fetchAndRender(`/api/category/${n}`); }

// --- ADMIN DASHBOARD LOGIC (PRO VERSION) ---
// Admin logic moved to specialized templates/admin_secure.html
let adminApiKey = localStorage.getItem('sasto_admin_key');
let adminActiveTab = 'overview';
let logoClicks = 0;

function handleLogoClick() {
    logoClicks++;
    if (logoClicks >= 5) {
        logoClicks = 0;
        window.location.href = '/admin';
    }
    setTimeout(() => logoClicks = 0, 3000);
}

async function switchAdminTab(tab) {
    adminActiveTab = tab;
    
    // Update active UI (Sidebar)
    document.querySelectorAll('.menu-item').forEach(item => {
        const itemTab = item.dataset.tab || (item.getAttribute('onclick') ? item.getAttribute('onclick').match(/'([^']+)'/)[1] : null);
        item.classList.toggle('active', itemTab === tab);
    });

    const contentArea = document.getElementById('admin-main-content');
    if (!contentArea) return;

    contentArea.innerHTML = `
        <div class="admin-loading" style="text-align: center; padding: 100px;">
            <div class="admin-spinner"></div>
            <p style="color: #666; margin-top: 15px;">Synchronizing with server...</p>
        </div>
    `;

    try {
        if (tab === 'overview' || tab === 'analytics') {
            const stats = await fetchAdminStats();
            if (stats.error) throw new Error(stats.error);
            renderAdminOverview(stats);
        } else if (tab === 'products') {
            contentArea.innerHTML = `
                <div class="admin-section">
                    <h2 style="color: white; margin-bottom: 10px;">Product Engine</h2>
                    <p style="color: #666; margin-bottom: 30px;">Manage background scrapers and indexing speed.</p>
                    <div class="admin-card">
                        <h4 style="color: white; margin-bottom: 15px;">System Maintenance</h4>
                        <div style="display: flex; gap: 10px;">
                            <button class="btn-primary-admin" style="width: auto;" onclick="location.reload()">
                                <i class="fas fa-sync"></i> Refresh Cache
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }
    } catch (e) {
        console.error("Admin Load Error:", e);
        contentArea.innerHTML = `
            <div style="text-align: center; padding: 100px; color: #ff4d4d;">
                <i class="fas fa-exclamation-circle" style="font-size: 3rem; margin-bottom: 20px;"></i>
                <h3>Session Connection Failed</h3>
                <p style="color: #666; margin-bottom: 20px;">We couldn't retrieve your analytics. Please try logging in again.</p>
                <button onclick="logoutAdmin()" class="btn-primary-admin" style="width: auto;">Login Again</button>
            </div>
        `;
    }
}

async function fetchAdminStats() {
    const response = await fetch('/api/revenue-stats', {
        headers: { 'X-API-KEY': adminApiKey }
    });
    if (!response.ok) throw new Error("Unauthorized");
    return await response.json();
}

function renderAdminOverview(data) {
    const contentArea = document.getElementById('admin-main-content');
    
    const rev = data.estimated_revenue_rs || data.estimated_revenue_npr || 0;
    const cat_stats = data.category_performance || data.category_stats || [];

    contentArea.innerHTML = `
        <div class="admin-welcome-row" style="margin-bottom: 35px;">
            <h1 style="font-size: 1.8rem; font-weight: 800; color: white;">System Overview</h1>
            <p style="color: #666;">Tracking real-time performance of SastoBazar Affiliate Engine.</p>
        </div>

        <div class="admin-stats-row">
            <div class="admin-card" style="border-left: 4px solid #00ff88;">
                <div class="card-title"><i class="fas fa-wallet" style="margin-right: 8px;"></i> Total Earnings</div>
                <div class="card-val" style="color: #00ff88">Rs. ${rev.toLocaleString()}</div>
                <div style="font-size: 0.8rem; color: #555;">Commission balance (Live)</div>
            </div>
            <div class="admin-card" style="border-left: 4px solid var(--accent-color);">
                <div class="card-title"><i class="fas fa-users" style="margin-right: 8px;"></i> User Engagement</div>
                <div class="card-val" style="color: white">${data.total_clicks}</div>
                <div style="font-size: 0.8rem; color: #555;">Total link interactions</div>
            </div>
            <div class="admin-card" style="border-left: 4px solid #3498db;">
                <div class="card-title"><i class="fas fa-bolt" style="margin-right: 8px;"></i> Today's Velocity</div>
                <div class="card-val" style="color: #3498db">${data.today_clicks}</div>
                <div style="font-size: 0.8rem; color: #555;">Clicks in last 24 hours</div>
            </div>
            <div class="admin-card" style="border-left: 4px solid #f1c40f;">
                <div class="card-title"><i class="fas fa-archive" style="margin-right: 8px;"></i> Active Index</div>
                <div class="card-val" style="color: #f1c40f">${data.total_products}</div>
                <div style="font-size: 0.8rem; color: #555;">Products in local cache</div>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: 1.8fr 1.2fr; gap: 30px;">
            <div class="admin-card" style="background: rgba(255,255,255,0.02);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px;">
                    <h4 style="color: white; font-weight: 800;"><i class="fas fa-star" style="color: #ff4d4d; margin-right: 10px;"></i> High Velocity Deals</h4>
                    <span style="font-size: 0.75rem; color: #555; background: #1a1a1a; padding: 4px 12px; border-radius: 20px;">TOP 5 PERFORMERS</span>
                </div>
                <div class="admin-table-wrapper">
                    ${data.top_products.length > 0 ? data.top_products.map((p, i) => `
                        <div style="display: flex; align-items: center; justify-content: space-between; padding: 15px 0; border-bottom: 1px solid #222;">
                            <div style="display: flex; align-items: center; gap: 18px;">
                                <span style="color: #333; font-weight: 900; font-size: 1.2rem;">0${i+1}</span>
                                <img src="${p.image}" style="width: 45px; height: 45px; border-radius: 10px; object-fit: cover; border: 1px solid #333;">
                                <div style="display: flex; flex-direction: column;">
                                    <span style="font-size: 0.95rem; color: #fff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 280px; font-weight: 600;">${p.title}</span>
                                    <span style="font-size: 0.75rem; color: #555;">ID: #DB-${p.id || 'N/A'}</span>
                                </div>
                            </div>
                            <div style="text-align: right;">
                                <div style="color: white; font-weight: 800;">${p.clicks} <span style="font-size: 0.7rem; color: #666; font-weight: 400;">CLICKS</span></div>
                                <div style="height: 4px; width: 60px; background: #222; border-radius: 2px; margin-top: 5px; overflow: hidden;">
                                    <div style="height: 100%; background: #00ff88; width: ${Math.min(100, (p.clicks / (data.top_products[0].clicks || 1)) * 100)}%;"></div>
                                </div>
                            </div>
                        </div>
                    `).join('') : '<p style="color: #444; text-align: center; padding: 60px;">System waiting for initial click data...</p>'}
                </div>
            </div>

            <div class="admin-card" style="background: rgba(255,255,255,0.02);">
                <h4 style="color: white; font-weight: 800; margin-bottom: 25px;"><i class="fas fa-chart-pie" style="color: var(--accent-color); margin-right: 10px;"></i> Market Distribution</h4>
                <div style="margin-top: 10px;">
                    ${cat_stats.length > 0 ? cat_stats.map(c => `
                        <div style="margin-bottom: 22px;">
                            <div style="display: flex; justify-content: space-between; font-size: 0.9rem; margin-bottom: 8px;">
                                <span style="text-transform: capitalize; color: #bbb; font-weight: 500;">${(c.category || 'Other').replace('-', ' ')}</span>
                                <span style="color: white; font-weight: 800;">${c.total_clicks || c.count || 0} <span style="font-size: 0.7rem; color: #555;">PTS</span></span>
                            </div>
                            <div style="height: 8px; background: #1a1a1a; border-radius: 10px; overflow: hidden; border: 1px solid #222;">
                                <div style="height: 100%; background: var(--accent-gradient); width: ${Math.min(100, ((c.total_clicks || c.count || 0) / (data.total_clicks || 1)) * 350)}%; border-radius: 10px; box-shadow: 0 0 10px rgba(255, 77, 77, 0.2);"></div>
                            </div>
                        </div>
                    `).join('') : '<p style="color: #444; text-align: center; padding: 60px;">Collecting category insights...</p>'}
                </div>
                <div style="margin-top: 30px; padding: 15px; background: rgba(0,255,136,0.05); border-radius: 12px; border: 1px solid rgba(0,255,136,0.1);">
                    <p style="font-size: 0.8rem; color: #00ff88; text-align: center;"><i class="fas fa-info-circle"></i> Best performing category: <strong style="text-transform: capitalize;">${cat_stats.length > 0 ? cat_stats[0].category.replace('-', ' ') : 'N/A'}</strong></p>
                </div>
            </div>
        </div>
    `;
}

// Check for existing session on load
window.addEventListener('load', () => {
    if (adminApiKey) {
        console.log("Admin session restored.");
    }
});
