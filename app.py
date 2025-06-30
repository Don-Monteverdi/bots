
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os

app = Flask(__name__, static_url_path='', static_folder='.')
CORS(app)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/parse', methods=['POST'])
def parse():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Invalid file type'}), 400

    # Dummy parsed result for now
    return jsonify({
        "Summary": {
            "Opening Balance": "1000",
            "Closing Balance": "1500",
            "Total Credits": "500",
            "Total Debits": "-200"
        },
        "Transactions": [
            {
                "Date": "2025-06-01",
                "Description": "Example Transaction",
                "Amount": "100.00",
                "Type": "Credit",
                "ValueDate": "2025-06-01"
            }
        ]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
