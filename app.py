import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import fitz  # PyMuPDF
import re

app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    return send_from_directory('.', 'index.html')

@app.route("/parse", methods=["POST"])
def parse_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    doc = fitz.open(stream=file.read(), filetype="pdf")
    full_text = ""
    for page in doc:
        full_text += page.get_text()

    lines = full_text.splitlines()
    lines = [line.strip() for line in lines if line.strip()]
    joined_lines = " ".join(lines)

    transactions = []
    total_credits = 0.0
    total_debits = 0.0

    transaction_pattern = re.compile(
        r"(\d{4}\.\d{2}\.\d{2}).*?(\d{4}\.\d{2}\.\d{2}).*?([-]?\d+[.,]\d{3}|[-]?\d+).*?(?=(\d{4}\.\d{2}\.\d{2})|$)"
    )
    matches = transaction_pattern.finditer(joined_lines)

    for match in matches:
        date, valuedate, amount, _ = match.groups()
        start = match.start()
        end = match.end()
        description = joined_lines[start+len(date)+len(valuedate):end-len(amount)].strip(", ")
        amount_clean = amount.replace(",", ".")
        amount_float = float(amount_clean)
        if amount_float < 0:
            total_debits += amount_float
            tx_type = "Debit"
        else:
            total_credits += amount_float
            tx_type = "Credit"
        transactions.append({
            "Date": date.replace(".", "-"),
            "ValueDate": valuedate.replace(".", "-"),
            "Amount": f"{amount_float:.3f}",
            "Description": description,
            "Type": tx_type
        })

    summary = {
        "Opening Balance": None,
        "Closing Balance": None,
        "Total Credits": f"{total_credits:.3f}" if total_credits else None,
        "Total Debits": f"{total_debits:.3f}" if total_debits else None
    }

    return jsonify({
        "Summary": summary,
        "Transactions": transactions
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)