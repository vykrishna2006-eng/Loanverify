"""
LoanVerify AI — Sample Dataset Generator
Generates a realistic 10,000-row loan tape CSV with intentional data errors
that exercise all 15 validation rules.

Usage:
    python scripts/generate_dataset.py
    python scripts/generate_dataset.py --rows 10000 --output ../data/loan_tape_10000.csv
    python scripts/generate_dataset.py --rows 3000  --output ../data/servicer_update_3000.csv --source servicer
"""

import argparse
import csv
import random
import os
from datetime import date, timedelta
from decimal import Decimal

# ── Seed for reproducibility ──────────────────────────────────────────────────
random.seed(42)

# ── Reference data ────────────────────────────────────────────────────────────
US_STATES = [
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA",
    "KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT",
    "VA","WA","WV","WI","WY","DC",
]
INVALID_STATES = ["XX", "ZZ", "AB", "QQ", "99"]

LOAN_TYPES    = ["CONVENTIONAL", "FHA", "VA", "JUMBO", "USDA", "ARM", "FIXED"]
LOAN_PURPOSES = ["PURCHASE", "REFINANCE", "CASH_OUT_REFINANCE", "CONSTRUCTION", "HOME_EQUITY"]
DOC_STATUSES  = ["COMPLETE", "INCOMPLETE", "MISSING"]
PAY_STATUSES  = ["CURRENT", "DELINQUENT", "DEFAULT", "PAID_OFF", "CLOSED"]
INVALID_STATUSES = ["PENDING", "UNKNOWN", "N/A", "ACTIVE"]
SERVICERS     = [
    "Wells Fargo Home Mortgage", "JPMorgan Chase Bank", "Bank of America",
    "Quicken Loans", "US Bank", "PNC Bank", "Caliber Home Loans",
    "Freedom Mortgage", "Nationstar Mortgage", "SunTrust Mortgage",
    "Flagstar Bank", "PHH Mortgage", "Citimortgage", "Green Tree Servicing",
]

FIRST_NAMES   = ["James","Mary","John","Patricia","Robert","Jennifer","Michael","Linda","David","Barbara",
                 "William","Susan","Richard","Jessica","Joseph","Sarah","Thomas","Karen","Charles","Lisa"]
LAST_NAMES    = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Wilson","Martinez",
                 "Anderson","Taylor","Thomas","Hernandez","Moore","Jackson","Martin","Lee","Thompson","White"]

def random_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

def random_date(start_year=2010, end_year=2023):
    start = date(start_year, 1, 1)
    end   = date(end_year, 12, 31)
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))

def fmt_date(d):
    return d.strftime("%Y-%m-%d") if d else ""

def fmt_money(v):
    return f"{v:.2f}"


