// RANZZSTORE LUXURY - MAIN JAVASCRIPT

function formatRupiah(number) {
    return 'Rp ' + Number(number).toLocaleString('id-ID');
}

// Show Toast Alert using SweetAlert2
function showToast(message, icon = 'success') {
    if (typeof Swal !== 'undefined') {
        const Toast = Swal.mixin({
            toast: true,
            position: 'top-end',
            showConfirmButton: false,
            timer: 3000,
            timerProgressBar: true,
            background: '#131720',
            color: '#f8fafc',
            iconColor: icon === 'success' ? '#c5a059' : '#ef4444',
            customClass: {
                popup: 'border border-[rgba(197,160,89,0.3)] shadow-2xl rounded-xl'
            }
        });
        Toast.fire({
            icon: icon,
            title: message
        });
    } else {
        alert(message);
    }
}

// Cart Drawer Controller
function toggleCartDrawer() {
    const drawer = document.getElementById('cart-drawer');
    const overlay = document.getElementById('cart-overlay');
    if (!drawer) return;

    if (drawer.classList.contains('translate-x-full')) {
        drawer.classList.remove('translate-x-full');
        drawer.classList.add('translate-x-0');
        overlay.classList.remove('hidden');
        loadDrawerCart();
    } else {
        drawer.classList.remove('translate-x-0');
        drawer.classList.add('translate-x-full');
        overlay.classList.add('hidden');
    }
}

// Load Drawer Cart Contents Dynamically
async function loadDrawerCart() {
    const container = document.getElementById('drawer-cart-items');
    const subtotalEl = document.getElementById('drawer-subtotal');
    if (!container) return;

    container.innerHTML = `
        <div class="flex flex-col items-center justify-center py-12 text-zinc-400">
            <i data-lucide="loader-2" class="w-8 h-8 animate-spin text-[#c5a059] mb-3"></i>
            <p class="text-sm">Memuat tas belanja...</p>
        </div>
    `;
    if (window.lucide) lucide.createIcons();

    try {
        const res = await fetch('/cart');
        const html = await res.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        
        // Grab items from /cart DOM
        const items = doc.querySelectorAll('.cart-row-item');
        const subtotalText = doc.getElementById('cart-summary-subtotal')?.innerText || 'Rp 0';

        if (items.length === 0) {
            container.innerHTML = `
                <div class="text-center py-16 px-4">
                    <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-500">
                        <i data-lucide="shopping-bag" class="w-8 h-8"></i>
                    </div>
                    <h4 class="font-serif text-lg text-zinc-200 mb-1">Tas Belanja Kosong</h4>
                    <p class="text-xs text-zinc-400 mb-6">Jelajahi mahakarya dan koleksi eksklusif kami.</p>
                    <a href="/shop" onclick="toggleCartDrawer()" class="inline-block px-5 py-2.5 text-xs font-semibold uppercase tracking-wider rounded-lg btn-gold">Mulai Belanja</a>
                </div>
            `;
            if (subtotalEl) subtotalEl.innerText = 'Rp 0';
        } else {
            let htmlItems = '';
            items.forEach(item => {
                const img = item.dataset.image;
                const name = item.dataset.name;
                const price = item.dataset.price;
                const qty = item.dataset.qty;
                const variant = item.dataset.variant;
                const key = item.dataset.key;

                htmlItems += `
                    <div class="flex items-center gap-4 py-3 border-b border-zinc-800/80">
                        <img src="${img}" alt="${name}" class="w-16 h-16 object-cover rounded-lg border border-zinc-800">
                        <div class="flex-1 min-w-0">
                            <h5 class="text-sm font-medium text-zinc-200 truncate">${name}</h5>
                            ${variant ? `<p class="text-xs text-[#c5a059]">${variant}</p>` : ''}
                            <p class="text-xs text-zinc-400 mt-1">${qty} × ${price}</p>
                        </div>
                        <button onclick="removeCartItem('${key}', true)" class="p-1 text-zinc-500 hover:text-rose-400 transition">
                            <i data-lucide="trash-2" class="w-4 h-4"></i>
                        </button>
                    </div>
                `;
            });
            container.innerHTML = htmlItems;
            if (subtotalEl) subtotalEl.innerText = subtotalText;
        }
        if (window.lucide) lucide.createIcons();
    } catch (e) {
        container.innerHTML = `<p class="text-center text-xs text-rose-400 py-6">Gagal memuat keranjang.</p>`;
    }
}

