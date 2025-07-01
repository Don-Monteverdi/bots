
from flask import Flask, request, jsonify, send_from_directory
import os
import fitz  # PyMuPDF
import re
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def extract_number(text):
    match = re.search(r"[-+]?\d[\d\s]*[.,]\d{2}", text)
    if match:
        return float(match.group(0).replace(" ", "").replace(",", "."))
    return 0.0

def parse_pdf(file_path):
    doc = fitz.open(file_path)
    raw_text = ""
    for page in doc:
        raw_text += page.get_text()

    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]

    # === Transaction grouping ===
    tx_blocks = []
    buffer = ""
    date_line_regex = re.compile(r"^\d{2}\.\d{2}\.\d{2}\s+\d{2}\.\d{2}\.\d{2}")

    for line in lines:
        if date_line_regex.match(line):
            if buffer:
                tx_blocks.append(buffer.strip())
            buffer = line
        else:
            buffer += " " + line
    if buffer:
        tx_blocks.append(buffer.strip())

    # === Extract each transaction ===
    transaction_pattern = re.compile(
        r"(?P<date>\d{2}\.\d{2}\.\d{2})\s+(?P<valuedate>\d{2}\.\d{2}\.\d{2})\s+(?P<amount>[-+]?[\d\s]*[.,]\d{2})\s+(?P<desc>.+)"
    )

    transactions = []
    summary = {}

    for block in tx_blocks:
        match = transaction_pattern.match(block)
        if match:
            raw_amount = match.group("amount").replace(" ", "").replace(",", ".")
            amount = float(raw_amount)
            transactions.append({
                "Date": "20" + match.group("date"),
                "ValueDate": "20" + match.group("valuedate"),
                "Amount": amount,
                "Type": "Credit" if amount >= 0 else "Debit",
                "Description": match.group("desc")
            })

    for line in lines:
        if "JÓVÁÍRÁSOK ÖSSZESEN" in line:
            summary["Total Credits"] = extract_number(line)
        elif "TERHELÉSEK ÖSSZESEN" in line:
            summary["Total Debits"] = extract_number(line)
        elif "NYITÓ EGYENLEG" in line:
            summary["Opening Balance"] = extract_number(line)
        elif "ZÁRÓ EGYENLEG" in line:
            summary["Closing Balance"] = extract_number(line)

    return {
        "Bank": "OTP",
        "Opening Balance": summary.get("Opening Balance", 0.0),
        "Closing Balance": summary.get("Closing Balance", 0.0),
        "Total Credits": summary.get("Total Credits", 0.0),
        "Total Debits": summary.get("Total Debits", 0.0),
        "Transactions": transactions
    }

@app.route("/parse", methods=["POST"])
def parse_route():
    if "file" not in request.files:
        return jsonify({"error": "Missing file"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    filename = secure_filename(file.filename)
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(path)

    try:
        result = parse_pdf(path)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/index.html")
@app.route("/")
def index():
    return send_from_directory(".", "index.html")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
