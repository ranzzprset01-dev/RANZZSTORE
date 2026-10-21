import os
import json
import csv
import io
import datetime
import random
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for, session, 
    jsonify, flash, make_response, send_file, Response
)
from werkzeug.security import generate_password_hash, check_password_hash
from models import get_db, init_db

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'ranzzstore-secret-key-2026-99x')

# Currency Formatter Filter
@app.template_filter('rupiah')
def rupiah_filter(value):
    try:
        val = int(round(float(value)))
        return f"Rp {val:,}".replace(",", ".")
    except (ValueError, TypeError):
        return f"Rp {value}"

@app.template_filter('from_json')
def from_json_filter(value):
    if not value:
        return []
    try:
        return json.loads(value)
    except Exception:
        return []

# Helper: Get Current User
def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user

# Helper: Get Store Settings
def get_store_settings():
    conn = get_db()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    conn.close()
    return {row['key']: row['value'] for row in rows}

# Global context processor
@app.context_processor
def inject_global_data():
    conn = get_db()
    categories = conn.execute("SELECT * FROM categories ORDER BY name ASC").fetchall()
    settings = {row['key']: row['value'] for row in conn.execute("SELECT key, value FROM settings").fetchall()}
    
    # Calculate cart count
    cart = session.get('cart', {})
    cart_count = sum(item.get('quantity', 1) for item in cart.values())
    conn.close()
    
    return {
        'nav_categories': categories,
        'current_user': get_current_user(),
        'settings': settings,
        'cart_count': cart_count,
        'now_year': datetime.datetime.now().year
    }

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user or user['role'] != 'admin':
            flash("Akses terbatas! Silakan masuk sebagai administrator.", "danger")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# ==========================================
# PUBLIC FRONT-END ROUTES
# ==========================================

@app.route('/')
def index():
    conn = get_db()
    featured_products = conn.execute("""
        SELECT p.*, c.name as category_name 
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.is_featured = 1 AND p.stock > 0
        ORDER BY p.id DESC LIMIT 4
    """).fetchall()

    new_arrivals = conn.execute("""
        SELECT p.*, c.name as category_name 
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.stock > 0
        ORDER BY p.id DESC LIMIT 8
    """).fetchall()

    best_sellers = conn.execute("""
        SELECT p.*, c.name as category_name 
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.badge = 'Terlaris' OR p.reviews_count > 20
        ORDER BY p.rating DESC LIMIT 4
    """).fetchall()

    categories = conn.execute("SELECT * FROM categories").fetchall()
    conn.close()

    return render_template('index.html', 
                           featured=featured_products, 
                           new_arrivals=new_arrivals, 
                           best_sellers=best_sellers,
                           categories=categories)

@app.route('/shop')
def shop():
    category_slug = request.args.get('category', '')
    query = request.args.get('q', '').strip()
    sort = request.args.get('sort', 'newest')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    badge = request.args.get('badge', '')

    conn = get_db()
    sql = """
        SELECT p.*, c.name as category_name, c.slug as category_slug 
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE 1=1
    """
    params = []

    if category_slug:
        sql += " AND c.slug = ?"
        params.append(category_slug)
    
    if query:
        sql += " AND (p.name LIKE ? OR p.description LIKE ? OR p.sku LIKE ?)"
        wildcard = f"%{query}%"
        params.extend([wildcard, wildcard, wildcard])

    if min_price is not None:
        sql += " AND p.price >= ?"
        params.append(min_price)

    if max_price is not None:
        sql += " AND p.price <= ?"
        params.append(max_price)

    if badge:
        sql += " AND p.badge = ?"
        params.append(badge)

    if sort == 'price_asc':
        sql += " ORDER BY p.price ASC"
    elif sort == 'price_desc':
        sql += " ORDER BY p.price DESC"
    elif sort == 'rating':
        sql += " ORDER BY p.rating DESC"
    elif sort == 'popular':
        sql += " ORDER BY p.reviews_count DESC"
    else:
        sql += " ORDER BY p.id DESC"

    products = conn.execute(sql, params).fetchall()
    categories = conn.execute("SELECT * FROM categories ORDER BY name ASC").fetchall()
    conn.close()

    return render_template('shop.html', 
                           products=products, 
                           categories=categories,
                           current_category=category_slug,
                           search_query=query,
                           current_sort=sort,
                           min_price=min_price,
                           max_price=max_price)

@app.route('/product/<slug>')
def product_detail(slug):
    conn = get_db()
    product = conn.execute("""
        SELECT p.*, c.name as category_name, c.slug as category_slug 
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.slug = ?
    """, (slug,)).fetchone()

    if not product:
        conn.close()
        flash("Produk tidak ditemukan.", "warning")
        return redirect(url_for('shop'))

    # Related products
    related = conn.execute("""
        SELECT p.*, c.name as category_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.category_id = ? AND p.id != ?
        LIMIT 4
    """, (product['category_id'], product['id'])).fetchall()

    # Reviews
    reviews = conn.execute("""
        SELECT * FROM reviews 
        WHERE product_id = ? 
        ORDER BY id DESC
    """, (product['id'],)).fetchall()

    conn.close()
    return render_template('product_detail.html', product=product, related=related, reviews=reviews)

