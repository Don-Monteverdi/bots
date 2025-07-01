
from flask import Flask, request, jsonify, send_from_directory
import os
import PyPDF2
from werkzeug.utils import secure_filename
from parsers import detect_and_parse

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def extract_text_from_pdf(pdf_file):
    reader = PyPDF2.PdfReader(pdf_file)
    return "\n".join(page.extract_text() or "" for page in reader.pages)

@app.route("/parse", methods=["POST"])
def parse_pdf():
    if "file" not in request.files:
        return jsonify({"error": "Missing file"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    filename = secure_filename(file.filename)
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(path)

    with open(path, "rb") as f:
        try:
            text = extract_text_from_pdf(f)
            result = detect_and_parse(text)
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route("/index.html")
def index():
    return send_from_directory(".", "index.html")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
