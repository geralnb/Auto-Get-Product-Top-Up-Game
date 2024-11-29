from flask import Flask, request, jsonify, send_file
import requests
import pandas as pd

app = Flask(__name__)

# Base URL for the API
BASE_URL = "your_base_url"

# Dummy member code and signature (replace with actual credentials)
MEMBER_CODE = "your_member_code"
SIGNATURE = "your_signature"

# Function to fetch data
def fetch_code_data(codes):
    data = []
    for code in codes:
        url = f"{BASE_URL}?member_code={MEMBER_CODE}&signature={SIGNATURE}&kode={code}"
        response = requests.get(url)

        # Debugging untuk melihat isi respons
        print(f"Response for code {code}: {response.text}")

        if response.status_code == 200:
            json_data = response.json()

            # Pastikan 'data' ada dan tidak kosong
            if "data" in json_data and len(json_data["data"]) > 0:
                produk_data = json_data["data"][0]  # Ambil elemen pertama
                nama_produk = produk_data.get("nama_produk", "N/A")
                price = produk_data.get("price", "N/A")
            else:
                nama_produk = "N/A"
                price = "N/A"

            data.append({"kode": code, "nama_produk": nama_produk, "price": price})
        else:
            data.append({"kode": code, "nama_produk": "Error", "price": "Error"})
    return data


@app.route('/get_codes', methods=['GET'])
def get_codes():
    # Get codes from query parameters, or use default
    codes = request.args.get('codes').split(',')

    # Fetch data for the codes
    data = fetch_code_data(codes)

    return jsonify(data)

@app.route('/export_xlsx', methods=['GET'])
def export_xlsx():
    # Get codes from query parameters, or use default
    codes = request.args.get('codes').split(',')

    # Fetch data for the codes
    data = fetch_code_data(codes)

    # Convert data to a Pandas DataFrame
    df = pd.DataFrame(data)

    # Save to XLSX
    file_path = "codes_export.xlsx"
    df.to_excel(file_path, index=False)

    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
