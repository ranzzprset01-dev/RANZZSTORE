# ✦ RANZZSTORE — Modern Luxury E-Commerce & Smart Business Suite ✦

Aplikasi toko online modern dan berkelas internasional yang dirancang khusus untuk butik kemewahan (*haute horlogerie*, kerajinan kulit murni, *haute parfumerie*, dan aksesoris eksklusif). Aplikasi ini dilengkapi dengan rangkaian tools operasional e-commerce yang sangat komprehensif, mulai dari sistem kasir offline (POS), pelacakan pengiriman beresiko tinggi, manajemen inventaris stok otomatis, generator faktur invoice cetak, hingga dasbor analitik penjualan berbasis Chart.js.

---

## 💎 Fitur Tampilan Modern & Berkelas ("Luxury Aesthetic")
- **Palet Warna Mewah**: Obsidian Black, Champagne Gold, & Warm Bronze dengan aksen Emerald & Ruby.
- **Tipografi Berkelas**: Kombinasi font elegan *Playfair Display* (klasik mewah) dan *Plus Jakarta Sans* (modern & tajam).
- **Glassmorphism & Micro-Interactions**: Efek kaca frosted blur, kartu produk dengan bayangan lembut, transisi halus, dan animasi zoom pada hover.
- **Responsive & Mobile-First**: Tampilan optimal di perangkat smartphone, tablet, maupun desktop layar lebar.
- **Interactive Sliding Cart Drawer**: Tas belanja dinamis yang meluncur dari samping layar tanpa perlu me-refresh halaman.
- **Wishlist Impian Pribadi**: Sistem simpan mahakarya favorit tersimpan otomatis di perangkat pengguna.
- **Sistem Ulasan & Rating Bintang**: Pelanggan dapat memberikan rating dan ulasan pengalaman langsung pada setiap halaman produk.

---

## 🛠️ Tools Lengkap yang Tersedia dalam Aplikasi

| Tool | Fungsi & Fitur Utama |
|---|---|
| **1. Tool Kasir Toko / POS (Point of Sale)** | Terminal kasir langsung untuk penjualan fisik di butik. Dilengkapi pencarian kilat produk/barcode SKU, kalkulator kembalian uang tunai otomatis, dan generator struk belanja termal siap cetak (*one-click print thermal receipt*). |
| **2. Tool Pelacak Pesanan Waktu Nyata (Order Tracker)** | Pelacakan status pengiriman 5 tahap (*Pesanan Dibuat -> Pembayaran Diterima -> Sedang Dikemas -> Dalam Pengiriman Kurir -> Selesai*). Menampilkan nomor resi kurir (JNE, SiCepat, GoSend) dan rincian paket. |
| **3. Tool Generator & Cetak Invoice Resmi (Printable Invoice)** | Cetak faktur tagihan resmi A4/PDF berstandar butik internasional dengan logo perusahaan, rincian pajak/PPN, stempel autentikasi digital, dan kode QR verifikasi legalitas. |
| **4. Tool Manajemen Kupon & Voucher Promo (Promo Engine)** | Buat kode diskon baru dengan tipe persentase (`%`) atau nominal rupiah tetap (`Rp`), batas minimal belanja, batas maksimal diskon, dan batas kuota penggunaan. |
| **5. Tool Analitik & Metrik Penjualan (Analytics Dashboard)** | Visualisasi omset transaksi lunas, total pesanan, grafik tren penjualan harian (Line Chart), komposisi katalog per kategori (Doughnut Chart), dan notifikasi stok menipis. |
| **6. Tool Peringatan Stok Kritis (Low Stock Warning)** | Indikator visual otomatis untuk produk dengan sisa stok $\le 5$ unit, dilengkapi tombol *1-Click Restock (+10 Unit)* untuk pengisian stok instan. |
| **7. Tool Ekspor Laporan CSV / Excel** | Ekspor seluruh riwayat transaksi penjualan dan seluruh data katalog produk ke dalam format file `.csv` untuk keperluan pembukuan keuangan. |
| **8. Tool Simulasi Multi-Pembayaran & Multi-Kurir** | Dukungan simulasi QRIS Dinamis, Virtual Account Bank (BCA, Mandiri, BRI, BNI), Kartu Kredit 3D Secure, dan Kurir COD dengan pilihan tarif ekspedisi JNE YES, SiCepat BEST, Paxel Vault, & GoSend Instant. |

---

## 🚀 Cara Menjalankan Aplikasi

### Opsi 1: Menggunakan File Batch (Paling Praktis di Windows)
Cukup klik ganda (double click) pada file:
```
run.bat
```

### Opsi 2: Menggunakan Terminal PowerShell / CMD
1. Buka folder proyek ini di terminal:
   ```powershell
   cd "d:\project toko online"
   ```
2. Inisialisasi basis data awal (sudah berisi produk mewah dan data pesanan contoh):
   ```powershell
   python seed_data.py
   ```