// Add To Cart Function
async function addToCart(productId, quantity = 1, variant = '') {
    try {
        const response = await fetch('/api/cart/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                product_id: productId,
                quantity: quantity,
                variant: variant
            })
        });

        const result = await response.json();
        if (result.success) {
            showToast(result.message, 'success');
            // Update cart badges
            const badges = document.querySelectorAll('.cart-badge');
            badges.forEach(b => {
                b.innerText = result.cart_count;
                b.classList.remove('hidden');
            });
            // Auto open drawer to delight user
            toggleCartDrawer();
        } else {
            showToast(result.message || 'Gagal menambahkan ke keranjang', 'error');
        }
    } catch (error) {
        showToast('Terjadi kesalahan jaringan.', 'error');
    }
}

// Update Cart Quantity
async function updateCartQuantity(key, quantity) {
    try {
        const response = await fetch('/api/cart/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key: key, quantity: quantity })
        });
        const res = await response.json();
        if (res.success) {
            window.location.reload();
        } else {
            showToast(res.message, 'error');
        }
    } catch (err) {
        showToast('Gagal mengubah kuantitas.', 'error');
    }
}

// Remove Cart Item
async function removeCartItem(key, reloadDrawer = false) {
    try {
        const response = await fetch('/api/cart/remove', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key: key })
        });
        const res = await response.json();
        if (res.success) {
            showToast('Produk dihapus dari tas belanja.', 'info');
            if (reloadDrawer) {
                loadDrawerCart();
                // update badge
                fetch('/cart').then(() => window.location.reload());
            } else {
                window.location.reload();
            }
        }
    } catch (err) {
        showToast('Gagal menghapus item.', 'error');
    }
}

// Voucher Tool
async function applyVoucher() {
    const input = document.getElementById('voucher-input');
    if (!input || !input.value.trim()) {
        showToast('Silakan ketik kode voucher', 'warning');
        return;
    }

    try {
        const res = await fetch('/api/voucher/apply', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code: input.value.trim() })
        });
        const data = await res.json();
        if (data.success) {
            showToast(data.message, 'success');
            setTimeout(() => window.location.reload(), 800);
        } else {
            showToast(data.message, 'error');
        }
    } catch (e) {
        showToast('Gagal menerapkan voucher.', 'error');
    }
}

async function removeVoucher() {
    try {
        const res = await fetch('/api/voucher/remove', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            showToast('Voucher dilepas.', 'info');
            setTimeout(() => window.location.reload(), 500);
        }
    } catch (e) {
        window.location.reload();
    }
}

// Wishlist Functionality (Stored in LocalStorage)
function getWishlist() {
    try {
        return JSON.parse(localStorage.getItem('ranzzstore_wishlist') || localStorage.getItem('aurelia_wishlist') || '[]');
    } catch (e) {
        return [];
    }
}

function updateWishlistBadge() {
    const list = getWishlist();
    const badges = document.querySelectorAll('.wishlist-badge');
    badges.forEach(b => {
        b.innerText = list.length;
        if (list.length > 0) b.classList.remove('hidden');
        else b.classList.add('hidden');
    });

    // Update heart icons on cards
    document.querySelectorAll('.btn-wishlist').forEach(btn => {
        const pid = parseInt(btn.dataset.productId);
        const icon = btn.querySelector('svg') || btn.querySelector('i');
        if (list.includes(pid)) {
            btn.classList.add('text-rose-500');
            btn.classList.remove('text-zinc-400');
        } else {
            btn.classList.remove('text-rose-500');
            btn.classList.add('text-zinc-400');
        }
    });
}

function toggleWishlist(productId, productName = 'Produk') {
    let list = getWishlist();
    const id = parseInt(productId);
    if (list.includes(id)) {
        list = list.filter(item => item !== id);
        showToast(`${productName} dihapus dari daftar impian.`, 'info');
    } else {
        list.push(id);
        showToast(`${productName} disimpan ke daftar impian.`, 'success');
    }
    localStorage.setItem('ranzzstore_wishlist', JSON.stringify(list));
    updateWishlistBadge();
}

// Initialize on DOM Ready
document.addEventListener('DOMContentLoaded', () => {
    if (window.lucide) lucide.createIcons();
    updateWishlistBadge();
});
