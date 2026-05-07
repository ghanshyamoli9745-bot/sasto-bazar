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

    card.innerHTML = `
        <div class="card-img-container" onclick="window.location.href='/product/${product.id}'">
            ${discountBadge}
            <img src="${product.image}" alt="${product.title}" loading="lazy">
        </div>
        <div class="card-content">
            <h3 onclick="window.location.href='/product/${product.id}'">${product.title}</h3>
            <div class="card-meta-row">
                <div class="card-rating">
                    ${parseFloat(product.rating) > 0 
                        ? `<i class="fas fa-star" style="color:#f9cb28"></i> <span>${product.rating}</span>` 
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

// --- Secret Admin Access ---
let logoClicks = 0;
function handleLogoClick() {
    logoClicks++;
    if (logoClicks === 5) {
        openAdminModal();
        logoClicks = 0;
    }
    setTimeout(() => { logoClicks = 0; }, 3000);
}

function openAdminModal() {
    document.getElementById('apiModal').style.display = 'flex';
    // Auto-load dashboard if key already in localStorage
    const savedKey = localStorage.getItem('ds_api_key');
    if (savedKey) {
        showRevenueDashboard(savedKey);
    }
}

function closeModal() {
    document.getElementById('apiModal').style.display = 'none';
    const r = document.getElementById('apiKeyResult');
    if (r) r.style.display = 'none';
}

async function generateKey() {
    const email = document.getElementById('adminEmail').value;
    const password = document.getElementById('adminPass').value;
    const resultDiv = document.getElementById('apiKeyResult');

    if (!email || !password) { alert('Please enter both email and password!'); return; }

    try {
        const response = await fetch('/api/generate-key', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await response.json();
        if (data.api_key) {
            localStorage.setItem('ds_api_key', data.api_key);
            showRevenueDashboard(data.api_key);
        } else {
            if (resultDiv) { resultDiv.textContent = '❌ Access Denied: Invalid Credentials!'; resultDiv.style.display = 'block'; }
        }
    } catch (error) {
        console.error(error);
        alert('Server Error: Could not generate key.');
    }
}

async function regenKey() {
    const key = localStorage.getItem('ds_api_key');
    if (!key) return;
    try {
        const res = await fetch('/api/generate-key', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: 'ghanshyamoli922@gmail.com', password: '9744556050', regen: true })
        });
        const data = await res.json();
        if (data.api_key) {
            localStorage.setItem('ds_api_key', data.api_key);
            showRevenueDashboard(data.api_key);
        }
    } catch(e) { console.error(e); }
}

function showRevenueDashboard(apiKey) {
    const authSection = document.getElementById('modalAuthSection');
    const dashboard = document.getElementById('revenueDashboard');
    if (authSection) authSection.style.display = 'none';
    if (dashboard) dashboard.style.display = 'block';
    const keyDisplay = document.getElementById('revApiKeyDisplay');
    if (keyDisplay) keyDisplay.textContent = apiKey.substring(0, 20) + '...';
    loadRevenueDashboard(apiKey);
}

async function loadRevenueDashboard(apiKey) {
    try {
        const res = await fetch('/api/revenue-stats', { headers: { 'X-API-KEY': apiKey } });
        if (!res.ok) throw new Error('Failed');
        const stats = await res.json();

        document.getElementById('revEarnings').textContent = `Rs. ${stats.estimated_revenue_npr.toLocaleString()}`;
        document.getElementById('revTotalClicks').textContent = stats.total_clicks.toLocaleString();
        document.getElementById('revTodayClicks').textContent = stats.today_clicks.toLocaleString();
        document.getElementById('revWeekClicks').textContent = stats.week_clicks.toLocaleString();
        document.getElementById('revTotalProducts').textContent = stats.total_products.toLocaleString();

        const topProd = document.getElementById('revTopProducts');
        if (topProd) {
            if (stats.top_products.length === 0) {
                topProd.innerHTML = '<div class="rev-empty-hint">No clicks recorded yet. Share your links!</div>';
            } else {
                topProd.innerHTML = stats.top_products.map(p => `
                    <div class="rev-prod-row">
                        <img src="${p.image}" class="rev-prod-img" onerror="this.style.display='none'">
                        <div class="rev-prod-info">
                            <div class="rev-prod-name">${p.title.substring(0, 45)}${p.title.length > 45 ? '...' : ''}</div>
                            <div class="rev-prod-price">${p.new_price}</div>
                        </div>
                        <div class="rev-prod-clicks">${p.clicks} <span>clicks</span></div>
                    </div>`).join('');
            }
        }

        const catEl = document.getElementById('revCategories');
        if (catEl && stats.category_stats.length > 0) {
            const max = stats.category_stats[0].total_clicks || 1;
            catEl.innerHTML = stats.category_stats.map(c => `
                <div class="rev-cat-row">
                    <span class="rev-cat-name">${c.category}</span>
                    <div class="rev-bar-wrap"><div class="rev-bar-fill" style="width:${Math.round((c.total_clicks/max)*100)}%"></div></div>
                    <span class="rev-cat-count">${c.total_clicks}</span>
                </div>`).join('');
        } else if (catEl) {
            catEl.innerHTML = '<div class="rev-empty-hint">No category data yet.</div>';
        }
    } catch(e) {
        console.error('Revenue load failed:', e);
    }
}
