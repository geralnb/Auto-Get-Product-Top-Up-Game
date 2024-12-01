from decouple import config
import os
import requests
import json
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_file
import pandas as pd

app = Flask(__name__)
load_dotenv('/home/ubuntu/python/.env', override=True)

# Base URL for the API
BASE_URL = "https://api.tokovoucher.net/produk/code"

# Load environment variables
MEMBER_CODE = os.getenv("MEMBER_CODE")
SIGNATURE = os.getenv("SIGNATURE")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

DATA_FILE = "data_old.json"

# Function to send messages to Telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        response = requests.post(url, data=payload)
        print(f"Response Telegram: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error saat mengirim notifikasi Telegram: {e}")

# Function to send files to Telegram
def send_telegram_file(file_path, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
    try:
        with open(file_path, "rb") as file:
            files = {"document": file}
            data = {"chat_id": TELEGRAM_CHAT_ID, "caption": caption}
            response = requests.post(url, data=data, files=files)
            print(f"Response Telegram File: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error saat mengirim file ke Telegram: {e}")

# Function to fetch data
def fetch_code_data(codes):
    data = []
    for code in codes:
        url = f"{BASE_URL}?member_code={MEMBER_CODE}&signature={SIGNATURE}&kode={code}"
        response = requests.get(url)
        if response.status_code == 200:
            json_data = response.json()
            if "data" in json_data and len(json_data["data"]) > 0:
                produk_data = json_data["data"][0]
                nama_produk = produk_data.get("nama_produk", "N/A")
                price = produk_data.get("price", "N/A")
                data.append({"kode": code, "nama_produk": nama_produk, "price": price})
        else:
            data.append({"kode": code, "nama_produk": "Error", "price": "Error"})
    return data

# Function to read old data
def read_old_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    return {}

# Function to save new data
def save_new_data(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)

# Function to detect price changes
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

# Flask endpoint to handle Excel export
@app.route('/export_xlsx', methods=['GET'])
def export_xlsx():
    codes = request.args.get('codes', '').split(',')
    if not codes:
        return jsonify({"error": "No codes provided"}), 400

    # Fetch data
    new_data = fetch_code_data(codes)

    # Read old data
    old_data = read_old_data()

    # Detect price changes
    changed, unchanged = detect_price_change(new_data, old_data)

    # Build notification message
    if changed:
        message = "<b>Perubahan Harga Terdeteksi:</b>\n"
        for item in changed:
            message += (f"- Kode: <b>{item['kode']}</b>\n"
                        f"  Nama: {item['nama_produk']}\n"
                        f"  Harga Lama: <s>{item['price_lama']}</s>\n"
                        f"  Harga Baru: <b>{item['price_baru']}</b>\n\n")
    else:
        message = "<b>Tidak Ada Perubahan Harga</b>\n"

    if unchanged:
        message += "<b>Produk Tanpa Perubahan Harga:</b>\n"
        for item in unchanged:
            message += (f"- Kode: <b>{item['kode']}</b>\n"
                        f"  Nama: {item['nama_produk']}\n"
                        f"  Harga: <b>{item['price']}</b>\n\n")

    # Send notification to Telegram
    send_telegram_message(message)

    # Save Excel file
    excel_file = "exported_data.xlsx"
    try:
        df = pd.DataFrame(new_data)
        df.to_excel(excel_file, index=False)

        # Send file notification to Telegram
        caption = "File Excel berhasil diekspor dan berisi data terbaru."
        send_telegram_file(excel_file, caption)

        # Save new data
        save_new_data({item["kode"]: item for item in new_data})

        return send_file(excel_file, as_attachment=True)
    except Exception as e:
        error_message = f"Error saat membuat atau mengirim file Excel: {e}"
        print(error_message)
        send_telegram_message(error_message)
        return jsonify({"error": error_message}), 500

# Main function for standalone execution
def main():
    codes = ["MLAWP1", "MLA12976", "MLA2195", "MLA1412", "MLA1220", "MLA878", "MLBB716"]
    new_data = fetch_code_data(codes)

    # Read old data
    old_data = read_old_data()

    # Detect price changes
    changed, unchanged = detect_price_change(new_data, old_data)

    # Notify changes
    if changed:
        message = "<b>Perubahan Harga Terdeteksi:</b>\n"
        for item in changed:
            message += (f"- Kode: <b>{item['kode']}</b>\n"
                        f"  Nama: {item['nama_produk']}\n"
                        f"  Harga Lama: <s>{item['price_lama']}</s>\n"
                        f"  Harga Baru: <b>{item['price_baru']}</b>\n\n")
    else:
        message = "<b>Tidak Ada Perubahan Harga</b>\n"

    if unchanged:
        message += "<b>Produk Tanpa Perubahan Harga:</b>\n"
        for item in unchanged:
            message += (f"- Kode: <b>{item['kode']}</b>\n"
                        f"  Nama: {item['nama_produk']}\n"
                        f"  Harga: <b>{item['price']}</b>\n\n")

    send_telegram_message(message)

    # Save new data
    save_new_data({item["kode"]: item for item in new_data})

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "flask":
        app.run(host="0.0.0.0", port=5000)
    else:
        main()
