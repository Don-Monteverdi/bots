
from flask import Flask, request, jsonify, send_file
from PyPDF2 import PdfReader
import re

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

    # Try to find bounds of the transaction section
    try:
        start = next(i for i, line in enumerate(lines) if "NYITÓ EGYENLEG" in line) - 2
        end = next(i for i, line in enumerate(lines) if "ZÁRÓ EGYENLEG" in line) + 2
        section = lines[start:end+1]
    except:
        section = lines

    def extract(label):
        match = re.search(rf"{label}:?\s*(-?\d+[.,]?\d*)", text)
        return match.group(1).replace(",", ".") if match else None

    summary = {
        "Opening Balance": extract("NYITÓ EGYENLEG"),
        "Closing Balance": extract("ZÁRÓ EGYENLEG"),
        "Total Credits": extract("JÓVÁÍRÁSOK ÖSSZESEN"),
        "Total Debits": extract("TERHELÉSEK ÖSSZESEN")
    }

    transactions = []
    i = 0
    while i < len(section):
        line = section[i]
        if re.match(r"\d{2}\.\d{2}\.\d{2}\s+\d{2}\.\d{2}\.\d{2}\s+[-\d]", line):
            parts = re.split(r"(\d{2}\.\d{2}\.\d{2})\s+(\d{2}\.\d{2}\.\d{2})\s+(-?\d+[.,]?\d*)", line, maxsplit=1)
            if len(parts) >= 4:
                date, value_date, amount = parts[1], parts[2], parts[3].replace(",", ".")
                description_lines = [parts[4].strip()] if len(parts) > 4 else []
                i += 1
                # Collect following lines that do not start with a date
                while i < len(section) and not re.match(r"\d{2}\.\d{2}\.\d{2}", section[i]):
                    description_lines.append(section[i].strip())
                    i += 1
                transactions.append({
                    "Date": "20" + date.replace(".", "-"),
                    "ValueDate": "20" + value_date.replace(".", "-"),
                    "Amount": float(amount),
                    "Description": " ".join(description_lines),
                    "Type": "Credit" if float(amount) > 0 else "Debit"
                })
            else:
                i += 1
        else:
            i += 1

    return jsonify({
        "Summary": summary,
        "Transactions": transactions
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
