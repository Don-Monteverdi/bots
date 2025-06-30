from flask import Flask, request, jsonify, send_from_directory
import fitz  # PyMuPDF
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def extract_text_from_first_page(pdf_path):
    doc = fitz.open(pdf_path)
    first_page = doc[0]
    text = first_page.get_text()
    doc.close()
    return text

def parse_transactions(text):
    import re
    lines = text.split('\n')
    transactions = []
    total_debits = 0.0
    total_credits = 0.0

    for line in lines:
        if re.search(r'\d{2}\.\d{2}\.\d{2}', line):
            match = re.search(r'(\d{2}\.\d{2}\.\d{2}).*?([-+]?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2,3}))', line)
            if match:
                date = '20' + match.group(1).replace('.', '-')
                amount = match.group(2).replace('.', '').replace(',', '.')
                amount_val = float(amount)
                desc = line.strip()
                transaction_type = "Credit" if amount_val > 0 else "Debit"
                if transaction_type == "Credit":
                    total_credits += amount_val
                else:
                    total_debits += abs(amount_val)
                transactions.append({
                    "Date": date,
                    "Description": desc,
                    "Amount": str(amount_val),
                    "Type": transaction_type,
                    "ValueDate": date
                })

    return {
        "Summary": {
            "Opening Balance": None,
            "Closing Balance": None,
            "Total Credits": f"{total_credits:.3f}",
            "Total Debits": f"-{total_debits:.3f}"
        },
        "Transactions": transactions
    }

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/parse', methods=['POST'])
def parse():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '' or not file.filename.endswith('.pdf'):
        return jsonify({"error": "Invalid file type"}), 400

    filepath = os.path.join('/tmp', file.filename)
    file.save(filepath)

    try:
        text = extract_text_from_first_page(filepath)
        parsed_data = parse_transactions(text)
        return jsonify(parsed_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)