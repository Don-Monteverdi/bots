
import re
from decimal import Decimal

def parse(text: str):
    lines = text.splitlines()
    transactions = []
    total_credits = Decimal("0.0")
    total_debits = Decimal("0.0")
    opening_balance = None
    closing_balance = None

    transaction_pattern = re.compile(
        r"(\d{2}\.\d{2}\.\d{2})\s+(\d{2}\.\d{2}\.\d{2})\s+([+-]?\d[\d\s]*,\d{2})([A-ZÁÉÍÓÖŐÚÜŰa-z0-9].*)"
    )

    for line in lines:
        line = line.strip()

        if "NYITÓ EGYENLEG" in line and opening_balance is None:
            match = re.search(r"(\d{2}\.\d{2}\.\d{2})\s+([+-]?\d[\d\s]*,\d{2})", line)
            if match:
                opening_balance = to_decimal(match.group(2))

        elif "ZÁRÓ EGYENLEG" in line and closing_balance is None:
            match = re.search(r"(\d{2}\.\d{2}\.\d{2})\s+([+-]?\d[\d\s]*,\d{2})", line)
            if match:
                closing_balance = to_decimal(match.group(2))

        match = transaction_pattern.match(line)
        if match:
            date, value_date, amount_str, description = match.groups()
            amount = to_decimal(amount_str)
            transactions.append({
                "Date": date,
                "ValueDate": value_date,
                "Amount": float(amount),
                "Type": "Credit" if amount > 0 else "Debit",
                "Description": description.strip()
            })
            if amount > 0:
                total_credits += amount
            else:
                total_debits += amount

    return {
        "Bank": "OTP",
        "Opening Balance": float(opening_balance or 0),
        "Closing Balance": float(closing_balance or 0),
        "Total Credits": float(total_credits),
        "Total Debits": float(total_debits),
        "Transactions": transactions
    }

def detect(text: str) -> bool:
    return "OTP BANK NYRT" in text.upper() or "ZÖLD BÁZIS SZÁMLA SZÁMLAKIVONAT" in text.upper()

def to_decimal(amount_str: str) -> Decimal:
    cleaned = amount_str.replace(" ", "").replace(".", "").replace(",", ".")
    return Decimal(cleaned)