# ==========================================
# CART & VOUCHER API
# ==========================================

@app.route('/cart')
def cart_page():
    cart = session.get('cart', {})
    cart_items = []
    subtotal = 0

    conn = get_db()
    for key, item in cart.items():
        p = conn.execute("SELECT * FROM products WHERE id = ?", (item['product_id'],)).fetchone()
        if p:
            item_subtotal = p['price'] * item['quantity']
            subtotal += item_subtotal
            cart_items.append({
                'key': key,
                'product_id': p['id'],
                'name': p['name'],
                'slug': p['slug'],
                'price': p['price'],
                'original_price': p['original_price'],
                'image_url': p['image_url'],
                'stock': p['stock'],
                'variant': item.get('variant', ''),
                'quantity': item['quantity'],
                'subtotal': item_subtotal
            })
    conn.close()

    voucher = session.get('voucher')
    discount_amount = 0
    if voucher:
        if voucher['discount_type'] == 'percent':
            discount_amount = (subtotal * voucher['discount_value']) / 100
            if voucher['max_discount'] > 0 and discount_amount > voucher['max_discount']:
                discount_amount = voucher['max_discount']
        else:
            discount_amount = voucher['discount_value']
        
        if subtotal < voucher.get('min_spend', 0):
            discount_amount = 0
            session.pop('voucher', None)
            voucher = None

    total = max(0, subtotal - discount_amount)

    return render_template('cart.html', 
                           cart_items=cart_items, 
                           subtotal=subtotal, 
                           discount_amount=discount_amount, 
                           voucher=voucher, 
                           total=total)

@app.route('/api/cart/add', methods=['POST'])
def api_add_to_cart():
    data = request.get_json() or {}
    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 1))
    variant = data.get('variant', '').strip()

    if not product_id or quantity <= 0:
        return jsonify({'success': False, 'message': 'Data tidak valid'}), 400

    conn = get_db()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()

    if not product:
        return jsonify({'success': False, 'message': 'Produk tidak ditemukan'}), 404

    if product['stock'] < quantity:
        return jsonify({'success': False, 'message': f'Stok tidak mencukupi (Tersisa: {product["stock"]})'}), 400

    cart = session.get('cart', {})
    cart_key = f"{product_id}_{variant}"

    if cart_key in cart:
        new_qty = cart[cart_key]['quantity'] + quantity
        if new_qty > product['stock']:
            return jsonify({'success': False, 'message': f'Maksimum stok ({product["stock"]}) tercapai'}), 400
        cart[cart_key]['quantity'] = new_qty
    else:
        cart[cart_key] = {
            'product_id': product['id'],
            'variant': variant,
            'quantity': quantity
        }

    session['cart'] = cart
    session.modified = True

    total_count = sum(item['quantity'] for item in cart.values())
    return jsonify({
        'success': True, 
        'message': f'{product["name"]} berhasil ditambahkan ke tas belanja!',
        'cart_count': total_count
    })

@app.route('/api/cart/update', methods=['POST'])
def api_update_cart():
    data = request.get_json() or {}
    cart_key = data.get('key')
    quantity = int(data.get('quantity', 1))

    cart = session.get('cart', {})
    if cart_key not in cart:
        return jsonify({'success': False, 'message': 'Item tidak ada dalam keranjang'}), 404

    if quantity <= 0:
        del cart[cart_key]
    else:
        conn = get_db()
        p = conn.execute("SELECT stock FROM products WHERE id = ?", (cart[cart_key]['product_id'],)).fetchone()
        conn.close()
        if p and quantity > p['stock']:
            return jsonify({'success': False, 'message': f'Maksimal {p["stock"]} item tersedia'}), 400
        cart[cart_key]['quantity'] = quantity

    session['cart'] = cart
    session.modified = True

    return jsonify({'success': True, 'message': 'Keranjang diperbarui'})

@app.route('/api/cart/remove', methods=['POST'])
def api_remove_cart():
    data = request.get_json() or {}
    cart_key = data.get('key')

    cart = session.get('cart', {})
    if cart_key in cart:
        del cart[cart_key]
        session['cart'] = cart
        session.modified = True

    return jsonify({'success': True, 'message': 'Item dihapus'})

