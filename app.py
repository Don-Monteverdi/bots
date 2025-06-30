from flask import Flask, request, jsonify
from flask_cors import CORS
import fitz  # PyMuPDF
import re
import os

app = Flask(__name__)
CORS(app)

def extract_text_from_pdf(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def parse_otp_statement(text):
    lines = text.splitlines()
    start_idx = None
    end_idx = None

    for i, line in enumerate(lines):
        if "NYITÓ EGYENLEG" in line.upper() and start_idx is None:
            start_idx = max(0, i - 2)
        if "ZÁRÓ EGYENLEG" in line.upper():
            end_idx = min(len(lines), i + 3)

    if start_idx is None or end_idx is None:
        return {"Summary": {}, "Transactions": []}

    relevant_lines = lines[start_idx:end_idx]
    content = "\n".join(relevant_lines)

    summary = {
        "Opening Balance": None,
        "Closing Balance": None,
        "Total Credits": None,
        "Total Debits": None
    }

    transactions = []
    transaction_pattern = re.compile(r"(\d{4}\.\d{2}\.\d{2})\s+(\d{4}\.\d{2}\.\d{2})?\s+(-?\d+[.,]?\d{0,3})\s+(.*)")

    for line in relevant_lines:
        upper = line.upper()
        if "NYITÓ EGYENLEG" in upper:
            match = re.search(r"(-?\d+[.,]\d{3})", line)
            if match:
                summary["Opening Balance"] = match.group(1).replace(",", ".")
        elif "ZÁRÓ EGYENLEG" in upper:
            match = re.search(r"(-?\d+[.,]\d{3})", line)
            if match:
                summary["Closing Balance"] = match.group(1).replace(",", ".")
        elif "JÓVÁÍRÁSOK ÖSSZESEN" in upper:
            match = re.search(r"(-?\d+[.,]\d{3})", line)
            if match:
                summary["Total Credits"] = match.group(1).replace(",", ".")
        elif "TERHELÉSEK ÖSSZESEN" in upper:
            match = re.search(r"(-?\d+[.,]\d{3})", line)
            if match:
                summary["Total Debits"] = match.group(1).replace(",", ".")

        match = transaction_pattern.match(line)
        if match:
            date, value_date, amount, description = match.groups()
            amount = amount.replace(",", ".")
            tx_type = "Credit" if not amount.startswith("-") else "Debit"
            transactions.append({
                "Date": date,
                "ValueDate": value_date or date,
                "Amount": f"{float(amount):.3f}",
                "Description": description.strip(),
                "Type": tx_type
            })

    return {"Summary": summary, "Transactions": transactions}

@app.route("/", methods=["GET"])
def index():
    return "✅ OTP Parser API is running. Use POST /parse to upload a PDF."

@app.route("/parse", methods=["POST"])
def parse():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files["file"]
    parsed_text = extract_text_from_pdf(file)
    result = parse_otp_statement(parsed_text)
    return jsonify(result)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
