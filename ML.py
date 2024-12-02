from decouple import config
import os
import requests
import json
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_file
import pandas as pd
from datetime import datetime
import logging
import time

# Logging setup
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

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

# Function to send messages to Telegram with retry
def send_telegram_message(message, retries=3):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    for attempt in range(retries):
        try:
            response = requests.post(url, data=payload)
            if response.status_code == 200:
                return
            logging.error(f"Retry {attempt + 1}/{retries} failed: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error during Telegram message send: {e}")
        time.sleep(2)
    logging.error("Failed to send Telegram message after retries.")

# Function to send files to Telegram with retry
def send_telegram_file(file_path, caption, retries=3):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
    for attempt in range(retries):
        try:
            with open(file_path, "rb") as file:
                files = {"document": file}
                data = {"chat_id": TELEGRAM_CHAT_ID, "caption": caption}
                response = requests.post(url, data=data, files=files)
                if response.status_code == 200:
                    return
                logging.error(f"Retry {attempt + 1}/{retries} failed: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error during Telegram file send: {e}")
        time.sleep(2)
    logging.error("Failed to send Telegram file after retries.")

# Function to fetch data
def fetch_code_data(codes):
    data = []
    for code in codes:
        url = f"{BASE_URL}?member_code={MEMBER_CODE}&signature={SIGNATURE}&kode={code}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                json_data = response.json()
                if "data" in json_data and len(json_data["data"]) > 0:
                    produk_data = json_data["data"][0]
                    nama_produk = produk_data.get("nama_produk", "N/A")
                    price = produk_data.get("price", "N/A")
                    data.append({"kode": code, "nama_produk": nama_produk, "price": price})
                else:
                    logging.warning(f"No data for code {code}")
            else:
                logging.error(f"Error fetching data for code {code}: {response.status_code}")
                data.append({"kode": code, "nama_produk": "Error", "price": "Error"})
        except Exception as e:
            logging.error(f"Exception during fetch for code {code}: {e}")
            data.append({"kode": code, "nama_produk": "Error", "price": "Error"})
    return data

# Function to read old data
def read_old_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    else:
        with open(DATA_FILE, "w") as file:
            json.dump({}, file)
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
    try:
        logging.debug("Endpoint /export_xlsx diakses.")
        
        # Mendapatkan kode dari parameter query
        codes = request.args.get('codes', '').split(',')
        logging.debug(f"Codes yang diterima: {codes}")
        
        if not codes:
            logging.error("Tidak ada kode yang diberikan.")
            return jsonify({"error": "No codes provided"}), 400

        # Fetch data
        logging.debug("Mulai mengambil data dari API.")
        new_data = fetch_code_data(codes)
        logging.debug(f"Data yang diambil: {new_data}")

        # Read old data
        logging.debug("Membaca data lama.")
        old_data = read_old_data()
        logging.debug(f"Data lama: {old_data}")

        # Detect price changes
        logging.debug("Mendeteksi perubahan harga.")
        changed, _ = detect_price_change(new_data, old_data)
        logging.debug(f"Data dengan perubahan harga: {changed}")

        # Kirim notifikasi Telegram hanya jika ada perubahan
        if changed:
            message = "<b>Perubahan Harga Terdeteksi:</b>\n"
            for item in changed:
                message += (f"- Kode: <b>{item['kode']}</b>\n"
                            f"  Nama: {item['nama_produk']}\n"
                            f"  Harga Lama: <s>{item['price_lama']}</s>\n"
                            f"  Harga Baru: <b>{item['price_baru']}</b>\n\n")
            logging.debug("Mengirim pesan ke Telegram.")
            send_telegram_message(message)

            # Save Excel file dan kirim ke Telegram
            logging.debug("Menyimpan data ke file Excel.")
            excel_file = f"Mobile_Legends_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            df = pd.DataFrame(new_data)
            df.to_excel(excel_file, index=False)
            logging.debug(f"File Excel disimpan: {excel_file}")

            # Kirim file Excel ke Telegram
            logging.debug("Mengirim file Excel ke Telegram.")
            caption = "File Excel berhasil diekspor dan berisi data terbaru."
            send_telegram_file(excel_file, caption)
        else:
            logging.info("Tidak ada perubahan harga, file Excel tidak dikirim.")

        # Save new data
        logging.debug("Menyimpan data baru ke file JSON.")
        save_new_data({item["kode"]: item for item in new_data})

        return jsonify({"message": "Proses selesai, periksa Telegram jika ada perubahan harga."})

    except Exception as e:
        error_message = f"Error dalam proses: {e}"
        logging.error(error_message, exc_info=True)
        send_telegram_message(error_message)
        return jsonify({"error": error_message}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