@app.route('/api/voucher/apply', methods=['POST'])
def api_apply_voucher():
    data = request.get_json() or {}
    code = data.get('code', '').strip().upper()

    if not code:
        return jsonify({'success': False, 'message': 'Masukkan kode voucher'}), 400

    conn = get_db()
    voucher = conn.execute("""
        SELECT * FROM vouchers 
        WHERE code = ? AND is_active = 1
    """, (code,)).fetchone()

    if not voucher:
        conn.close()
        return jsonify({'success': False, 'message': 'Kode voucher tidak valid atau telah kedaluwarsa'}), 404

    # Calculate current cart subtotal
    cart = session.get('cart', {})
    subtotal = 0
    for key, item in cart.items():
        p = conn.execute("SELECT price FROM products WHERE id = ?", (item['product_id'],)).fetchone()
        if p:
            subtotal += p['price'] * item['quantity']
    conn.close()

    if subtotal < voucher['min_spend']:
        min_rp = rupiah_filter(voucher['min_spend'])
        return jsonify({
            'success': False, 
            'message': f'Minimum belanja untuk voucher ini adalah {min_rp}'
        }), 400

    discount_amount = 0
    if voucher['discount_type'] == 'percent':
        discount_amount = (subtotal * voucher['discount_value']) / 100
        if voucher['max_discount'] > 0 and discount_amount > voucher['max_discount']:
            discount_amount = voucher['max_discount']
    else:
        discount_amount = voucher['discount_value']

    session['voucher'] = {
        'code': voucher['code'],
        'discount_type': voucher['discount_type'],
        'discount_value': voucher['discount_value'],
        'min_spend': voucher['min_spend'],
        'max_discount': voucher['max_discount'],
        'calculated_discount': discount_amount
    }
    session.modified = True

    return jsonify({
        'success': True, 
        'message': f'Voucher {voucher["code"]} berhasil digunakan! Hemat {rupiah_filter(discount_amount)}',
        'discount': discount_amount
    })

@app.route('/api/voucher/remove', methods=['POST'])
def api_remove_voucher():
    session.pop('voucher', None)
    session.modified = True
    return jsonify({'success': True, 'message': 'Voucher dilepas'})

# ==========================================
# CHECKOUT & ORDER MANAGEMENT
# ==========================================

@app.route('/checkout')
def checkout():
    cart = session.get('cart', {})
    if not cart:
        flash("Tas belanja Anda masih kosong.", "info")
        return redirect(url_for('shop'))

    conn = get_db()
    cart_items = []
    subtotal = 0
    for key, item in cart.items():
        p = conn.execute("SELECT * FROM products WHERE id = ?", (item['product_id'],)).fetchone()
        if p:
            item_subtotal = p['price'] * item['quantity']
            subtotal += item_subtotal
            cart_items.append({
                'product': p,
                'variant': item.get('variant', ''),
                'quantity': item['quantity'],
                'subtotal': item_subtotal
            })
    conn.close()

    voucher = session.get('voucher')
    discount_amount = 0
    if voucher:
        if voucher['discount_type'] == 'percent':
            discount_amount = (subtotal * voucher['discount_value']) / 100
            if voucher['max_discount'] > 0 and discount_amount > voucher['max_discount']:
                discount_amount = voucher['max_discount']
        else:
            discount_amount = voucher['discount_value']

    couriers = [
        {'id': 'jne_yes', 'name': 'JNE YES (Yakin Esok Sampai)', 'cost': 35000, 'etd': '1 Hari'},
        {'id': 'sicepat_best', 'name': 'SiCepat BEST Express', 'cost': 28000, 'etd': '1 - 2 Hari'},
        {'id': 'paxel_cold', 'name': 'Paxel Insured Vault Express', 'cost': 45000, 'etd': '1 Hari (Asuransi Penuh)'},
        {'id': 'gosend_instant', 'name': 'GoSend Instant Courier (Jabodetabek)', 'cost': 50000, 'etd': '3 - 5 Jam'}
    ]

    return render_template('checkout.html', 
                           cart_items=cart_items, 
                           subtotal=subtotal, 
                           discount_amount=discount_amount, 
                           voucher=voucher, 
                           couriers=couriers)

