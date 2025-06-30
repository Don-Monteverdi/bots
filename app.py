from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import pdfplumber
import re

app = Flask(__name__)
CORS(app)

def extract_transactions(text):
    transactions = []
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if re.match(r'\d{2}\.\d{2}\.\d{2}', line):  # Match dates like 25.03.04
            try:
                parts = line.split()
                date = parts[0]
                value_date = parts[1]
                amount_match = re.search(r'(-?\d+[.,]\d+|-?\d+)', line)
                amount = amount_match.group().replace(",", ".") if amount_match else "0"
                trans_type = "Credit" if not amount.startswith("-") else "Debit"
                description = line[line.find(amount) + len(amount):].strip()
                transactions.append({
                    "Date": f"20{date[-2:]}-{date[3:5]}-{date[0:2]}",
                    "ValueDate": f"20{value_date[-2:]}-{value_date[3:5]}-{value_date[0:2]}",
                    "Amount": amount,
                    "Description": description,
                    "Type": trans_type
                })
            except Exception:
                continue
    return transactions

@app.route('/')
def index():
    return "✅ OTP Parser API is running. Use POST /parse to upload a PDF."

@app.route('/parse', methods=['POST'])
def parse_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']

    try:
        with pdfplumber.open(file) as pdf:
            text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())

        transactions = extract_transactions(text)

        total_credits = sum(float(t['Amount']) for t in transactions if t['Type'] == 'Credit')
        total_debits = sum(float(t['Amount']) for t in transactions if t['Type'] == 'Debit')

        summary = {
            "Opening Balance": None,
            "Closing Balance": None,
            "Total Credits": f"{total_credits:.3f}",
            "Total Debits": f"{total_debits:.3f}"
        }

        return jsonify({
            "Summary": summary,
            "Transactions": transactions
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
