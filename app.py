from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import fitz  # PyMuPDF
import os
import re

app = Flask(__name__, static_url_path='', static_folder='.')
CORS(app)

def parse_transactions(text):
    lines = text.split("\n")
    transactions = []
    total_credits = 0.0
    total_debits = 0.0

    for line in lines:
        match = re.search(r"(\d{4}\.\d{2}\.\d{2}).*?([-\d\.]+)", line)
        if match:
            date = match.group(1).replace('.', '-')
            amount_str = match.group(2).replace(".", "").replace(",", ".")
            amount = float(amount_str)
            tx_type = "Credit" if amount > 0 else "Debit"
            if tx_type == "Credit":
                total_credits += amount
            else:
                total_debits += abs(amount)
            transactions.append({
                "Date": date,
                "ValueDate": date,
                "Amount": f"{amount:.3f}",
                "Type": tx_type,
                "Description": line.strip()
            })

    summary = {
        "Opening Balance": None,
        "Closing Balance": None,
        "Total Credits": f"{total_credits:.3f}",
        "Total Debits": f"-{total_debits:.3f}"
    }

    return {"Summary": summary, "Transactions": transactions}

@app.route("/")
def index():
    return send_from_directory('.', 'index.html')

@app.route("/parse", methods=["POST"])
def parse_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '' or not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "Invalid file type"}), 400

    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    parsed_data = parse_transactions(text)
    return jsonify(parsed_data)

if __name__ == "__main__":
    app.run(debug=True, port=5000)