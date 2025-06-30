from flask import Flask, request, jsonify, send_from_directory
import fitz  # PyMuPDF
import re
import os

app = Flask(__name__)

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_first_page(file_stream):
    doc = fitz.open(stream=file_stream.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def parse_summary(text):
    summary = {
        "Opening Balance": None,
        "Closing Balance": None,
        "Total Credits": None,
        "Total Debits": None
    }

    opening = re.search(r'NYITÓ EGYENLEG\s+(-?[\d.]+)', text)
    if opening:
        summary["Opening Balance"] = opening.group(1)

    closing = re.search(r'ZÁRÓ EGYENLEG\s+(-?[\d.]+)', text)
    if closing:
        summary["Closing Balance"] = closing.group(1)

    credits = re.search(r'JÓVÁÍRÁSOK ÖSSZESEN:\s+([\d.]+)', text)
    if credits:
        summary["Total Credits"] = credits.group(1)

    debits = re.search(r'TERHELÉSEK ÖSSZESEN:\s+(-?[\d.]+)', text)
    if debits:
        summary["Total Debits"] = debits.group(1)

    return summary

def parse_transactions(text):
    transactions = []
    lines = text.split('\n')
    for line in lines:
        match = re.match(r'(\d{2}\.\d{2}\.\d{2})\s+(\d{2}\.\d{2}\.\d{2})\s+([-\d.]+)\s+(.+)', line)
        if match:
            date, value_date, amount, description = match.groups()
            transactions.append({
                "Date": "20" + date.replace(".", "-"),
                "ValueDate": "20" + value_date.replace(".", "-"),
                "Amount": amount,
                "Description": description.strip(),
                "Type": "Credit" if float(amount.replace(".", "").replace(",", ".")) > 0 else "Debit"
            })
    return transactions

@app.route("/")
def serve_frontend():
    return send_from_directory(".", "index.html")

@app.route("/parse", methods=["POST"])
def parse_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file and allowed_file(file.filename):
        file.stream.seek(0)
        text = extract_text_from_first_page(file.stream)
        summary = parse_summary(text)
        transactions = parse_transactions(text)
        return jsonify({
            "Summary": summary,
            "Transactions": transactions
        })
    return jsonify({"error": "Invalid file type"}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
