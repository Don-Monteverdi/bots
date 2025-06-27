from flask import Flask, request, jsonify, render_template_string
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

    def parse_amount(value):
        try:
            return float(value.replace(".", "").replace(",", "."))
        except:
            return None

    transactions = []
    opening_balance = closing_balance = total_credits = total_debits = None
    found_start, found_end = False, False
    start_index, end_index = 0, len(lines)

    for i, line in enumerate(lines):
        if "NYITÓ EGYENLEG" in line.upper():
            found_start = True
            start_index = max(0, i - 2)
        elif "ZÁRÓ EGYENLEG" in line.upper():
            found_end = True
            end_index = min(len(lines), i + 3)
        elif "JÓVÁÍRÁSOK ÖSSZESEN" in line.upper():
            match = re.search(r"(\d[\d\.]*,\d{2})", line)
            if match:
                total_credits = parse_amount(match.group(1))
        elif "TERHELÉSEK ÖSSZESEN" in line.upper():
            match = re.search(r"(\d[\d\.]*,\d{2})", line)
            if match:
                total_debits = -parse_amount(match.group(1))

    # Extract balances around the NYITÓ and ZÁRÓ markers
    for i in range(start_index, start_index + 6):
        val = parse_amount(lines[i]) if i < len(lines) else None
        if val is not None:
            opening_balance = val
            break
    for i in range(end_index - 3, end_index + 3):
        val = parse_amount(lines[i]) if i < len(lines) else None
        if val is not None:
            closing_balance = val
            break

    # Extract transactions between start and end
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