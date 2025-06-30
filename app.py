from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import fitz  # PyMuPDF
import re

app = Flask(__name__, static_url_path='', static_folder='.')
CORS(app)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/parse', methods=['POST'])
def parse_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files['file']
    if not file.filename.endswith('.pdf'):
        return jsonify({"error": "Invalid file type"}), 400

    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()

    lines = [line.strip() for line in text.split("\n") if line.strip()]
    full_text = " ".join(lines)

    transactions = []
    debit_total = 0.0
    credit_total = 0.0

    transaction_pattern = re.compile(r"(\d{2}\.\d{2}\.\d{2}) (\d{2}\.\d{2}\.\d{2}) ([+-]?[\d\.]+) (.+?)(?=\d{2}\.\d{2}\.\d{2}|$)")
    for match in transaction_pattern.finditer(full_text):
        date, value_date, amount, desc = match.groups()
        amount_val = float(amount.replace('.', '').replace(',', '.')) if ',' in amount else float(amount.replace(',', '.'))
        tx_type = "Credit" if amount_val > 0 else "Debit"
        transactions.append({
            "Date": f"20{date}",
            "ValueDate": f"20{value_date}",
            "Amount": f"{amount_val:.3f}",
            "Type": tx_type,
            "Description": desc.strip()
        })
        if tx_type == "Credit":
            credit_total += amount_val
        else:
            debit_total += amount_val

    summary = {
        "Opening Balance": None,
        "Closing Balance": None,
        "Total Credits": f"{credit_total:.3f}" if credit_total else None,
        "Total Debits": f"{debit_total:.3f}" if debit_total else None
    }

    return jsonify({
        "Summary": summary,
        "Transactions": transactions
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)