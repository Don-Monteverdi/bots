from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import fitz  # PyMuPDF
import os

app = Flask(__name__, static_folder='.')
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

    pdf = fitz.open(stream=file.read(), filetype='pdf')
    text = ''
    for page in pdf:
        text += page.get_text()

    return jsonify({
        "Summary": {
            "Opening Balance": "1000.00",
            "Closing Balance": "1500.00",
            "Total Credits": "700.00",
            "Total Debits": "200.00"
        },
        "Transactions": [
            {
                "Date": "2025-03-01",
                "ValueDate": "2025-03-01",
                "Description": "Sample Transaction 1",
                "Amount": "100.00",
                "Type": "Credit"
            }
        ]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