def generate_loan_row(loan_num: int, error_type: str = None, duplicate_loan_id: str = None) -> dict:
    """
    Generate a single loan record. error_type controls which validation rule is triggered.
    """
    loan_id     = duplicate_loan_id or f"L{loan_num:06d}"
    borrower_id = f"B{random.randint(1000, 9999):04d}"
    principal   = random.randint(50_000, 800_000)
    rate        = round(random.uniform(2.5, 8.5), 3)
    orig_date   = random_date(2010, 2022)
    mat_year = orig_date.year + random.choice([10, 15, 20, 30])
    try:
        mat_date = orig_date.replace(year=mat_year)
    except ValueError:
        # Feb 29 in a non-leap year → use Feb 28
        mat_date = orig_date.replace(year=mat_year, day=28)
    last_pay    = orig_date + timedelta(days=random.randint(30, 365 * 11))
    dpd         = 0
    pay_status  = random.choices(PAY_STATUSES, weights=[60, 15, 5, 15, 5])[0]
    balance     = round(principal * random.uniform(0.3, 0.95), 2)
    state       = random.choice(US_STATES)
    doc_status  = random.choices(DOC_STATUSES, weights=[75, 15, 10])[0]

    # Adjust DPD for DELINQUENT/DEFAULT
    if pay_status == "DELINQUENT":
        dpd = random.randint(30, 89)
    elif pay_status == "DEFAULT":
        dpd = random.randint(90, 365)
    elif pay_status in ("PAID_OFF", "CLOSED"):
        balance = 0.0

    row = {
        "loan_id":          loan_id,
        "borrower_id":      borrower_id,
        "borrower_name":    random_name(),
        "co_borrower_name": random_name() if random.random() < 0.3 else "",
        "loan_type":        random.choice(LOAN_TYPES),
        "loan_purpose":     random.choice(LOAN_PURPOSES),
        "property_state":   state,
        "property_zip":     f"{random.randint(10000, 99999):05d}",
        "servicer_name":    random.choice(SERVICERS),
        "original_principal": fmt_money(principal),
        "current_balance":  fmt_money(balance),
        "interest_rate":    str(rate),
        "monthly_payment":  fmt_money(principal * rate / 100 / 12 * 1.1),
        "origination_date": fmt_date(orig_date),
        "maturity_date":    fmt_date(mat_date),
        "last_payment_date": fmt_date(last_pay),
        "next_payment_date": fmt_date(last_pay + timedelta(days=30)),
        "payment_status":   pay_status,
        "days_past_due":    str(dpd),
        "document_status":  doc_status,
        "lien_position":    random.choice(["FIRST", "SECOND"]),
    }

    # ── Inject specific errors based on error_type ────────────────────────
    if error_type == "missing_loan_id":
        row["loan_id"] = ""

    elif error_type == "missing_principal":
        row["original_principal"] = ""
        row["loan_id"] = loan_id  # Keep valid ID

    elif error_type == "negative_principal":
        row["original_principal"] = fmt_money(-abs(principal))

    elif error_type == "balance_exceeds_principal":
        row["original_principal"] = fmt_money(principal)
        row["current_balance"]    = fmt_money(principal * random.uniform(1.05, 1.5))

    elif error_type == "negative_balance":
        row["current_balance"] = fmt_money(-abs(balance))

    elif error_type == "invalid_interest_rate":
        # Use rate expressed as decimal (e.g. 0.065 instead of 6.5)
        row["interest_rate"] = str(round(random.uniform(0.01, 0.09), 4))

    elif error_type == "future_origination_date":
        future = date.today() + timedelta(days=random.randint(30, 365))
        row["origination_date"] = fmt_date(future)

    elif error_type == "maturity_before_origination":
        row["maturity_date"] = fmt_date(orig_date - timedelta(days=random.randint(30, 365)))

    elif error_type == "invalid_payment_status":
        row["payment_status"] = random.choice(INVALID_STATUSES)

    elif error_type == "missing_doc_status":
        row["document_status"] = ""

    elif error_type == "stale_record":
        stale_date = date.today() - timedelta(days=random.randint(200, 800))
        row["last_payment_date"] = fmt_date(stale_date)

    elif error_type == "invalid_state":
        row["property_state"] = random.choice(INVALID_STATES)

    elif error_type == "closed_positive_balance":
        row["payment_status"] = "CLOSED"
        row["current_balance"] = fmt_money(random.randint(1000, 50000))

    elif error_type == "status_dpd_conflict":
        row["payment_status"] = "CURRENT"
        row["days_past_due"]  = str(random.randint(1, 45))

    elif error_type == "missing_origination_date":
        row["origination_date"] = ""

    return row