@app.route('/api/checkout', methods=['POST'])
def process_checkout():
    cart = session.get('cart', {})
    if not cart:
        return jsonify({'success': False, 'message': 'Keranjang kosong'}), 400

    data = request.get_json() or {}
    name = data.get('customer_name', '').strip()
    email = data.get('customer_email', '').strip()
    phone = data.get('customer_phone', '').strip()
    address = data.get('shipping_address', '').strip()
    city = data.get('shipping_city', '').strip()
    postal = data.get('shipping_postal_code', '').strip()
    courier_name = data.get('shipping_courier', 'JNE YES')
    courier_cost = float(data.get('shipping_cost', 35000))
    payment_method = data.get('payment_method', 'QRIS')
    notes = data.get('notes', '').strip()

    if not (name and email and phone and address and city):
        return jsonify({'success': False, 'message': 'Harap lengkapi semua data formulir pengiriman'}), 400

    conn = get_db()
    cursor = conn.cursor()

    # Re-calculate subtotal and verify stock
    subtotal = 0
    items_to_save = []

    for key, item in cart.items():
        p = cursor.execute("SELECT * FROM products WHERE id = ?", (item['product_id'],)).fetchone()
        if not p or p['stock'] < item['quantity']:
            conn.close()
            return jsonify({'success': False, 'message': f'Stok produk {p["name"] if p else ""} tidak mencukupi'}), 400
        
        item_sub = p['price'] * item['quantity']
        subtotal += item_sub
        items_to_save.append({
            'product_id': p['id'],
            'product_name': p['name'],
            'product_price': p['price'],
            'quantity': item['quantity'],
            'subtotal': item_sub,
            'variant': item.get('variant', ''),
            'image_url': p['image_url']
        })

    # Discount calculation
    voucher = session.get('voucher')
    discount_amount = 0
    voucher_code = None
    if voucher:
        voucher_code = voucher['code']
        if voucher['discount_type'] == 'percent':
            discount_amount = (subtotal * voucher['discount_value']) / 100
            if voucher['max_discount'] > 0 and discount_amount > voucher['max_discount']:
                discount_amount = voucher['max_discount']
        else:
            discount_amount = voucher['discount_value']
        
        # Increment voucher used count
        cursor.execute("UPDATE vouchers SET used_count = used_count + 1 WHERE code = ?", (voucher_code,))

    total = max(0, subtotal - discount_amount) + courier_cost

    # Generate Order Number: ORD-YYYYMMDD-XXXX
    date_str = datetime.datetime.now().strftime("%Y%m%d")
    random_suffix = random.randint(1000, 9999)
    order_number = f"ORD-{date_str}-{random_suffix}"

    user_id = session.get('user_id')

    # Initial payment status
    # In luxury e-commerce demo, QRIS or VA can simulate instant pay or pending
    payment_status = 'unpaid'
    order_status = 'pending'

    cursor.execute("""
        INSERT INTO orders 
        (order_number, user_id, customer_name, customer_email, customer_phone, 
         shipping_address, shipping_city, shipping_postal_code, shipping_courier, 
         shipping_cost, tracking_number, subtotal, discount_amount, voucher_code, 
         total, payment_method, payment_status, order_status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        order_number, user_id, name, email, phone, 
        address, city, postal, courier_name, 
        courier_cost, None, subtotal, discount_amount, voucher_code, 
        total, payment_method, payment_status, order_status, notes
    ))
    order_id = cursor.lastrowid

    # Insert items & reduce stock
    for it in items_to_save:
        cursor.execute("""
            INSERT INTO order_items 
            (order_id, product_id, product_name, product_price, quantity, subtotal, selected_variant, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (order_id, it['product_id'], it['product_name'], it['product_price'], it['quantity'], it['subtotal'], it['variant'], it['image_url']))

        cursor.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (it['quantity'], it['product_id']))

    conn.commit()
    conn.close()

    # Clear cart and voucher
    session.pop('cart', None)
    session.pop('voucher', None)
    session.modified = True

    return jsonify({
        'success': True,
        'order_number': order_number,
        'redirect_url': url_for('order_success', order_number=order_number)
    })

@app.route('/order-success/<order_number>')
def order_success(order_number):
    conn = get_db()
    order = conn.execute("SELECT * FROM orders WHERE order_number = ?", (order_number,)).fetchone()
    if not order:
        conn.close()
        flash("Pesanan tidak ditemukan.", "warning")
        return redirect(url_for('index'))

    items = conn.execute("SELECT * FROM order_items WHERE order_id = ?", (order['id'],)).fetchall()
    conn.close()

    # VA Account number generation simulation
    va_numbers = {
        'BCA_VA': '8277' + str(order['id']).zfill(8) + '99',
        'MANDIRI_VA': '8950' + str(order['id']).zfill(8) + '77',
        'BNI_VA': '9881' + str(order['id']).zfill(8) + '11',
        'BRI_VA': '1044' + str(order['id']).zfill(8) + '55'
    }
    simulated_va = va_numbers.get(order['payment_method'], '8888' + str(order['id']).zfill(8))

    return render_template('order_success.html', order=order, items=items, simulated_va=simulated_va)

@app.route('/api/order/simulate-pay/<order_number>', methods=['POST'])
def simulate_payment(order_number):
    conn = get_db()
    cursor = conn.cursor()
    order = cursor.execute("SELECT * FROM orders WHERE order_number = ?", (order_number,)).fetchone()
    if not order:
        conn.close()
        return jsonify({'success': False, 'message': 'Pesanan tidak ditemukan'}), 404

    cursor.execute("""
        UPDATE orders 
        SET payment_status = 'paid', order_status = 'processing', updated_at = CURRENT_TIMESTAMP
        WHERE order_number = ?
    """, (order_number,))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Pembayaran berhasil dikonfirmasi! Pesanan segera disiapkan.'})

# ==========================================
# ORDER TRACKER TOOL (Pelacak Pesanan)
# ==========================================

@app.route('/track-order', methods=['GET', 'POST'])
def track_order():
    order_query = request.args.get('order_number') or request.form.get('order_number') or ''
    order = None
    items = []

    if order_query:
        order_query = order_query.strip().upper()
        conn = get_db()
        order = conn.execute("""
            SELECT * FROM orders 
            WHERE UPPER(order_number) = ? OR UPPER(tracking_number) = ?
        """, (order_query, order_query)).fetchone()

        if order:
            items = conn.execute("SELECT * FROM order_items WHERE order_id = ?", (order['id'],)).fetchall()
        else:
            flash(f"Nomor pesanan atau resi '{order_query}' tidak ditemukan dalam sistem.", "warning")
        conn.close()

    return render_template('track_order.html', order=order, items=items, search_query=order_query)

