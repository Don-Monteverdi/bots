
from flask import Flask, request, jsonify, render_template_string
import fitz  # PyMuPDF
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

    doc = fitz.open(filepath)
    text = "\n".join(page.get_text() for page in doc)
    lines = text.splitlines()

    def parse_amount(val):
        try:
            return float(val.replace(".", "").replace(",", "."))
        except:
            return None

    transactions = []
    opening_balance = closing_balance = total_credits = total_debits = None
    start_found = end_found = False
    start_index = end_index = 0

    for i, line in enumerate(lines):
        if "NYITÓ EGYENLEG" in line.upper() and not start_found:
            opening_match = re.search(r"(\d[\d\.]*,\d{2})", line)
            if opening_match:
                opening_balance = parse_amount(opening_match.group(1))
            start_found = True
            start_index = max(0, i - 2)
        elif "ZÁRÓ EGYENLEG" in line.upper() and not end_found:
            closing_match = re.search(r"(\d[\d\.]*,\d{2})", line)
            if closing_match:
                closing_balance = parse_amount(closing_match.group(1))
            end_found = True
            end_index = min(len(lines), i + 8)
        elif "JÓVÁÍRÁSOK ÖSSZESEN" in line.upper():
            match = re.search(r"(\d[\d\.]*,\d{2})", line)
            if match:
                total_credits = parse_amount(match.group(1))
        elif "TERHELÉSEK ÖSSZESEN" in line.upper():
            match = re.search(r"(\d[\d\.]*,\d{2})", line)
            if match:
                total_debits = -parse_amount(match.group(1))

    i = start_index
    while i < end_index:
        line = lines[i].strip()
        if re.match(r"\d{2}\.\d{2}\.\d{2}", line):
            date = line
            value_date = None
            amount = None
            description = []
            j = i + 1

            while j < len(lines):
                next_line = lines[j].strip()
                if re.match(r"\d{2}\.\d{2}\.\d{2}", next_line) and value_date is None:
                    value_date = next_line
                elif amount is None:
                    amt = parse_amount(next_line)
                    if amt is not None:
                        amount = amt
                    else:
                        description.append(next_line)
                else:
                    if re.match(r"\d{2}\.\d{2}\.\d{2}", next_line):
                        break
                    description.append(next_line)
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
