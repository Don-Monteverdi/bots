
from flask import Flask, request, jsonify, send_file
from PyPDF2 import PdfReader
from datetime import datetime
import re
import os

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return send_file("index.html")

@app.route("/parse", methods=["POST"])
def parse_pdf():
    if 'pdf_file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['pdf_file']
    reader = PdfReader(file)
    text = "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
    lines = text.splitlines()

    try:
        start = next(i for i, line in enumerate(lines) if "NYITÓ EGYENLEG" in line) - 2
        end = next(i for i, line in enumerate(lines) if "ZÁRÓ EGYENLEG" in line) + 2
        section = lines[start:end+1]
    except:
        return jsonify({"error": "Could not locate transaction section"}), 400

    def extract(label):
        match = re.search(rf'(-?\d+(?:\.\d{{1,3}})?)\s*\n?.*{label}', text, re.IGNORECASE)
        return match.group(1) if match else None

    summary = {
        "Opening Balance": extract("NYITO EGYENLEG"),
        "Closing Balance": extract("ZARO EGYENLEG"),
        "Total Credits": extract("JOVAIRASOK OSSZESEN"),
        "Total Debits": extract("TERHELES.*OSSZESEN")
    }

    results = []
    i = 0
    while i < len(section):
        line = section[i].strip().replace(" ", "")
        if re.match(r'\d{2}\.\d{2}\.\d{2}', line):
            try:
                date = datetime.strptime(line, "%y.%m.%d").strftime("%Y-%m-%d")
                i += 1

                value_date = None
                check = section[i].strip().replace(" ", "")
                if re.match(r'\d{2}\.\d{2}\.\d{2}', check):
                    value_date = datetime.strptime(check, "%y.%m.%d").strftime("%Y-%m-%d")
                    i += 1

                amt_str = section[i].strip()
                if not re.match(r'-?\d+(?:\.\d{1,3})?$', amt_str):
                    i += 1
                    continue
                amt = float(amt_str)
                i += 1

                desc = []
                while i < len(section):
                    check = section[i].strip().replace(" ", "")
                    if re.match(r'\d{2}\.\d{2}\.\d{2}', check):
                        break
                    if not re.match(r'-?\d+(?:\.\d{1,3})?$', section[i].strip()):
                        desc.append(section[i].strip())
                    i += 1

                results.append({
                    "Date": date,
                    "ValueDate": value_date,
                    "Amount": amt_str,
                    "AmountFloat": amt,
                    "Description": " ".join(desc),
                    "Type": "Credit" if amt > 0 else "Debit"
                })
            except:
                i += 1
        else:
            i += 1

    return jsonify({
        "Summary": summary,
        "Transactions": results
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