# ==========================================
# INVOICE GENERATOR TOOL
# ==========================================

@app.route('/invoice/<order_number>')
def view_invoice(order_number):
    conn = get_db()
    order = conn.execute("SELECT * FROM orders WHERE order_number = ?", (order_number,)).fetchone()
    if not order:
        conn.close()
        flash("Pesanan tidak ditemukan.", "danger")
        return redirect(url_for('index'))

    items = conn.execute("SELECT * FROM order_items WHERE order_id = ?", (order['id'],)).fetchall()
    settings = {row['key']: row['value'] for row in conn.execute("SELECT key, value FROM settings").fetchall()}
    conn.close()

    return render_template('invoice.html', order=order, items=items, settings=settings)

# ==========================================
# REVIEWS & WISHLIST
# ==========================================

@app.route('/api/review/add', methods=['POST'])
def add_review():
    data = request.get_json() or {}
    product_id = data.get('product_id')
    name = data.get('name', '').strip()
    rating = int(data.get('rating', 5))
    comment = data.get('comment', '').strip()

    if not product_id or not name or not comment:
        return jsonify({'success': False, 'message': 'Harap isi ulasan dan nama Anda.'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO reviews (product_id, customer_name, rating, comment)
        VALUES (?, ?, ?, ?)
    """, (product_id, name, rating, comment))

    # Recalculate product rating
    stats = cursor.execute("""
        SELECT AVG(rating) as avg_rating, COUNT(*) as cnt 
        FROM reviews WHERE product_id = ?
    """, (product_id,)).fetchone()

    avg_rate = round(stats['avg_rating'], 1) if stats['avg_rating'] else 5.0
    cnt = stats['cnt']

    cursor.execute("""
        UPDATE products 
        SET rating = ?, reviews_count = ?
        WHERE id = ?
    """, (avg_rate, cnt, product_id))

    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Terima kasih atas ulasan berharga Anda!'})

@app.route('/wishlist')
def wishlist():
    return render_template('wishlist.html')

# ==========================================
# AUTHENTICATION
# ==========================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_role'] = user['role']
            session['user_name'] = user['name']
            flash(f"Selamat datang kembali, {user['name']}!", "success")
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('index'))
        else:
            flash("Email atau kata sandi tidak cocok.", "danger")

    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not (name and email and password):
            flash("Semua bidang wajib diisi.", "warning")
            return render_template('auth/register.html')

        if password != confirm_password:
            flash("Konfirmasi kata sandi tidak cocok.", "warning")
            return render_template('auth/register.html')

        conn = get_db()
        cursor = conn.cursor()
        existing = cursor.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            conn.close()
            flash("Email ini sudah terdaftar. Silakan masuk.", "warning")
            return redirect(url_for('login'))

        pwd_hash = generate_password_hash(password)
        cursor.execute("""
            INSERT INTO users (name, email, password_hash, role, phone)
            VALUES (?, ?, ?, 'customer', ?)
        """, (name, email, pwd_hash, phone))
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()

        session['user_id'] = new_id
        session['user_role'] = 'customer'
        session['user_name'] = name
        flash("Pendaftaran akun berhasil! Selamat berbelanja.", "success")
        return redirect(url_for('index'))

    return render_template('auth/register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Anda telah keluar dari akun.", "info")
    return redirect(url_for('index'))

# ==========================================
# ADMIN TOOLS & DASHBOARD SUITE
# ==========================================

@app.route('/admin')
@admin_required
def admin_dashboard():
    conn = get_db()

    # Metrics
    total_revenue = conn.execute("SELECT SUM(total) as rev FROM orders WHERE payment_status = 'paid'").fetchone()['rev'] or 0
    total_orders = conn.execute("SELECT COUNT(*) as cnt FROM orders").fetchone()['cnt']
    pending_orders = conn.execute("SELECT COUNT(*) as cnt FROM orders WHERE order_status = 'pending'").fetchone()['cnt']
    total_products = conn.execute("SELECT COUNT(*) as cnt FROM products").fetchone()['cnt']
    low_stock_count = conn.execute("SELECT COUNT(*) as cnt FROM products WHERE stock <= 5").fetchone()['cnt']

    # Low stock items
    low_stock_items = conn.execute("SELECT * FROM products WHERE stock <= 5 ORDER BY stock ASC LIMIT 5").fetchall()

    # Recent orders
    recent_orders = conn.execute("""
        SELECT * FROM orders 
        ORDER BY id DESC LIMIT 6
    """).fetchall()

    # Category breakdown for Chart.js
    category_stats = conn.execute("""
        SELECT c.name, COUNT(p.id) as product_count
        FROM categories c
        LEFT JOIN products p ON c.id = p.category_id
        GROUP BY c.id
    """).fetchall()

    cat_labels = [row['name'] for row in category_stats]
    cat_data = [row['product_count'] for row in category_stats]

    # Daily revenue simulation/data
    sales_trend = conn.execute("""
        SELECT DATE(created_at) as sale_date, SUM(total) as day_total, COUNT(*) as order_count
        FROM orders
        GROUP BY DATE(created_at)
        ORDER BY sale_date ASC
        LIMIT 7
    """).fetchall()

    trend_labels = [row['sale_date'] for row in sales_trend]
    trend_totals = [row['day_total'] for row in sales_trend]

    conn.close()

    return render_template('admin/dashboard.html',
                           total_revenue=total_revenue,
                           total_orders=total_orders,
                           pending_orders=pending_orders,
                           total_products=total_products,
                           low_stock_count=low_stock_count,
                           low_stock_items=low_stock_items,
                           recent_orders=recent_orders,
                           cat_labels=json.dumps(cat_labels),
                           cat_data=json.dumps(cat_data),
                           trend_labels=json.dumps(trend_labels),
                           trend_totals=json.dumps(trend_totals))

@app.route('/admin/products')
@admin_required
def admin_products():
    search = request.args.get('search', '').strip()
    category_id = request.args.get('category_id', '')

    conn = get_db()
    sql = """
        SELECT p.*, c.name as category_name 
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE 1=1
    """
    params = []
    if search:
        sql += " AND (p.name LIKE ? OR p.sku LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    if category_id:
        sql += " AND p.category_id = ?"
        params.append(category_id)

    sql += " ORDER BY p.id DESC"
    products = conn.execute(sql, params).fetchall()
    categories = conn.execute("SELECT * FROM categories ORDER BY name ASC").fetchall()
    conn.close()

    return render_template('admin/products.html', products=products, categories=categories, search=search, selected_cat=category_id)

@app.route('/admin/products/add', methods=['POST'])
@admin_required
def admin_add_product():
    name = request.form.get('name', '').strip()
    category_id = request.form.get('category_id')
    price = float(request.form.get('price', 0))
    original_price = float(request.form.get('original_price', 0)) or None
    stock = int(request.form.get('stock', 0))
    sku = request.form.get('sku', '').strip()
    image_url = request.form.get('image_url', '').strip()
    description = request.form.get('description', '').strip()
    badge = request.form.get('badge', '').strip() or None
    is_featured = 1 if request.form.get('is_featured') else 0

    # Auto slug from name
    slug = name.lower().replace(' ', '-').replace('&', 'and').replace('/', '-') + f"-{random.randint(100, 999)}"

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO products 
        (name, slug, category_id, price, original_price, stock, sku, image_url, description, badge, is_featured)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, slug, category_id, price, original_price, stock, sku, image_url, description, badge, is_featured))
    conn.commit()
    conn.close()

    flash("Produk baru berhasil ditambahkan!", "success")
    return redirect(url_for('admin_products'))

@app.route('/admin/products/edit/<int:product_id>', methods=['POST'])
@admin_required
def admin_edit_product(product_id):
    name = request.form.get('name', '').strip()
    category_id = request.form.get('category_id')
    price = float(request.form.get('price', 0))
    original_price = float(request.form.get('original_price', 0)) or None
    stock = int(request.form.get('stock', 0))
    sku = request.form.get('sku', '').strip()
    image_url = request.form.get('image_url', '').strip()
    description = request.form.get('description', '').strip()
    badge = request.form.get('badge', '').strip() or None
    is_featured = 1 if request.form.get('is_featured') else 0

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE products 
        SET name = ?, category_id = ?, price = ?, original_price = ?, stock = ?, 
            sku = ?, image_url = ?, description = ?, badge = ?, is_featured = ?
        WHERE id = ?
    """, (name, category_id, price, original_price, stock, sku, image_url, description, badge, is_featured, product_id))
    conn.commit()
    conn.close()

    flash("Perubahan produk berhasil disimpan!", "success")
    return redirect(url_for('admin_products'))

@app.route('/admin/products/delete/<int:product_id>', methods=['POST'])
@admin_required
def admin_delete_product(product_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()

    flash("Produk berhasil dihapus dari katalog.", "info")
    return redirect(url_for('admin_products'))

@app.route('/admin/products/quick-stock/<int:product_id>', methods=['POST'])
@admin_required
def admin_quick_stock(product_id):
    add_qty = int(request.form.get('quantity', 10))
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET stock = stock + ? WHERE id = ?", (add_qty, product_id))
    conn.commit()
    conn.close()

    flash(f"Berhasil menambahkan {add_qty} unit stok!", "success")
    return redirect(url_for('admin_products'))

# ==========================================
# ADMIN ORDERS MANAGEMENT TOOL
# ==========================================

@app.route('/admin/orders')
@admin_required
def admin_orders():
    status = request.args.get('status', '')
    search = request.args.get('search', '').strip()

    conn = get_db()
    sql = "SELECT * FROM orders WHERE 1=1"
    params = []

    if status:
        sql += " AND order_status = ?"
        params.append(status)

    if search:
        sql += " AND (order_number LIKE ? OR customer_name LIKE ? OR customer_phone LIKE ? OR tracking_number LIKE ?)"
        wildcard = f"%{search}%"
        params.extend([wildcard, wildcard, wildcard, wildcard])

    sql += " ORDER BY id DESC"
    orders = conn.execute(sql, params).fetchall()
    conn.close()

    return render_template('admin/orders.html', orders=orders, current_status=status, search=search)

@app.route('/admin/orders/<int:order_id>')
@admin_required
def admin_order_detail(order_id):
    conn = get_db()
    order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if not order:
        conn.close()
        flash("Pesanan tidak ditemukan.", "danger")
        return redirect(url_for('admin_orders'))

    items = conn.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,)).fetchall()
    conn.close()

    return render_template('admin/order_detail.html', order=order, items=items)

