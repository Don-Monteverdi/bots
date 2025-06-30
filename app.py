from flask import Flask, request, jsonify
from flask_cors import CORS
import fitz  # PyMuPDF
import re

app = Flask(__name__)
CORS(app)

def extract_text_from_pdf(file_stream):
    doc = fitz.open(stream=file_stream.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def parse_bank_statement(text):
    lines = text.splitlines()
    clean_lines = [line.strip() for line in lines if line.strip()]

    start, end = None, None
    for i, line in enumerate(clean_lines):
        if "NYITÓ EGYENLEG" in line and start is None:
            start = max(0, i - 2)
        if "ZÁRÓ EGYENLEG" in line:
            end = min(len(clean_lines), i + 3)
            break

    if start is None or end is None:
        return {"Summary": {}, "Transactions": []}

    section = clean_lines[start:end]
    joined_text = "\n".join(section)

    summary = {
        "Opening Balance": None,
        "Closing Balance": None,
        "Total Credits": None,
        "Total Debits": None,
    }

    def find_amount(label):
        for line in section:
            if label in line:
                parts = re.findall(r"-?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,3})?", line)
                return parts[-1].replace(",", ".") if parts else None
        return None

    summary["Opening Balance"] = find_amount("NYITÓ EGYENLEG")
    summary["Closing Balance"] = find_amount("ZÁRÓ EGYENLEG")
    summary["Total Credits"] = find_amount("JÓVÁÍRÁSOK ÖSSZESEN")
    summary["Total Debits"] = find_amount("TERHELÉSEK ÖSSZESEN")

    transaction_pattern = re.compile(
        r"(\d{4}\.\d{2}\.\d{2})\s+(\d{4}\.\d{2}\.\d{2})?\s+(-?\d+[.,]?\d*)\s+(.*)"
    )

    transactions = []
    for line in clean_lines:
        match = transaction_pattern.match(line)
        if match:
            date, valuedate, amount, desc = match.groups()
            amount = amount.replace(",", ".")
            transactions.append({
                "Date": date,
                "ValueDate": valuedate or date,
                "Amount": f"{float(amount):.3f}" if "." in amount else f"{int(amount):.3f}",
                "Description": desc.strip(),
                "Type": "Credit" if float(amount.replace('.', '').replace(',', '.')) > 0 else "Debit"
            })

    return {"Summary": summary, "Transactions": transactions}

@app.route("/")
def home():
    return "✅ OTP Parser API is running. Use POST /parse to upload a PDF."

@app.route("/parse", methods=["POST"])
def parse():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    text = extract_text_from_pdf(file)
    result = parse_bank_statement(text)
    return jsonify(result)
