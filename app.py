
from flask import Flask, request, jsonify
from flask_cors import CORS
import fitz  # PyMuPDF
import re

app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    return "✅ OTP Parser API is running. Use POST /parse to upload a PDF."

@app.route("/parse", methods=["POST"])
def parse_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = "\n".join(page.get_text() for page in doc)

    opening_match = re.search(r"(\d{2}\.\d{2}\.\d{2})\s+-?\d+[.,]\d+\nNYITÓ EGYENLEG", text)
    opening_balance = None
    if opening_match:
        line = opening_match.group(0)
        try:
            opening_balance = re.findall(r"(-?\d+[.,]\d+)", line)[0]
        except:
            opening_balance = None

    closing_match = re.search(r"ZÁRÓ EGYENLEG\s*-?\d+[.,]\d+", text)
    closing_balance = None
    if closing_match:
        try:
            closing_balance = re.findall(r"(-?\d+[.,]\d+)", closing_match.group(0))[0]
        except:
            closing_balance = None

    # Keep placeholder logic for transaction parsing here...
    summary = {
        "Opening Balance": opening_balance,
        "Closing Balance": closing_balance,
        "Total Credits": None,
        "Total Debits": None,
    }

    return jsonify({"Summary": summary, "Transactions": []})
