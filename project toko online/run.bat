@echo off
chcp 65001 > nul
cls
echo ======================================================================
echo    ✦ RANZZSTORE — MODERN LUXURY E-COMMERCE & SMART ADMIN TOOLS ✦
echo ======================================================================
echo.
echo [1/2] Menyiapkan basis data SQLite dan data awal produk mewah...
python seed_data.py
echo.
echo [2/2] Memulai server web Toko Online...
echo URL Toko Online: http://localhost:5000
echo Panel Admin   : http://localhost:5000/admin (admin@ranzzstore.com / admin123)
echo.
echo Tekan Ctrl+C di jendela ini untuk menghentikan server kapan saja.
echo ======================================================================
python app.py
pause
