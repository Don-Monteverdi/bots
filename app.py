from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import fitz  # PyMuPDF
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/parse', methods=['POST'])
def parse_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    file = request.files['file']
    if not file.filename.endswith('.pdf'):
        return jsonify({'error': 'Invalid file type'}), 400

    text = ''
    with fitz.open(stream=file.read(), filetype='pdf') as doc:
        for page in doc:
            text += page.get_text()

    lines = text.split('\n')
    transactions = []
    total_credits = 0
    total_debits = 0

    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = line.split(',')
        if len(parts) >= 5:
            try:
                amount = parts[0].strip()
                date = parts[1].strip()
                value_date = parts[2].strip()
                description = parts[3].strip()
                t_type = parts[4].strip()

                numeric_amount = float(amount.replace('.', '').replace(',', '.'))
                if numeric_amount > 0:
                    total_credits += numeric_amount
                    t_type = 'Credit'
                else:
                    total_debits += abs(numeric_amount)
                    t_type = 'Debit'

                transactions.append({
                    'Amount': amount,
                    'Date': date,
                    'ValueDate': value_date,
                    'Description': description,
                    'Type': t_type
                })
            except Exception:
                continue

    summary = {
        'Opening Balance': None,
        'Closing Balance': None,
        'Total Credits': f"{total_credits:.3f}" if total_credits else None,
        'Total Debits': f"{total_debits:.3f}" if total_debits else None
    }

    return jsonify({'Summary': summary, 'Transactions': transactions})

@app.route('/<path:path>')
def static_proxy(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
