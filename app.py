
from flask import Flask, request, jsonify
import fitz  # PyMuPDF
import re

app = Flask(__name__)

def extract_text_from_pdf(file_stream):
    doc = fitz.open(stream=file_stream.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def parse_otp_statement(text):
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    section = []
    started = False

    for i, line in enumerate(lines):
        if "NYITÓ EGYENLEG" in line:
            section = lines[max(0, i-2):]
            started = True
        if started and "ZÁRÓ EGYENLEG" in line:
            section = section[:section.index(line)+3]
            break

    opening = next((l for l in section if "NYITÓ EGYENLEG" in l), None)
    closing = next((l for l in section if "ZÁRÓ EGYENLEG" in l), None)
    total_credits = next((l for l in section if "JÓVÁÍRÁSOK ÖSSZESEN" in l), None)
    total_debits = next((l for l in section if "TERHELÉSEK ÖSSZESEN" in l), None)

    def extract_amount(line):
        m = re.findall(r"-?\d+[.,]?\d{0,3}", line.replace(" ", ""))
        return m[-1] if m else None

    summary = {
        "Opening Balance": extract_amount(opening),
        "Closing Balance": extract_amount(closing),
        "Total Credits": extract_amount(total_credits),
        "Total Debits": extract_amount(total_debits)
    }

    # Extract transactions from lines
    transactions = []
    clean_lines = [l.strip() for l in section if l.strip()]
    i = 0
    while i < len(clean_lines) - 2:
        if re.match(r"\d{2}\.\d{2}\.\d{2}", clean_lines[i]) and            re.match(r"\d{2}\.\d{2}\.\d{2}", clean_lines[i+1]) and            re.match(r"-?\d+([.,]?\d{1,3})?", clean_lines[i+2]):

            date = clean_lines[i]
            value_date = clean_lines[i+1]
            amount = clean_lines[i+2]
            amount_normalized = amount.replace(",", ".")
            desc = []
            i += 3
            while i < len(clean_lines) and not re.match(r"\d{2}\.\d{2}\.\d{2}", clean_lines[i]):
                desc.append(clean_lines[i])
                i += 1

            transactions.append({
                "Date": "20" + date.replace(".", "-"),
                "ValueDate": "20" + value_date.replace(".", "-"),
                "Amount": amount.strip(),
                "Description": " ".join(desc),
                "Type": "Credit" if float(amount_normalized) > 0 else "Debit"
            })
        else:
            i += 1

    return {
        "Summary": summary,
        "Transactions": transactions
    }

@app.route("/", methods=["GET"])
def health():
    return "✅ OTP Parser API is running. Use POST /parse to upload a PDF."

@app.route("/parse", methods=["POST"])
def parse():
    if 'file' not in request.files:
        return jsonify({ "error": "No file uploaded" }), 400

    file = request.files['file']
    text = extract_text_from_pdf(file)
    result = parse_otp_statement(text)
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)
