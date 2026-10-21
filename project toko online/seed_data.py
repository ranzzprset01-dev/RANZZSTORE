import json
from werkzeug.security import generate_password_hash
from models import get_db, init_db

def seed():
    init_db()
    conn = get_db()
    cursor = conn.cursor()

    # Clear existing data
    cursor.execute("DELETE FROM reviews")
    cursor.execute("DELETE FROM order_items")
    cursor.execute("DELETE FROM orders")
    cursor.execute("DELETE FROM vouchers")
    cursor.execute("DELETE FROM products")
    cursor.execute("DELETE FROM categories")
    cursor.execute("DELETE FROM users")
    cursor.execute("DELETE FROM settings")

    # 1. Users
    admin_hash = generate_password_hash("admin123")
    user_hash = generate_password_hash("user123")

    cursor.execute("""
    INSERT INTO users (name, email, password_hash, role, phone, address)
    VALUES 
    ('Admin Ranzzstore', 'admin@ranzzstore.com', ?, 'admin', '08119876543', 'Penthouse A-12, SCBD Jakarta'),
    ('Budi Pratama', 'customer@gmail.com', ?, 'customer', '08123456789', 'Jl. Wijaya Timur No. 45, Kebayoran Baru, Jakarta Selatan')
    """, (admin_hash, user_hash))

    # 2. Categories
    categories = [
        ("Jam Tangan Mewah", "timepieces", "watch", "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?q=80&w=800&auto=format&fit=crop"),
        ("Tas & Kerajinan Kulit", "leather-goods", "briefcase", "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?q=80&w=800&auto=format&fit=crop"),
        ("Parfum & Fragrance", "haute-fragrance", "sparkles", "https://images.unsplash.com/photo-1592945403244-b3fbafd7f539?q=80&w=800&auto=format&fit=crop"),
        ("Audio & Gadget Klasik", "acoustic-gadgets", "headphones", "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?q=80&w=800&auto=format&fit=crop"),
        ("Kacamata & Aksesoris", "eyewear-accessories", "glasses", "https://images.unsplash.com/photo-1511499767150-a48a237f0083?q=80&w=800&auto=format&fit=crop")
    ]

    for name, slug, icon, img in categories:
        cursor.execute("INSERT INTO categories (name, slug, icon, image_url) VALUES (?, ?, ?, ?)", (name, slug, icon, img))

    cat_map = {row['slug']: row['id'] for row in cursor.execute("SELECT id, slug FROM categories").fetchall()}

    # 3. Products
    products = [
        (
            cat_map["timepieces"],
            "Chronograph Aurelia Royal Noir 41mm",
            "aurelia-royal-noir-41mm",
            "Dibuat dengan presisi tinggi Swiss Automatic Movement kaliber 8200. Dilengkapi kristal safir anti-gores ganda dengan lapisan anti-reflektif dan dial matte hitam bergradasi rose gold. Tahan air hingga kedalaman 100 meter.",
            14500000,
            18500000,
            12,
            "AUR-WATCH-001",
            "https://images.unsplash.com/photo-1524592094714-0f0654e20314?q=80&w=800&auto=format&fit=crop",
            json.dumps([
                "https://images.unsplash.com/photo-1524592094714-0f0654e20314?q=80&w=800&auto=format&fit=crop",
                "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?q=80&w=800&auto=format&fit=crop",
                "https://images.unsplash.com/photo-1533139502658-0198f920d8e8?q=80&w=800&auto=format&fit=crop"
            ]),
            json.dumps(["Rose Gold / Black", "Silver / Navy", "All Matte Black"]),
            4.9,
            42,
            "Terlaris",
            1
        ),
        (
            cat_map["timepieces"],
            "Skeleton Automatic Tourbillon Heritage",
            "skeleton-automatic-tourbillon",
            "Karya seni horologi tingkat tinggi dengan mekanisme roda gigi terbuka transparan, cadangan daya 72 jam, dan case titanium aerospace grade 5 dengan strap kulit buaya asli Italia.",
            28900000,
            34000000,
            5,
            "AUR-WATCH-002",
            "https://images.unsplash.com/photo-1509042239860-f550ce710b93?q=80&w=800&auto=format&fit=crop",
            json.dumps([
                "https://images.unsplash.com/photo-1509042239860-f550ce710b93?q=80&w=800&auto=format&fit=crop"
            ]),
            json.dumps(["Obsidian Black", "Pure Platinum"]),
            5.0,
            18,
            "Edisi Terbatas",
            1
        ),
        (
            cat_map["leather-goods"],
            "The Monolith Leather Briefcase Cognac",
            "monolith-leather-briefcase-cognac",
            "Tas kerja eksekutif dari kulit full-grain vegetable tanned asal Florence. Memiliki kompartemen empuk untuk laptop 16 inci, interior beludru lembut, dan sistem kunci kuningan berlapis emas 24k antik.",
            5750000,
            6800000,
            8,
            "AUR-BAG-001",
            "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?q=80&w=800&auto=format&fit=crop",
            json.dumps([
                "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?q=80&w=800&auto=format&fit=crop",
                "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?q=80&w=800&auto=format&fit=crop"
            ]),
            json.dumps(["Cognac Brown", "Midnight Charcoal", "Olive Saddle"]),
            4.8,
            29,
            "Pilihan Editor",
            1
        ),
        (
            cat_map["leather-goods"],
            "Slimfold Bifold Wallet Signature Leather",
            "slimfold-bifold-wallet-signature",
            "Dompet minimalis ramping dengan perlindungan RFID blocking terintegrasi. Menampung hingga 10 kartu dan uang tunai tanpa membuatnya tampak tebal. Jahitan tangan artisanal yang kokoh.",
            1250000,
            1600000,
            24,
            "AUR-WAL-001",
            "https://images.unsplash.com/photo-1627123424574-724758594e93?q=80&w=800&auto=format&fit=crop",
            json.dumps([
                "https://images.unsplash.com/photo-1627123424574-724758594e93?q=80&w=800&auto=format&fit=crop"
            ]),
            json.dumps(["Espresso Brown", "Caviar Black"]),
            4.9,
            56,
            "Terlaris",
            0
        ),
        (
            cat_map["haute-fragrance"],
            "L'Extrait de Santal & Bergamot 100ml",
            "lextrait-de-santal-bergamot",
            "Kombinasi harmonis antara kehangatan kayu cendana Mysore, kesegaran bergamot Calabria, dan rempah kapulaga eksotis. Konsentrasi Extrait de Parfum 30% dengan daya tahan aroma lebih dari 16 jam.",
            3200000,
            3900000,
            15,
            "AUR-PERF-001",
            "https://images.unsplash.com/photo-1592945403244-b3fbafd7f539?q=80&w=800&auto=format&fit=crop",
            json.dumps([
                "https://images.unsplash.com/photo-1592945403244-b3fbafd7f539?q=80&w=800&auto=format&fit=crop",
                "https://images.unsplash.com/photo-1547887537-6158d64c35b3?q=80&w=800&auto=format&fit=crop"
            ]),
            json.dumps(["50ml Extrait", "100ml Extrait"]),
            5.0,
            64,
            "Signature",
            1
        ),
        (
            cat_map["haute-fragrance"],
            "Oud Impérial & Rose Damascena 100ml",
            "oud-imperial-rose-damascena",
            "Aroma kaya bernuansa bangsawan timur tengah. Diformulasikan dari ekstrak kayu gaharu murni berumur 20 tahun yang berpadu dengan keanggunan mawar Damaskus segar dan sentuhan ambergris.",
            4100000,
            4900000,
            9,
            "AUR-PERF-002",
            "https://images.unsplash.com/photo-1547887537-6158d64c35b3?q=80&w=800&auto=format&fit=crop",
            json.dumps([
                "https://images.unsplash.com/photo-1547887537-6158d64c35b3?q=80&w=800&auto=format&fit=crop"
            ]),
            json.dumps(["100ml Luxury Flacon"]),
            4.9,
            31,
            "Eksklusif",
            0
        ),
        (
            cat_map["acoustic-gadgets"],
            "Studio ANC Master Hi-Fi Headphones",
            "studio-anc-master-hifi",
            "Headphone nirkabel kelas audiophile dengan driver Beryllium 45mm custom, body aluminium aeronautika berbalut kulit domba lembut, serta peredam bising aktif (ANC) adaptif generasi terbaru.",
            7450000,
            8900000,
            7,
            "AUR-AUD-001",
            "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?q=80&w=800&auto=format&fit=crop",
            json.dumps([
                "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?q=80&w=800&auto=format&fit=crop",
                "https://images.unsplash.com/photo-1484704849700-f032a568e944?q=80&w=800&auto=format&fit=crop"
            ]),
            json.dumps(["Gunmetal Silver", "Champagne Gold", "Stealth Onyx"]),
            4.8,
            38,
            "Inovasi",
            1
        ),
        (
            cat_map["acoustic-gadgets"],
            "Acoustic Craft Walnut Bluetooth Speaker",
            "acoustic-craft-walnut-speaker",
            "Speaker meja berdaya 120W dengan kabinet kayu kenari solid Amerika yang dirancang secara akustik untuk dentuman bass yang hangat dan vokal kristal jernih. Dilengkapi amplifier tabung hybrid.",
            6200000,
            7500000,
            11,
            "AUR-AUD-002",
            "https://images.unsplash.com/photo-1545454675-3531b543be5d?q=80&w=800&auto=format&fit=crop",
            json.dumps([
                "https://images.unsplash.com/photo-1545454675-3531b543be5d?q=80&w=800&auto=format&fit=crop"
            ]),
            json.dumps(["Natural Walnut", "Dark Ebony"]),
            4.9,
            27,
            "Baru",
            0
        ),
        (
            cat_map["eyewear-accessories"],
            "Avanguardia Titanium Polarized Sunglasses",
            "avanguardia-titanium-sunglasses",
            "Kacamata hitam berdesain geometris dengan bingkai titanium ultra-ringan hanya 14 gram buatan Jepang. Lensa nylon polarisasi grade militer yang menyaring 100% radiasi UV dan silau cahaya.",
            3450000,
            4200000,
            14,
            "AUR-SUN-001",
            "https://images.unsplash.com/photo-1511499767150-a48a237f0083?q=80&w=800&auto=format&fit=crop",
            json.dumps([
                "https://images.unsplash.com/photo-1511499767150-a48a237f0083?q=80&w=800&auto=format&fit=crop"
            ]),
            json.dumps(["24k Gold Frame / Green Lens", "Gunmetal / Smoke Black"]),
            4.8,
            19,
            "Pilihan Editor",
            1
        ),
        (
            cat_map["eyewear-accessories"],
            "Royal Cufflinks Platinum & Blue Sapphire",
            "royal-cufflinks-platinum-sapphire",
            "Manset kemeja resmi berlapis platinum 950 dengan hiasan batu safir biru royal sintetis berpotongan cushion brilliant. Menghadirkan wibawa dan karisma pada setiap setelan jas Anda.",
            2400000,
            2950000,
            20,
            "AUR-ACC-001",
            "https://images.unsplash.com/photo-1617038260897-41a1f14a8ca0?q=80&w=800&auto=format&fit=crop",
            json.dumps([
                "https://images.unsplash.com/photo-1617038260897-41a1f14a8ca0?q=80&w=800&auto=format&fit=crop"
            ]),
            json.dumps(["Platinum / Royal Blue", "Yellow Gold / Emerald Green"]),
            5.0,
            14,
            "Baru",
            0
        )
    ]

    for p in products:
        cursor.execute("""
        INSERT INTO products 
        (category_id, name, slug, description, price, original_price, stock, sku, image_url, gallery_json, variants_json, rating, reviews_count, badge, is_featured)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, p)

    # 4. Vouchers
    vouchers = [
        ("LUXE10", "percent", 10, 500000, 500000, 100, 12, 1, "2027-12-31"),
        ("ELEGANT50K", "fixed", 50000, 250000, 50000, 500, 89, 1, "2027-12-31"),
        ("VIPMEMBER", "percent", 20, 2000000, 1500000, 50, 4, 1, "2027-12-31")
    ]
    for v in vouchers:
        cursor.execute("""
        INSERT INTO vouchers (code, discount_type, discount_value, min_spend, max_discount, usage_limit, used_count, is_active, expires_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, v)

    # 5. Settings
    settings = [
        ("store_name", "Ranzzstore"),
        ("store_tagline", "Modern Luxury & Premium Lifestyle"),
        ("store_currency", "IDR"),
        ("store_phone", "+62 812-8888-7799"),
        ("store_email", "concierge@ranzzstore.com"),
        ("store_address", "Senopati Suites Tower 2, Penthouse Level, Kebayoran Baru, Jakarta"),
        ("tax_rate", "11"), # 11% PPN
        ("enable_qris", "1"),
        ("enable_va", "1"),
        ("enable_cod", "1")
    ]
    for k, v in settings:
        cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (k, v))

    # 6. Sample Initial Orders (To populate Admin Dashboard & Order Tracker immediately)
    p1 = cursor.execute("SELECT id, name, price, image_url FROM products WHERE sku='AUR-WATCH-001'").fetchone()
    p2 = cursor.execute("SELECT id, name, price, image_url FROM products WHERE sku='AUR-BAG-001'").fetchone()
    p3 = cursor.execute("SELECT id, name, price, image_url FROM products WHERE sku='AUR-PERF-001'").fetchone()

    sample_orders = [
        (
            "ORD-20261020-001",
            1,
            "Budi Pratama",
            "customer@gmail.com",
            "08123456789",
            "Jl. Wijaya Timur No. 45",
            "Jakarta Selatan",
            "12170",
            "JNE YES (Yakin Esok Sampai)",
            35000,
            "JNE-ID982347101X",
            14500000,
            500000,
            "LUXE10",
            14035000,
            "QRIS",
            "paid",
            "shipped",
            "Tolong di-bubble wrap tebal ya, terima kasih.",
            "2026-10-20 14:20:00"
        ),
        (
            "ORD-20261021-002",
            None,
            "Clarissa Stephanie",
            "clarissa.s@luxury.id",
            "081399887766",
            "Apartemen Dharmawangsa Residence Lantai 18",
            "Jakarta Selatan",
            "12160",
            "GoSend Instant Courier",
            50000,
            "GOSEND-88291033",
            5750000,
            50000,
            "ELEGANT50K",
            5750000,
            "BCA_VA",
            "paid",
            "processing",
            "Harap konfirmasi sebelum dikirim kurir.",
            "2026-10-21 09:15:00"
        ),
        (
            "ORD-20261021-003",
            None,
            "Hendrawan Kusuma",
            "hendrawan.k@gmail.com",
            "08177654321",
            "Jl. Diponegoro No. 88",
            "Surabaya",
            "60241",
            "SiCepat BEST Express",
            45000,
            None,
            3200000,
            0,
            None,
            3245000,
            "MANDIRI_VA",
            "unpaid",
            "pending",
            "Dikirim dengan kemasan kado mewah jika bisa.",
            "2026-10-21 17:40:00"
        )
    ]

    for ord in sample_orders:
        cursor.execute("""
        INSERT INTO orders 
        (order_number, user_id, customer_name, customer_email, customer_phone, shipping_address, shipping_city, shipping_postal_code, shipping_courier, shipping_cost, tracking_number, subtotal, discount_amount, voucher_code, total, payment_method, payment_status, order_status, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ord)
        order_id = cursor.lastrowid

        if ord[0] == "ORD-20261020-001":
            cursor.execute("""
            INSERT INTO order_items (order_id, product_id, product_name, product_price, quantity, subtotal, selected_variant, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (order_id, p1['id'], p1['name'], p1['price'], 1, p1['price'], "Rose Gold / Black", p1['image_url']))
        elif ord[0] == "ORD-20261021-002":
            cursor.execute("""
            INSERT INTO order_items (order_id, product_id, product_name, product_price, quantity, subtotal, selected_variant, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (order_id, p2['id'], p2['name'], p2['price'], 1, p2['price'], "Cognac Brown", p2['image_url']))
        elif ord[0] == "ORD-20261021-003":
            cursor.execute("""
            INSERT INTO order_items (order_id, product_id, product_name, product_price, quantity, subtotal, selected_variant, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (order_id, p3['id'], p3['name'], p3['price'], 1, p3['price'], "100ml Extrait", p3['image_url']))

    # 7. Sample Reviews
    reviews = [
        (p1['id'], "Budi Pratama", 5, "Kualitas jam tangan di luar ekspektasi! Finishing sangat halus, packaging mewah serasa unboxing brand Swiss kelas atas."),
        (p1['id'], "Dr. Kevin Nugroho", 5, "Akurasi pergerakan automaticnya luar biasa. Strap kulitnya nyaman sekali dipakai seharian."),
        (p2['id'], "Clarissa Stephanie", 5, "Kulit aslinya wangi khas vegetable-tanned, kompartemen laptop sangat aman dan jahitan super presisi."),
        (p3['id'], "Reza Rahardian", 5, "Projection dan sillage parfum ini sangat berkelas, tidak menyengat tapi tahan lebih dari 12 jam di jas.")
    ]
    for r in reviews:
        cursor.execute("INSERT INTO reviews (product_id, customer_name, rating, comment) VALUES (?, ?, ?, ?)", r)

    conn.commit()
    conn.close()
    print("Database seeding completed successfully.")

if __name__ == '__main__':
    seed()
