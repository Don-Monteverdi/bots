from flask import Flask, request, jsonify, render_template_string
from PyPDF2 import PdfReader
import re
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Bank Statement Parser</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 2em; background: #f7f7f7; }
        h1 { color: #333; }
        form { margin-bottom: 2em; }
        pre { background: #fff; border: 1px solid #ccc; padding: 1em; max-height: 500px; overflow: auto; }
        button { padding: 0.5em 1em; background: #007bff; color: white; border: none; cursor: pointer; }
    </style>
</head>
<body>
    <h1>📄 Upload Bank Statement (PDF)</h1>
    <form id="uploadForm" enctype="multipart/form-data">
        <input type="file" name="file" id="fileInput" accept=".pdf" required />
        <button type="submit">Parse PDF</button>
    </form>
    <pre id="result">Awaiting upload...</pre>

    <script>
        const form = document.getElementById("uploadForm");
        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            const fileInput = document.getElementById("fileInput");
            const file = fileInput.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append("file", file);

            const response = await fetch("/parse", {
                method: "POST",
                body: formData
            });

            const result = document.getElementById("result");
            if (response.ok) {
                const data = await response.json();
                result.textContent = JSON.stringify(data, null, 2);
            } else {
                result.textContent = "❌ Error parsing file.";
            }
        });
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_PAGE)

@app.route("/parse", methods=["POST"])
def parse_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join("/tmp", filename)
    file.save(filepath)

    reader = PdfReader(filepath)
    full_text = "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
    lines = full_text.splitlines()

    # Balances
    opening_balance = closing_balance = None
    for i, line in enumerate(lines):
        if "NYITÓ EGYENLEG" in line.upper() and i >= 1:
            try:
                opening_balance = float(lines[i - 1].replace(".", "").replace(",", "."))
            except:
                pass
        if "ZÁRÓ EGYENLEG" in line.upper() and i >= 1:
            try:
                closing_balance = float(lines[i - 1].replace(".", "").replace(",", "."))
            except:
                pass

    # Totals
    total_credits = total_debits = None
    for line in lines:
        if "JÓVÁÍRÁSOK ÖSSZESEN" in line and "TERHELÉSEK ÖSSZESEN" in line:
            credit_match = re.search(r"JÓVÁÍRÁSOK ÖSSZESEN:\s*(-?\d[\d\.]+)", line)
            debit_match = re.search(r"TERHELÉSEK ÖSSZESEN:\s*(-?\d[\d\.]+)", line)
            if credit_match:
                total_credits = float(credit_match.group(1).replace(".", ""))
            if debit_match:
                total_debits = float(debit_match.group(1).replace(".", ""))

    # Transactions
    transactions = []
    i = 0
    while i < len(lines) - 3:
        date_line = lines[i].strip()
        value_date_line = lines[i + 2].strip()
        amount_line = lines[i + 3].strip()
        if re.match(r"\d{2}\.\d{2}\.\d{2}", date_line) and re.match(r"\d{2}\.\d{2}\.\d{2}", value_date_line):
            try:
                amount = float(amount_line.replace(".", "").replace(",", "."))
                type_ = "Credit" if amount > 0 else "Debit"
                description_lines = []
                j = i + 4
                while j < len(lines) and not re.match(r"\d{2}\.\d{2}\.\d{2}", lines[j].strip()):
                    description_lines.append(lines[j].strip())
                    j += 1
                transactions.append({
                    "Date": date_line,
                    "ValueDate": value_date_line,
                    "Amount": amount,
                    "Type": type_,
                    "Description": " ".join(description_lines)
                })
                i = j - 1
            except:
                pass
        i += 1

    return jsonify({
        "Opening Balance": opening_balance,
        "Closing Balance": closing_balance,
        "Total Credits": total_credits,
        "Total Debits": total_debits,
        "Transactions": transactions
    })

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)