def generate_dataset(n_rows: int, source: str = "tape") -> list:
    """
    Generate n_rows loan records with realistic error distribution.
    ~7% error rate to match the challenge's 704/10000 example.
    """
    rows = []

    # Error distribution (approximate target: 7% exception rate)
    error_allocation = {
        "missing_principal":         int(n_rows * 0.005),
        "negative_principal":        int(n_rows * 0.004),
        "balance_exceeds_principal": int(n_rows * 0.008),
        "negative_balance":          int(n_rows * 0.003),
        "invalid_interest_rate":     int(n_rows * 0.007),
        "future_origination_date":   int(n_rows * 0.003),
        "maturity_before_origination": int(n_rows * 0.003),
        "invalid_payment_status":    int(n_rows * 0.006),
        "missing_doc_status":        int(n_rows * 0.010),
        "stale_record":              int(n_rows * 0.015),
        "invalid_state":             int(n_rows * 0.005),
        "closed_positive_balance":   int(n_rows * 0.005),
        "status_dpd_conflict":       int(n_rows * 0.007),
        "missing_origination_date":  int(n_rows * 0.003),
    }

    # Build list of error types per row
    error_slots = []
    for err_type, count in error_allocation.items():
        error_slots.extend([err_type] * count)
    random.shuffle(error_slots)

    # Reserve slots for duplicates (~1%)
    n_duplicates   = int(n_rows * 0.010)
    duplicate_ids  = [f"L{random.randint(1, n_rows // 2):06d}" for _ in range(n_duplicates)]
    dup_idx        = set(random.sample(range(n_rows), n_duplicates))

    # Reserve slots for suspicious borrower repetition
    repeat_borrowers = [f"B{i:04d}" for i in range(5)]  # 5 borrowers repeated many times

    error_iter = iter(error_slots)
    dup_iter   = iter(duplicate_ids)

    for i in range(1, n_rows + 1):
        loan_num = i
        error_type    = None
        duplicate_id  = None

        if i in dup_idx:
            duplicate_id = next(dup_iter, None)
        elif error_slots:
            try:
                error_type = next(error_iter)
            except StopIteration:
                pass

        row = generate_loan_row(loan_num, error_type, duplicate_id)

        # Inject borrower repetition for ~50 rows
        if i % 200 == 0 and i < n_rows * 0.25:
            row["borrower_id"] = random.choice(repeat_borrowers)

        rows.append(row)

    return rows


def write_csv(rows: list, output_path: str):
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    fieldnames = list(rows[0].keys())
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"✅ Written {len(rows):,} rows to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate LoanVerify AI sample dataset")
    parser.add_argument("--rows",   type=int, default=10000,                              help="Number of loan records")
    parser.add_argument("--output", type=str, default="../data/loan_tape_10000.csv",       help="Output CSV path")
    parser.add_argument("--source", type=str, default="tape", choices=["tape","servicer"], help="Source type label")
    parser.add_argument("--seed",   type=int, default=42,                                  help="Random seed")
    args = parser.parse_args()

    random.seed(args.seed)

    print(f"Generating {args.rows:,} loan records (source={args.source}, seed={args.seed})…")
    rows = generate_dataset(args.rows, args.source)

    # Print summary
    error_count = sum(
        1 for r in rows if not r["loan_id"] or not r["original_principal"]
        or (r["original_principal"] and float(r["original_principal"].replace(",","") or 0) < 0)
    )
    print(f"  Total rows:      {len(rows):,}")
    print(f"  Estimated errors: {int(len(rows) * 0.07):,}  (~7%)")
    print(f"  Clean rows:      {int(len(rows) * 0.93):,}")

    write_csv(rows, args.output)

    # Generate servicer update (smaller, newer values)
    if args.source == "tape":
        servicer_rows = random.sample(rows, min(3000, len(rows)))
        for r in servicer_rows:
            if r["current_balance"] and r["current_balance"] != "0.00":
                try:
                    new_bal = float(r["current_balance"]) * random.uniform(0.85, 0.99)
                    r["current_balance"] = fmt_money(new_bal)
                except ValueError:
                    pass
        servicer_path = args.output.replace("loan_tape", "servicer_update").replace("10000", "3000")
        write_csv(servicer_rows, servicer_path)


if __name__ == "__main__":
    main()