@app.route('/admin/orders/<int:order_id>/update-status', methods=['POST'])
@admin_required
def admin_update_order_status(order_id):
    order_status = request.form.get('order_status')
    payment_status = request.form.get('payment_status')
    tracking_number = request.form.get('tracking_number', '').strip()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE orders 
        SET order_status = ?, payment_status = ?, tracking_number = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (order_status, payment_status, tracking_number or None, order_id))
    conn.commit()
    conn.close()

    flash(f"Status pesanan berhasil diperbarui!", "success")
    return redirect(url_for('admin_order_detail', order_id=order_id))

# ==========================================
# ADMIN PROMO & VOUCHER TOOL
# ==========================================

@app.route('/admin/vouchers')
@admin_required
def admin_vouchers():
    conn = get_db()
    vouchers = conn.execute("SELECT * FROM vouchers ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('admin/vouchers.html', vouchers=vouchers)

@app.route('/admin/vouchers/add', methods=['POST'])
@admin_required
def admin_add_voucher():
    code = request.form.get('code', '').strip().upper()
    discount_type = request.form.get('discount_type', 'percent')
    discount_value = float(request.form.get('discount_value', 0))
    min_spend = float(request.form.get('min_spend', 0))
    max_discount = float(request.form.get('max_discount', 0))
    usage_limit = int(request.form.get('usage_limit', 100))
    expires_at = request.form.get('expires_at') or "2027-12-31"

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO vouchers 
            (code, discount_type, discount_value, min_spend, max_discount, usage_limit, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (code, discount_type, discount_value, min_spend, max_discount, usage_limit, expires_at))
        conn.commit()
        flash(f"Voucher promosi {code} berhasil dibuat!", "success")
    except Exception as e:
        flash(f"Gagal membuat voucher (mungkin kode sudah digunakan): {e}", "danger")
    finally:
        conn.close()

    return redirect(url_for('admin_vouchers'))

@app.route('/admin/vouchers/toggle/<int:voucher_id>', methods=['POST'])
@admin_required
def admin_toggle_voucher(voucher_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE vouchers SET is_active = CASE WHEN is_active=1 THEN 0 ELSE 1 END WHERE id = ?", (voucher_id,))
    conn.commit()
    conn.close()
    flash("Status keaktifan voucher berhasil diubah.", "info")
    return redirect(url_for('admin_vouchers'))

@app.route('/admin/vouchers/delete/<int:voucher_id>', methods=['POST'])
@admin_required
def admin_delete_voucher(voucher_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM vouchers WHERE id = ?", (voucher_id,))
    conn.commit()
    conn.close()
    flash("Voucher berhasil dihapus.", "info")
    return redirect(url_for('admin_vouchers'))

# ==========================================
# ADMIN POS (POINT OF SALE) CASHIER TOOL
# ==========================================

@app.route('/admin/pos')
@admin_required
def admin_pos():
    conn = get_db()
    products = conn.execute("""
        SELECT p.*, c.name as category_name 
        FROM products p 
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.stock > 0
        ORDER BY p.name ASC
    """).fetchall()
    categories = conn.execute("SELECT * FROM categories ORDER BY name ASC").fetchall()
    conn.close()
    return render_template('admin/pos.html', products=products, categories=categories)

@app.route('/api/pos/checkout', methods=['POST'])
@admin_required
def admin_pos_checkout():
    data = request.get_json() or {}
    items = data.get('items', [])
    customer_name = data.get('customer_name', 'Tamu Walk-in').strip() or 'Tamu Walk-in'
    payment_method = data.get('payment_method', 'TUNAI (CASH)')
    cash_given = float(data.get('cash_given', 0))
    discount_amount = float(data.get('discount_amount', 0))

    if not items:
        return jsonify({'success': False, 'message': 'Keranjang POS kosong'}), 400

    conn = get_db()
    cursor = conn.cursor()

    subtotal = 0
    order_items_data = []

    for item in items:
        p = cursor.execute("SELECT * FROM products WHERE id = ?", (item['product_id'],)).fetchone()
        if not p or p['stock'] < item['quantity']:
            conn.close()
            return jsonify({'success': False, 'message': f'Stok {p["name"] if p else ""} tidak mencukupi!'}), 400
        
        item_sub = p['price'] * item['quantity']
        subtotal += item_sub
        order_items_data.append({
            'product_id': p['id'],
            'product_name': p['name'],
            'price': p['price'],
            'quantity': item['quantity'],
            'subtotal': item_sub,
            'image_url': p['image_url']
        })

    total = max(0, subtotal - discount_amount)
    change = max(0, cash_given - total) if payment_method == 'TUNAI (CASH)' else 0

    date_str = datetime.datetime.now().strftime("%Y%m%d")
    order_number = f"POS-{date_str}-{random.randint(1000, 9999)}"

    # Create POS Order
    cursor.execute("""
        INSERT INTO orders 
        (order_number, user_id, customer_name, customer_email, customer_phone, 
         shipping_address, shipping_city, shipping_postal_code, shipping_courier, 
         shipping_cost, tracking_number, subtotal, discount_amount, total, 
         payment_method, payment_status, order_status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        order_number, session.get('user_id'), customer_name, 'pos-counter@ranzzstore.com', '-', 
        'Transaksi Kasir Langsung (Boutique SCBD)', 'Jakarta', '12190', 'In-Store Pickup', 
        0, 'POS-DIRECT', subtotal, discount_amount, total, 
        payment_method, 'paid', 'completed', 'Transaksi Kasir POS Kasir'
    ))
    order_id = cursor.lastrowid

    # Items & Stock
    for it in order_items_data:
        cursor.execute("""
            INSERT INTO order_items 
            (order_id, product_id, product_name, product_price, quantity, subtotal, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (order_id, it['product_id'], it['product_name'], it['price'], it['quantity'], it['subtotal'], it['image_url']))

        cursor.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (it['quantity'], it['product_id']))

    conn.commit()
    conn.close()

    return jsonify({
        'success': True,
        'order_number': order_number,
        'subtotal': subtotal,
        'discount': discount_amount,
        'total': total,
        'cash_given': cash_given,
        'change': change,
        'message': 'Transaksi Kasir Berhasil!'
    })

# ==========================================
# ADMIN EXPORT TOOLS
# ==========================================

@app.route('/admin/export/orders.csv')
@admin_required
def admin_export_orders():
    conn = get_db()
    orders = conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'Nomor Pesanan', 'Tanggal', 'Pelanggan', 'Email', 'Telepon', 
        'Kota', 'Kurir', 'Resi', 'Subtotal (IDR)', 'Diskon (IDR)', 
        'Total (IDR)', 'Metode Pembayaran', 'Status Pembayaran', 'Status Pesanan'
    ])

    for o in orders:
        writer.writerow([
            o['order_number'], o['created_at'], o['customer_name'], o['customer_email'], o['customer_phone'],
            o['shipping_city'], o['shipping_courier'], o['tracking_number'] or '-',
            int(o['subtotal']), int(o['discount_amount']), int(o['total']),
            o['payment_method'], o['payment_status'], o['order_status']
        ])

    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=laporan_penjualan_ranzzstore.csv"
    response.headers["Content-type"] = "text/csv; charset=utf-8"
    return response

@app.route('/admin/export/products.csv')
@admin_required
def admin_export_products():
    conn = get_db()
    products = conn.execute("""
        SELECT p.*, c.name as category_name 
        FROM products p 
        LEFT JOIN categories c ON p.category_id = c.id
        ORDER BY p.id DESC
    """).fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['SKU', 'Nama Produk', 'Kategori', 'Harga (IDR)', 'Harga Asli (IDR)', 'Stok', 'Badge', 'Rating', 'Terjual/Ulasan'])

    for p in products:
        writer.writerow([
            p['sku'], p['name'], p['category_name'] or 'Umum',
            int(p['price']), int(p['original_price'] or 0), p['stock'],
            p['badge'] or '-', p['rating'], p['reviews_count']
        ])

    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=daftar_produk_katalog.csv"
    response.headers["Content-type"] = "text/csv; charset=utf-8"
    return response

# ==========================================
# ADMIN SETTINGS TOOL
# ==========================================

@app.route('/admin/settings', methods=['GET', 'POST'])
@admin_required
def admin_settings():
    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        for key in ['store_name', 'store_tagline', 'store_phone', 'store_email', 'store_address', 'tax_rate']:
            val = request.form.get(key, '')
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, val))
        conn.commit()
        flash("Pengaturan toko berhasil diperbarui!", "success")

    settings = {row['key']: row['value'] for row in cursor.execute("SELECT key, value FROM settings").fetchall()}
    conn.close()
    return render_template('admin/settings.html', settings=settings)

if __name__ == '__main__':
    init_db()
    print(">> Ranzzstore Luxury E-Commerce Engine Starting on http://127.0.0.1:5000 <<")
    app.run(host='0.0.0.0', port=5000, debug=True)
