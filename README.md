# 📄 Bank Statement Parser API 

This is a simple Flask-based API that parses Hungarian bank statements (PDFs from Erste) and extracts:

- Opening and Closing Balances
- Total Credits and Debits
- All Transactions (Date, Value Date, Amount, Description)

## 🚀 Deployment (on Render)

### 1. Files Included
- `app.py` — Main Flask server
- `requirements.txt` — Python dependencies
- `index.html` — Test frontend (simple upload form)

### 2. Render Setup
1. Create a new **Web Service** on [Render.com](https://render.com)
2. Upload these files to your repo or zip folder
3. Set Render settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
4. Deploy and test!

---

## 🧪 Local Test

To test locally:

```bash
pip install -r requirements.txt
python app.py
```

Then open `http://localhost:5000/index.html` in your browser.

---

## 📤 API Usage

### `POST /parse`

**Body:**
- Form-data with `file`: PDF file

**Response:**
```json
{
  "Opening Balance": -440.0,
  "Closing Balance": 78583.0,
  "Total Credits": 974822.0,
  "Total Debits": -895799.0,
  "Transactions": [
    {
      "Date": "25.03.13",
      "ValueDate": "25.03.13",
      "Amount": -280000.0,
      "Type": "Debit",
      "Description": "KÉSZPÉNZFELVÉT ATM-BŐL ..."
    },
    ...
  ]
}
```

---

## ✅ Author
Built with ❤️ using `Flask + PyPDF2` for robust parsing of Hungarian financial documents.
