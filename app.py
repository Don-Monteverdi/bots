
from flask import Flask, request, jsonify, send_from_directory
import os
import re
import PyPDF2
from werkzeug.utils import secure_filename
from decimal import Decimal

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def to_decimal(amount_str):
    cleaned = amount_str.replace(" ", "").replace(".", "").replace(",", ".")
    return Decimal(cleaned)

def extract_text_from_pdf(pdf_file):
    reader = PyPDF2.PdfReader(pdf_file)
    return "\n".join(page.extract_text() or "" for page in reader.pages)

def parse_bank_statement(text):
    lines = text.splitlines()
    transactions = []
    total_credits = Decimal("0.0")
    total_debits = Decimal("0.0")
    opening_balance = None
    closing_balance = None

    transaction_pattern = re.compile(
        r"(\d{2}\.\d{2}\.\d{2})\s+(\d{2}\.\d{2}\.\d{2})\s+([+-]?\d[\d\s]*,\d{2})([A-ZÁÉÍÓÖŐÚÜŰa-z].*)"
    )

    bank = "Unknown"
    if "ERSTE BANK" in text.upper():
        bank = "Erste"
    elif "OTP BANK" in text.upper():
        bank = "OTP"

    for line in lines:
        line = line.strip()

        if "NYITÓ EGYENLEG" in line.upper() and opening_balance is None:
            m = re.search(r"(\d{2}\.\d{2}\.\d{2})?\s*([+-]?\d[\d\s]*,\d{2})", line)
            if m: opening_balance = to_decimal(m.group(2))

        elif "ZÁRÓ EGYENLEG" in line.upper() and closing_balance is None:
            m = re.search(r"(\d{2}\.\d{2}\.\d{2})?\s*([+-]?\d[\d\s]*,\d{2})", line)
            if m: closing_balance = to_decimal(m.group(2))

        match = transaction_pattern.match(line)
        if match:
            date, value_date, amount_str, desc = match.groups()
            amount = to_decimal(amount_str)
            transactions.append({
                "Date": date,
                "ValueDate": value_date,
                "Amount": float(amount),
                "Type": "Credit" if amount > 0 else "Debit",
                "Description": desc.strip()
            })
            if amount > 0:
                total_credits += amount
            else:
                total_debits += amount

    return {
        "Bank": bank,
        "Opening Balance": float(opening_balance or 0),
        "Closing Balance": float(closing_balance or 0),
        "Total Credits": float(total_credits),
        "Total Debits": float(total_debits),
        "Transactions": transactions
    }

@app.route("/parse", methods=["POST"])
def parse_pdf():
    if "file" not in request.files:
        return jsonify({"error": "Missing file"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    filename = secure_filename(file.filename)
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(path)

    with open(path, "rb") as f:
        try:
            text = extract_text_from_pdf(f)
            result = parse_bank_statement(text)
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route("/index.html")
def index():
    return send_from_directory(".", "index.html")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
