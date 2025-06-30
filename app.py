
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import fitz  # PyMuPDF
import re

app = Flask(__name__)
CORS(app)

@app.route("/")
def serve_frontend():
    return send_from_directory(directory='.', path='index.html')

@app.route("/parse", methods=["POST"])
def parse_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    file_path = "/tmp/temp.pdf"
    file.save(file_path)

    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()

    transactions = []
    summary = {
        "Opening Balance": None,
        "Closing Balance": None,
        "Total Credits": None,
        "Total Debits": None
    }

    return jsonify({
        "Summary": summary,
        "Transactions": transactions
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
