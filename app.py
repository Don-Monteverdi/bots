from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import fitz  # PyMuPDF
import os
import re

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/parse', methods=['POST'])
def parse_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['file']
    if not file.filename.endswith('.pdf'):
        return jsonify({'error': 'Invalid file type'}), 400

    doc = fitz.open(stream=file.read(), filetype='pdf')
    text = ""
    for page in doc:
        text += page.get_text()

    lines = [line.strip() for line in text.split("\n") if line.strip()]

    transaction_pattern = re.compile(
        r"(?P<date>\d{2}\.\d{2}\.\d{2})\s+(?P<valuedate>\d{2}\.\d{2}\.\d{2})\s+(?P<amount>[-]?\d+[.,]?\d*)\s+(?P<desc>.+)"
    )

    transactions = []
    for line in lines:
        match = transaction_pattern.match(line)
        if match:
            amount = match.group("amount").replace(",", ".")
            if amount.endswith(".000"):
                amount = amount[:-4]
            elif amount.endswith(".00"):
                amount = amount[:-3]
            elif amount.endswith(".0"):
                amount = amount[:-2]
            transactions.append({
                "Date": "20" + match.group("date"),
                "ValueDate": "20" + match.group("valuedate"),
                "Amount": amount,
                "Type": "Credit" if not amount.startswith("-") else "Debit",
                "Description": match.group("desc")
            })

    summary = {
        "Opening Balance": None,
        "Closing Balance": None,
        "Total Credits": None,
        "Total Debits": None
    }

    for line in lines:
        if "NYITÓ EGYENLEG" in line:
            summary["Opening Balance"] = ''.join(re.findall(r"[-]?\d+[.,]?\d*", line))
        elif "ZÁRÓ EGYENLEG" in line:
            summary["Closing Balance"] = ''.join(re.findall(r"[-]?\d+[.,]?\d*", line))
        elif "JÓVÁÍRÁSOK ÖSSZESEN" in line:
            summary["Total Credits"] = ''.join(re.findall(r"[-]?\d+[.,]?\d*", line))
        elif "TERHELÉSEK ÖSSZESEN" in line:
            summary["Total Debits"] = ''.join(re.findall(r"[-]?\d+[.,]?\d*", line))

    return jsonify({
        "Summary": summary,
        "Transactions": transactions
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
