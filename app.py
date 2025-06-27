from flask import Flask, request, jsonify, render_template_string, send_from_directory
from PyPDF2 import PdfReader
import re
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

HTML_PAGE = """<!DOCTYPE html>
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
</html>"""

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_PAGE)

@app.route("/index.html")
def serve_index():
    return send_from_directory(".", "index.html")

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
    text = "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
    lines = text.splitlines()

    # Initialize
    transactions = []
    opening_balance = closing_balance = total_credits = total_debits = None

    # Match Hungarian format numbers like 1.234.567,89
    def parse_huf(amount_str):
        try:
            return float(amount_str.replace(".", "").replace(",", "."))
        except:
            return None

    # Extract balances
    for i, line in enumerate(lines):
        if "NYITÓ EGYENLEG" in line.upper():
            for j in range(i-3, i+1):
                val = parse_huf(lines[j])
                if val is not None:
                    opening_balance = val
        if "ZÁRÓ EGYENLEG" in line.upper():
            for j in range(i-3, i+1):
                val = parse_huf(lines[j])
                if val is not None:
                    closing_balance = val
        if "JÓVÁÍRÁSOK ÖSSZESEN" in line.upper():
            match = re.search(r"(\d[\d\.]*,\d{2})", line)
            if match:
                total_credits = parse_huf(match.group(1))
        if "TERHELÉSEK ÖSSZESEN" in line.upper():
            match = re.search(r"(\d[\d\.]*,\d{2})", line)
            if match:
                total_debits = -parse_huf(match.group(1))

    # Extract transactions
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if re.match(r"\d{2}\.\d{2}\.\d{2}", line):
            date = line
            value_date = None
            amount = None
            description = []
            j = i + 1

            # Search next 5 lines for value date, amount
            while j < len(lines) and j < i + 10:
                if re.match(r"\d{2}\.\d{2}\.\d{2}", lines[j].strip()) and value_date is None:
                    value_date = lines[j].strip()
                elif amount is None:
                    possible = parse_huf(lines[j].strip())
                    if possible is not None:
                        amount = possible
                else:
                    description.append(lines[j].strip())
                j += 1

            if amount is not None:
                transactions.append({
                    "Date": date,
                    "ValueDate": value_date,
                    "Amount": amount,
                    "Type": "Credit" if amount > 0 else "Debit",
                    "Description": " ".join(description)
                })
            i = j
        else:
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