3. Jalankan server aplikasi:
   ```powershell
   python app.py
   ```
4. Buka peramban (browser) Anda dan akses:
   - **Etalase Toko**: [http://localhost:5000](http://localhost:5000)
   - **Panel Admin Suite**: [http://localhost:5000/admin](http://localhost:5000/admin)
   - **Terminal Kasir POS**: [http://localhost:5000/admin/pos](http://localhost:5000/admin/pos)
   - **Pelacak Pesanan**: [http://localhost:5000/track-order](http://localhost:5000/track-order)

---

## 🔐 Akun Demo untuk Uji Coba

Halaman login telah dilengkapi tombol **1-Klik Demo Login** sehingga Anda tidak perlu mengetik manual:

### 1. Akun Administrator (Akses Penuh Seluruh Tools)
- **Email**: `admin@ranzzstore.com`
- **Kata Sandi**: `admin123`
- **Hak Akses**: Mengelola stok produk, mengubah status pesanan & input nomor resi pengiriman, membuat voucher promo, mengoperasikan mesin kasir POS, mencetak invoice, serta mengekspor laporan penjualan.

### 2. Akun Pelanggan VIP
- **Email**: `customer@gmail.com`
- **Kata Sandi**: `user123`
- **Hak Akses**: Menjelajahi katalog, menambah ke tas belanja, menyimpan ke daftar impian (*wishlist*), menggunakan voucher promo, melakukan checkout, dan melacak status pesanan.

---

## 🎟️ Kode Voucher Promo Aktif untuk Dicoba
- `LUXE10` : Diskon 10% (Min. belanja Rp 500.000, Maks. diskon Rp 500.000)
- `ELEGANT50K` : Potongan langsung Rp 50.000 (Min. belanja Rp 250.000)
- `VIPMEMBER` : Diskon 20% (Min. belanja Rp 2.000.000, Maks. diskon Rp 1.500.000)

---

## 📦 Contoh Nomor Pesanan untuk Uji Pelacak (Track Order)
- `ORD-20261020-001` (Status: Dikirim / Resi: `JNE-ID982347101X`)
- `ORD-20261021-002` (Status: Sedang Diproses / Resi: `GOSEND-88291033`)
- `ORD-20261021-003` (Status: Menunggu Pembayaran)

---

## 📁 Struktur Berkas Proyek

```
d:\project toko online\
├── app.py                      # Server backend Flask & API endpoint
├── models.py                   # Struktur tabel SQLite & koneksi database
├── seed_data.py                # Data awal: katalog produk, kategori, voucher, pesanan
├── database.db                 # Berkas basis data SQLite
├── requirements.txt            # Daftar pustaka Python yang dibutuhkan
├── run.bat                     # Skrip 1-klik untuk menjalankan aplikasi di Windows
├── README.md                   # Dokumentasi lengkap aplikasi
├── static/
│   ├── css/
│   │   └── custom.css          # Desain mewah, tema gelap, gold accents, glassmorphism
│   └── js/
│       └── main.js             # Logika keranjang belanja dinamis, voucher, & wishlist
└── templates/
    ├── base.html               # Tata letak utama butik (navbar, drawer cart, footer)
    ├── index.html              # Halaman beranda mewah dengan showcase mahakarya
    ├── shop.html               # Halaman katalog dengan filter kategori, harga, & sort
    ├── product_detail.html     # Halaman detail produk, varian, galeri foto, & ulasan
    ├── cart.html               # Halaman tas belanja dengan kalkulator voucher
    ├── checkout.html           # Formulir checkout multi-langkah (kurir & pembayaran)
    ├── order_success.html      # Konfirmasi pesanan & simulator QRIS / Virtual Account
    ├── track_order.html        # Tool pelacakan pesanan & resi kurir interaktif
    ├── wishlist.html           # Halaman daftar impian mahakarya tersimpan
    ├── invoice.html            # Tool faktur invoice resmi siap cetak A4/PDF
    ├── auth/
    │   ├── login.html          # Halaman masuk akun dengan tombol 1-klik demo
    │   └── register.html       # Halaman pendaftaran anggota baru
    └── admin/
        ├── layout.html         # Kerangka panel admin dengan sidebar menu
        ├── dashboard.html      # Dasbor analitik, grafik omset Chart.js, & peringatan stok
        ├── products.html       # Tool manajemen produk (tambah, edit, hapus, restock)
        ├── orders.html         # Tool manajemen pesanan & filter status pengiriman
        ├── order_detail.html   # Tool update status kurir & input nomor resi
        ├── vouchers.html       # Tool pembuatan kupon diskon & promosi
        ├── pos.html            # Tool mesin kasir butik (POS) & cetak struk kasir
        └── settings.html       # Tool pengaturan profil butik, alamat, & pajak PPN
```
