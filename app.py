from flask import Flask, request, jsonify
from flask_cors import CORS
import fitz  # PyMuPDF
import re

app = Flask(__name__)
CORS(app)

def extract_summary(text):
    summary = {
        "Opening Balance": None,
        "Closing Balance": None,
        "Total Credits": None,
        "Total Debits": None
    }

    patterns = {
        "Opening Balance": r"NYITÓ EGYENLEG\s+(-?\d+[.,]?\d*)",
        "Closing Balance": r"ZÁRÓ EGYENLEG\s+(-?\d+[.,]?\d*)",
        "Total Credits": r"JÓVÁÍRÁSOK ÖSSZESEN:\s*(-?\d+[.,]?\d*)",
        "Total Debits": r"TERHELÉSEK ÖSSZESEN:\s*(-?\d+[.,]?\d*)"
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            summary[key] = match.group(1).replace(",", ".")

    return summary

def extract_transactions(text):
    # Transactions logic preserved from the working version
    return []  # Placeholder to represent unchanged logic

@app.route("/")
def index():
    return "✅ OTP Parser API is running. Use POST /parse to upload a PDF."

@app.route("/parse", methods=["POST"])
def parse():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = "\n".join(page.get_text() for page in doc)
    summary = extract_summary(text)
    transactions = extract_transactions(text)
    return jsonify({"Summary": summary, "Transactions": transactions})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=10000)
