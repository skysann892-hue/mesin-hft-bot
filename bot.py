import time
import requests
from datetime import datetime
from flask import Flask
import threading
import os
import statistics

# ==================================================
# 1. INISIALISASI PENYAMARAN WEB (FLASK)
# ==================================================
app = Flask(__name__)

@app.route('/')
def home():
    return "Lapor! Markas Bot HFT Aktif dan Berjalan!"

# ==================================================
# 2. MESIN UTAMA BOT TRADING (SUPER LITE)
# ==================================================
def jalankan_bot():
    TELEGRAM_TOKEN = "8245773813:AAEkD4fEBRyAsZdwXjN0OSV6zXGObOpG7Ww"
    CHAT_ID = "6407479740"

    def kirim_laporan_telegram(pesan):
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = {"chat_id": CHAT_ID, "text": pesan, "parse_mode": "Markdown"}
            requests.post(url, json=payload)
        except Exception as e:
            print(f"⚠️ Gagal menghantar laporan ke Telegram: {e}")

    # Menggunakan API awam Binance terus tanpa ccxt
    symbol = 'BTCUSDT'
    url_binance = f"https://api.binance.us/api/v3/klines?symbol={symbol}&interval=1m&limit=60"

    saldo_usdt = 100.0
    posisi = "KOSONG"     
    harga_masuk = 0.0     
    ukuran_kontrak = 0.0  

    ambang_z = 2.0

    print("==================================================")
    print("⚔️ MESIN HFT SUPER LITE + ALARM TELEGRAM AKTIF!")
    print(f"Mengintai: {symbol} | Batas: Z-Score +/- {ambang_z}")
    print("==================================================\n")

    kirim_laporan_telegram("🤖 *Lapor, Komandan!* Mesin HFT Super Lite rasmi diaktifkan di Termux. Bebas halangan!")

    while True:
        try:
            # Menyedot data pasaran secara terus (Sangat pantas dan ringan)
            respons = requests.get(url_binance).json()
            
            # Mengambil hanya harga 'close' (indeks ke-4) dan mengubahnya menjadi nombor (float)
            daftar_close = [float(lilin[4]) for lilin in respons]
            
            harga_sekarang = daftar_close[-1]
            ma = statistics.mean(daftar_close)
            
            try:
                std = statistics.stdev(daftar_close)
            except statistics.StatisticsError:
                std = 0.0001
                
            if std == 0: std = 0.0001 
            
            z_score = (harga_sekarang - ma) / std
            waktu = datetime.now().strftime('%H:%M:%S')
            
            print(f"[{waktu}] Harga: {harga_sekarang:.2f} | Z-Score: {z_score:+.2f} | Status: {posisi}")
            
            # Logika Eksekusi Trading
            if posisi == "KOSONG" and z_score < -ambang_z:
                posisi = "LONG"
                harga_masuk = harga_sekarang
                ukuran_kontrak = saldo_usdt / harga_sekarang
                notifikasi = f"🟢 *[ALARM BUKA LONG]*\n📉 Z-Score ekstrem: {z_score:.2f}\n💰 Membeli kontrak pada harga: {harga_masuk:.2f} USDT"
                kirim_laporan_telegram(notifikasi)
                
            elif posisi == "KOSONG" and z_score > ambang_z:
                posisi = "SHORT"
                harga_masuk = harga_sekarang
                ukuran_kontrak = saldo_usdt / harga_sekarang
                notifikasi = f"🔴 *[ALARM BUKA SHORT]*\n📈 Z-Score ekstrem: {z_score:.2f}\n🎯 Menjual kosong pada harga: {harga_masuk:.2f} USDT"
                kirim_laporan_telegram(notifikasi)

            elif posisi == "LONG" and z_score >= 0:
                saldo_usdt = ukuran_kontrak * harga_sekarang
                posisi = "KOSONG"
                notifikasi = f"💰 *[TAKE PROFIT LONG SUCCESS]*\n⚖️ Z-Score normal: {z_score:.2f}\n🚪 Keluar pada harga: {harga_sekarang:.2f}\n💵 Baki: {saldo_usdt:.4f} USDT"
                kirim_laporan_telegram(notifikasi)

            elif posisi == "SHORT" and z_score <= 0:
                profit = (harga_masuk - harga_sekarang) * ukuran_kontrak
                saldo_usdt = saldo_usdt + profit
                posisi = "KOSONG"
                notifikasi = f"💰 *[TAKE PROFIT SHORT SUCCESS]*\n⚖️ Z-Score normal: {z_score:.2f}\n🚪 Keluar pada harga: {harga_sekarang:.2f}\n💵 Baki: {saldo_usdt:.4f} USDT"
                kirim_laporan_telegram(notifikasi)
                
            time.sleep(10)
            
        except Exception as e:
            print(f"⚠️ Radar terganggu: {e}")
            time.sleep(5)

# ==================================================
# 3. PEMICU PELUNCURAN
# ==================================================
if __name__ == "__main__":
    bot_thread = threading.Thread(target=jalankan_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
        
