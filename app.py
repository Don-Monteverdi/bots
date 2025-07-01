
from flask import Flask, request, jsonify, send_from_directory
import os
import re
import fitz  # PyMuPDF
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def is_date(val):
    return re.match(r"\d{2}\.\d{2}\.\d{2}", val)

def is_amount(val):
    return re.match(r"[-+]?\d[\d\s]*[.,]?\d*", val)

def normalize_amount(val):
    val = val.strip().replace(" ", "")
    if "," in val:
        val = val.replace(".", "").replace(",", ".")
    else:
        val = val.replace(".", "")
    try:
        return float(val)
    except:
        return 0.0
    val = val.replace(" ", "").replace(",", ".")
    try:
        return float(val)
    except:
        return 0.0

def parse_pdf(path):
    doc = fitz.open(path)
    text = "\n".join(page.get_text() for page in doc)
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    transactions = []

    opening_balance = None
    closing_balance = None
    i = 0
    while i < len(lines) - 2:
        if is_date(lines[i]) and is_date(lines[i+1]) and is_amount(lines[i+2]):
            date = "20" + lines[i].replace(".", "-")
            valuedate = "20" + lines[i+1].replace(".", "-")
            amount = normalize_amount(lines[i+2])
            j = i + 3
            desc_lines = []
            while j < len(lines) and not is_date(lines[j]):
                desc_lines.append(lines[j])
                j += 1
            desc = " ".join(desc_lines)
            transactions.append({
                "Date": date,
                "ValueDate": valuedate,
                "Amount": amount,
                "Type": "Credit" if amount > 0 else "Debit",
                "Description": desc.strip()
            })
            i = j
        else:
            i += 1

    summary = {
        "Total Credits": round(sum(t["Amount"] for t in transactions if t["Amount"] > 0), 2),
        "Total Debits": round(sum(t["Amount"] for t in transactions if t["Amount"] < 0), 2),
        "Opening Balance": opening_balance,
        "Closing Balance": None
    }

    for line in lines:
        if "NYITÓ EGYENLEG" in line:
            match = re.search(r"[-+]?\d[\d\s]*[.,]?\d*", line)
            if match:
                summary["Opening Balance"] = normalize_amount(match.group(0))
        if "ZÁRÓ EGYENLEG" in line:
            match = re.search(r"[-+]?\d[\d\s]*[.,]?\d*", line)
            if match:
                summary["Closing Balance"] = normalize_amount(match.group(0))

    return {
        "Bank": "OTP",
        **summary,
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
