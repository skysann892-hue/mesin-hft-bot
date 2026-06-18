import time
import requests
from datetime import datetime
from flask import Flask
import threading
import os
import statistics
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==================================================
# 1. INISIALISASI PENYAMARAN WEB (FLASK)
# ==================================================
app = Flask(__name__)

@app.route('/')
def home():
    return "Lapor! Markas Bot HFT Aktif dan Berjalan!"

# ==================================================
# 2. MESIN UTAMA BOT TRADING (EDISI BYBIT)
# ==================================================
def jalankan_bot():
    TELEGRAM_TOKEN = "8245773813:AAEkD4fEBRyAsZdwXjN0OSV6zXGObOpG7Ww"
    CHAT_ID = "6407479740"

    def kirim_laporan_telegram(pesan):
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = {"chat_id": CHAT_ID, "text": pesan, "parse_mode": "Markdown"}
            requests.post(url, json=payload, verify=False)
        except Exception as e:
            pass

    # MENGGUNAKAN JALUR API BYBIT V5 (PASAR FUTURES / LINEAR)
    symbol = 'BTCUSDT'
    url_bybit = f"https://api.bybit.com/v5/market/kline?category=linear&symbol={symbol}&interval=1&limit=60"

    saldo_usdt = 100.0
    posisi = "KOSONG"     
    harga_masuk = 0.0     
    ukuran_kontrak = 0.0  

    ambang_z = 2.0

    print("==================================================")
    print("⚔️ MESIN HFT SUPER LITE (BYBIT) + ALARM TELEGRAM AKTIF!")
    print(f"Mengintai: {symbol} | Batas: Z-Score +/- {ambang_z}")
    print("==================================================\n")

    kirim_laporan_telegram("🤖 *Lapor, Komandan!* Radar telah digeser. Mesin HFT kini memantau markas BYBIT!")

    while True:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            respons_raw = requests.post(url_bybit, headers=headers, verify=False) if requests.request == "POST" else requests.get(url_bybit, headers=headers, verify=False)
            
            if respons_raw.status_code != 200:
                print(f"⚠️ Radar terganggu (Kode {respons_raw.status_code}). Menunggu jalur aman...")
                time.sleep(10)
                continue
                
            respons = respons_raw.json()
            
            # Membongkar brankas data Bybit
            data_kline = respons.get('result', {}).get('list', [])
            
            if not data_kline:
                print("⚠️ Gagal menyedot data dari Bybit. Mengulang...")
                time.sleep(5)
                continue
            
            # Taktik Membalik Urutan: Bybit mengirim data terbaru di awal. Kita balik agar sesuai rumusan kita.
            data_kline.reverse()
            
            # Mengambil harga 'close' (indeks ke-4, strukturnya sama persis dengan Binance)
            daftar_close = [float(lilin[4]) for lilin in data_kline]
            harga_sekarang = daftar_close[-1]
            ma = statistics.mean(daftar_close)
            
            try:
                std = statistics.stdev(daftar_close)
            except:
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
                notifikasi = f"🟢 *[ALARM BUKA LONG - BYBIT]*\n📉 Z-Score ekstrem: {z_score:.2f}\n💰 Membeli kontrak di harga: {harga_masuk:.2f} USDT"
                kirim_laporan_telegram(notifikasi)
                
            elif posisi == "KOSONG" and z_score > ambang_z:
                posisi = "SHORT"
                harga_masuk = harga_sekarang
                ukuran_kontrak = saldo_usdt / harga_sekarang
                notifikasi = f"🔴 *[ALARM BUKA SHORT - BYBIT]*\n📈 Z-Score ekstrem: {z_score:.2f}\n🎯 Menjual kosong di harga: {harga_masuk:.2f} USDT"
                kirim_laporan_telegram(notifikasi)

            elif posisi == "LONG" and z_score >= 0:
                saldo_usdt = ukuran_kontrak * harga_sekarang
                posisi = "KOSONG"
                notifikasi = f"💰 *[TAKE PROFIT LONG SUCCESS]*\n⚖️ Z-Score normal: {z_score:.2f}\n🚪 Keluar di harga: {harga_sekarang:.2f}\n💵 Total Saldo: {saldo_usdt:.4f} USDT"
                kirim_laporan_telegram(notifikasi)

            elif posisi == "SHORT" and z_score <= 0:
                profit = (harga_masuk - harga_sekarang) * ukuran_kontrak
                saldo_usdt = saldo_usdt + profit
                posisi = "KOSONG"
                notifikasi = f"💰 *[TAKE PROFIT SHORT SUCCESS]*\n⚖️ Z-Score normal: {z_score:.2f}\n🚪 Keluar di harga: {harga_sekarang:.2f}\n💵 Total Saldo: {saldo_usdt:.4f} USDT"
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
