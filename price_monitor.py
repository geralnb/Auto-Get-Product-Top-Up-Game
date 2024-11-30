from decouple import config
import os
import requests
import json
from dotenv import load_dotenv

# Base URL for the API
BASE_URL = "https://api.tokovoucher.net/produk/code"
# Load file .env
load_dotenv()

MEMBER_CODE = os.getenv("MEMBER_CODE")
SIGNATURE = os.getenv("SIGNATURE")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

print(f"TELEGRAM_TOKEN: {TELEGRAM_TOKEN}")
print(f"TELEGRAM_CHAT_ID: {TELEGRAM_CHAT_ID}")

# File untuk menyimpan data lama
DATA_FILE = "data_old.json"

# Function untuk mengirim pesan ke Telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, data=payload)
        print(f"Response Telegram: {response.status_code} - {response.text}")
        response.raise_for_status()  # Akan melempar error jika status code >= 400
    except requests.exceptions.RequestException as e:
        print(f"Error saat mengirim notifikasi Telegram: {e}")

# Function untuk fetch data
def fetch_code_data(codes):
    data = []
    for code in codes:
        url = f"{BASE_URL}?member_code={MEMBER_CODE}&signature={SIGNATURE}&kode={code}"
        response = requests.get(url)
        if response.status_code == 200:
            json_data = response.json()
            if "data" in json_data and len(json_data["data"]) > 0:
                produk_data = json_data["data"][0]  # Ambil elemen pertama
                nama_produk = produk_data.get("nama_produk", "N/A")
                price = produk_data.get("price", "N/A")
                data.append({"kode": code, "nama_produk": nama_produk, "price": price})
        else:
            data.append({"kode": code, "nama_produk": "Error", "price": "Error"})
    return data

# Function untuk membaca data lama
def read_old_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    return {}

# Function untuk menyimpan data baru
def save_new_data(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)

# Function untuk mendeteksi perubahan harga
def detect_price_change(new_data, old_data):
    changed = []
    unchanged = []
    for item in new_data:
        kode = item["kode"]
        new_price = item["price"]
        old_price = old_data.get(kode, {}).get("price")
        if new_price != old_price:
            changed.append({
                "kode": kode,
                "nama_produk": item["nama_produk"],
                "price_baru": new_price,
                "price_lama": old_price if old_price else "N/A"
            })
        else:
            unchanged.append({
                "kode": kode,
                "nama_produk": item["nama_produk"],
                "price": new_price
            })
    return changed, unchanged

# Main function untuk memeriksa perubahan harga
def main():
    codes = ["MLAWP1", "MLA12976", "MLA2195", "MLA1412", "MLA1220", "MLA878", "MLBB716"]  # Tambahkan kode lainnya sesuai kebutuhan
    new_data = fetch_code_data(codes)

    # Baca data lama
    old_data = read_old_data()

    if not old_data:  # Jika data lama tidak ada
        print("Data lama tidak ditemukan. Menyimpan data baru sebagai data lama...")
        save_new_data({item["kode"]: item for item in new_data})
        print("Data baru telah disimpan.")
        return

    # Deteksi perubahan harga
    changed, unchanged = detect_price_change(new_data, old_data)

    # Pesan notifikasi Telegram
    message = ""
    if changed:
        print("Perubahan harga terdeteksi:")
        message += "<b>Perubahan Harga Terdeteksi:</b>\n"
        for item in changed:
            print(f"Kode: {item['kode']}, Nama: {item['nama_produk']}, Harga Lama: {item['price_lama']}, Harga Baru: {item['price_baru']}")
            message += (f"- Kode: <b>{item['kode']}</b>\n"
                        f"  Nama: {item['nama_produk']}\n"
                        f"  Harga Lama: <s>{item['price_lama']}</s>\n"
                        f"  Harga Baru: <b>{item['price_baru']}</b>\n\n")
    if unchanged:
        print("Tidak ada perubahan harga untuk produk berikut:")
        message += "<b>Tidak Ada Perubahan Harga:</b>\n"
        for item in unchanged:
            print(f"Kode: {item['kode']}, Nama: {item['nama_produk']}, Harga: {item['price']}")
            message += (f"- Kode: <b>{item['kode']}</b>\n"
                        f"  Nama: {item['nama_produk']}\n"
                        f"  Harga: <b>{item['price']}</b>\n"
                        f"  Tidak ada perubahan harga\n\n")

    # Kirim notifikasi Telegram
    send_telegram_message(message)

    # Simpan data baru
    save_new_data({item["kode"]: item for item in new_data})
    
    # Akses endpoint export_xlsx
    try:
        export_response = requests.get("http://127.0.0.1:5000/export_xlsx?codes=" + ",".join(codes))
        if export_response.status_code == 200:
            print("File Excel berhasil diekspor!")
            send_telegram_message("File Excel berhasil diekspor!")
        else:
            print(f"Gagal mengekspor file Excel. Status: {export_response.status_code}")
            send_telegram_message(f"Gagal mengekspor file Excel. Status: {export_response.status_code}")
    except requests.exceptions.ConnectionError as e:
        print("Gagal menghubungi server untuk ekspor Excel:", e)
        send_telegram_message("Gagal menghubungi server untuk ekspor Excel.")

if __name__ == "__main__":
    main()
