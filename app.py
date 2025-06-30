
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

    # More robust summary parsing logic
    try:
        # Use regular expressions to extract numeric values after the keywords
        opening = re.search(r"NYITÓ EGYENLEG\s+(-?[\d.]+)", text)
        closing = re.search(r"ZÁRÓ EGYENLEG\s+(-?[\d.]+)", text)
        credits = re.search(r"JÓVÁÍRÁSOK ÖSSZESEN:\s*(-?[\d.]+)", text)
        debits = re.search(r"TERHELÉSEK ÖSSZESEN:\s*(-?[\d.]+)", text)

        summary["Opening Balance"] = opening.group(1) if opening else None
        summary["Closing Balance"] = closing.group(1) if closing else None
        summary["Total Credits"] = credits.group(1) if credits else None
        summary["Total Debits"] = debits.group(1) if debits else None
    except:
        pass

    return summary

def extract_transactions(text):
    # Transactions logic preserved from the last working version
    pattern = r"(\d{4}\.\d{2}\.\d{2}).*?(\d{4}\.\d{2}\.\d{2})?\s+([+-]?[\d.]+)\s+(.*?)\n"
    matches = re.findall(pattern, text, re.DOTALL)

    transactions = []
    for match in matches:
        date, val_date, amount, desc = match
        if amount.strip() == "":
            continue
        transactions.append({
            "Date": date,
            "ValueDate": val_date if val_date else date,
            "Amount": amount.strip(),
            "Description": desc.strip(),
            "Type": "Credit" if "-" not in amount.strip() else "Debit"
        })
    return transactions

@app.route("/")
def index():
    return "✅ OTP Parser API is running. Use POST /parse to upload a PDF."

@app.route("/parse", methods=["POST"])
def parse_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    pdf = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in pdf:
        text += page.get_text()

    summary = extract_summary(text)
    transactions = extract_transactions(text)

    return jsonify({"Summary": summary, "Transactions": transactions})
