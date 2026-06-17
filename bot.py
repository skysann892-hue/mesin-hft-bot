import ccxt
import pandas as pd
import time
import requests
from datetime import datetime

# ==================================================
# PENGATURAN TELEGRAM KUSTOM KOMANDAN
# ==================================================
TELEGRAM_TOKEN = "8245773813:AAEkD4fEBRyAsZdwXjN0OSV6zXGObOpG7Ww"
CHAT_ID = "6407479740"

def kirim_laporan_telegram(pesan):
    """Fungsi khusus untuk mengirimkan sinyal radio ke Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": pesan, "parse_mode": "Markdown"}
        requests.post(url, json=payload)
    except Exception as e:
        print(f"⚠️ Gagal mengirim laporan ke Telegram: {e}")

# ==================================================
# MESIN HFT FUTURES DUA ARAH (LONG & SHORT)
# ==================================================
exchange = ccxt.binanceus()
symbol = 'BTC/USDT'

saldo_usdt = 100.0
posisi = "KOSONG"     
harga_masuk = 0.0     
ukuran_kontrak = 0.0  

ambang_z = 2.0
window_size = 60 

print("==================================================")
print("⚔️ MESIN HFT FUTURES + ALARM TELEGRAM AKTIF!")
print(f"Mengintai: {symbol} | Batas: Z-Score +/- {ambang_z}")
print("==================================================\n")

# Mengirimkan pesan tes ke handphone Anda saat mesin dinyalakan
kirim_laporan_telegram("🤖 *Lapor, Komandan!* Mesin HFT Futures Anda resmi diaktifkan. Radar siap berburu!")

while True:
    try:
        # Menarik data dari bursa
        ohlcv = exchange.fetch_ohlcv(symbol, '1m', limit=window_size)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        harga_sekarang = df['close'].iloc[-1]
        ma = df['close'].mean()
        std = df['close'].std()
        if std == 0: std = 0.0001 
        
        z_score = (harga_sekarang - ma) / std
        waktu = datetime.now().strftime('%H:%M:%S')
        
        print(f"[{waktu}] Harga: {harga_sekarang:.2f} | Z-Score: {z_score:+.2f} | Status: {posisi}")
        
        # 1. EKSEKUSI BUKA LONG (Pasar Panik / Oversold)
        if posisi == "KOSONG" and z_score < -ambang_z:
            posisi = "LONG"
            harga_masuk = harga_sekarang
            ukuran_kontrak = saldo_usdt / harga_sekarang
            
            notifikasi = f"🟢 *[ALARM BUKA LONG]*\n📉 Z-Score ekstrem: {z_score:.2f}\n💰 Membeli kontrak di harga: {harga_masuk:.2f} USDT"
            kirim_laporan_telegram(notifikasi)
            
        # 2. EKSEKUSI BUKA SHORT (Pasar Euforia / Overbought)
        elif posisi == "KOSONG" and z_score > ambang_z:
            posisi = "SHORT"
            harga_masuk = harga_sekarang
            ukuran_kontrak = saldo_usdt / harga_sekarang
            
            notifikasi = f"🔴 *[ALARM BUKA SHORT]*\n📈 Z-Score ekstrem: {z_score:.2f}\n🎯 Menjual kosong di harga: {harga_masuk:.2f} USDT"
            kirim_laporan_telegram(notifikasi)

        # 3. TUTUP POSISI LONG (Ambil Keuntungan)
        elif posisi == "LONG" and z_score >= 0:
            saldo_usdt = ukuran_kontrak * harga_sekarang
            posisi = "KOSONG"
            
            notifikasi = f"💰 *[TAKE PROFIT LONG SUCCESS]*\n⚖️ Z-Score kembali normal: {z_score:.2f}\n🚪 Keluar di harga: {harga_sekarang:.2f}\n💵 Total Saldo: {saldo_usdt:.4f} USDT"
            kirim_laporan_telegram(notifikasi)

        # 4. TUTUP POSISI SHORT (Ambil Keuntungan)
        elif posisi == "SHORT" and z_score <= 0:
            profit = (harga_masuk - harga_sekarang) * ukuran_kontrak
            saldo_usdt = saldo_usdt + profit
            posisi = "KOSONG"
            
            notifikasi = f"💰 *[TAKE PROFIT SHORT SUCCESS]*\n⚖️ Z-Score kembali normal: {z_score:.2f}\n🚪 Keluar di harga: {harga_sekarang:.2f}\n💵 Total Saldo: {saldo_usdt:.4f} USDT"
            kirim_laporan_telegram(notifikasi)
            
        time.sleep(10) # Istirahat 10 detik sebelum memindai lagi
        
    except Exception as e:
        print(f"⚠️ Radar terganggu: {e}")
        time.sleep(5)
