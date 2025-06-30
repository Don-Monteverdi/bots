
from flask import Flask, request, jsonify
from flask_cors import CORS
import fitz  # PyMuPDF
import re
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return '✅ OTP Parser API is running. Use POST /parse to upload a PDF.'

@app.route('/parse', methods=['POST'])
def parse_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if not file or not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Invalid file type'}), 400

    text = ''
    try:
        with fitz.open(stream=file.read(), filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
    except Exception as e:
        return jsonify({'error': f'Failed to read PDF: {str(e)}'}), 500

    lines = text.split('
')
    transactions = []
    summary = {
        "Opening Balance": None,
        "Closing Balance": None,
        "Total Credits": None,
        "Total Debits": None
    }

    for line in lines:
        if "NYITÓ EGYENLEG" in line:
            match = re.search(r"-?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{3})?", line)
            if match:
                summary["Opening Balance"] = match.group(0).replace(",", ".")
        elif "ZÁRÓ EGYENLEG" in line:
            match = re.search(r"-?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{3})?", line)
            if match:
                summary["Closing Balance"] = match.group(0).replace(",", ".")
        elif "JÓVÁÍRÁSOK ÖSSZESEN" in line:
            match = re.search(r"-?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{3})?", line)
            if match:
                summary["Total Credits"] = match.group(0).replace(",", ".")
        elif "TERHELÉSEK ÖSSZESEN" in line:
            match = re.search(r"-?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{3})?", line)
            if match:
                summary["Total Debits"] = match.group(0).replace(",", ".")

    transaction_regex = re.compile(
        r"(\d{4}\.\d{2}\.\d{2}).*?(\d{4}\.\d{2}\.\d{2})?[^\d-]*?([-−]?[\d.]+).*?(?=\d{4}\.\d{2}\.\d{2}|$)",
        re.DOTALL
    )
    matches = transaction_regex.finditer(text)

    for match in matches:
        date = match.group(1).replace('.', '-')
        value_date = match.group(2).replace('.', '-') if match.group(2) else date
        amount = match.group(3).replace(",", ".").replace("−", "-")
        type_ = "Credit" if not amount.startswith("-") else "Debit"
        desc_start = match.end()
        desc_end = text.find(match.group(1), desc_start)
        description = text[desc_start:desc_end].strip() if desc_end != -1 else text[desc_start:].strip()

        transactions.append({
            "Date": date,
            "ValueDate": value_date,
            "Amount": amount,
            "Type": type_,
            "Description": description
        })

    return jsonify({"Summary": summary, "Transactions": transactions})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
