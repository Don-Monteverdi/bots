
# 📄 Bank Statement Parser (Erste + OTP)

A Flask-based API to parse Hungarian bank statements from **Erste** and **OTP** into structured JSON.

## ✅ Supported Features
- Detects and parses Erste and OTP statements automatically
- Outputs opening/closing balances, totals, and full transaction list
- Web frontend included
- Ready to deploy on Render

---

## 🔧 Local Usage

```bash
pip install -r requirements.txt
python app.py
```

Then open [http://localhost:5000/index.html](http://localhost:5000/index.html)

---

## 🛠 Render Deployment

1. Upload this repo to GitHub
2. Create a new Render **Web Service**
3. Set:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python app.py`

---

## 📤 API

### `POST /parse`
Form-data with `file` (PDF)

**Response:**
```json
{
  "Bank": "OTP",
  "Opening Balance": 78583.0,
  "Closing Balance": 59521.0,
  "Total Credits": 501996.0,
  "Total Debits": -521058.0,
  "Transactions": [...]
}
```
