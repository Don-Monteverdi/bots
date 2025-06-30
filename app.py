
from flask import Flask, request, jsonify, send_from_directory
import fitz  # PyMuPDF
import re
from flask_cors import CORS

app = Flask(__name__, static_url_path='', static_folder='.')
CORS(app)

@app.route("/")
def index():
    return send_from_directory('.', 'index.html')

@app.route('/parse', methods=['POST'])
def parse_pdf():
    file = request.files['file']
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()

    lines = text.splitlines()
    start_idx, end_idx = 0, len(lines)

    for i, line in enumerate(lines):
        if "NYITÓ EGYENLEG" in line:
            start_idx = max(0, i - 2)
        if "ZÁRÓ EGYENLEG" in line:
            end_idx = min(len(lines), i + 3)

    relevant_lines = lines[start_idx:end_idx]
    joined_lines = "\n".join(relevant_lines)

    def extract_balance(label):
        match = re.search(rf"{label}\s*(-?\d[\d\s]*,\d{{3}})", joined_lines)
        if match:
            return match.group(1).replace(" ", "").replace(",", ".")
        return None

    opening_balance = extract_balance("NYITÓ EGYENLEG")
    closing_balance = extract_balance("ZÁRÓ EGYENLEG")
    total_credits = extract_balance("JÓVÁÍRÁSOK ÖSSZESEN")
    total_debits = extract_balance("TERHELÉSEK ÖSSZESEN")

    transaction_pattern = re.compile(
        r"(\d{4}\.\d{2}\.\d{2})\s+(\d{4}\.\d{2}\.\d{2})?\s+([-\d\s,.]+)\s+(.*)"
    )

    transactions = []
    for line in relevant_lines:
        match = transaction_pattern.match(line)
        if match:
            date, valuedate, amount, desc = match.groups()
            amount_clean = amount.replace(" ", "").replace(".", "").replace(",", ".")
            type_ = "Credit" if not amount_clean.startswith("-") else "Debit"
            transactions.append({
                "Date": date.strip(),
                "ValueDate": valuedate.strip() if valuedate else date.strip(),
                "Amount": f"{float(amount_clean):.3f}",
                "Description": desc.strip(),
                "Type": type_
            })

    summary = {
        "Opening Balance": opening_balance,
        "Closing Balance": closing_balance,
        "Total Credits": total_credits,
        "Total Debits": total_debits
    }

    return jsonify({
        "Summary": summary,
        "Transactions": transactions
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
