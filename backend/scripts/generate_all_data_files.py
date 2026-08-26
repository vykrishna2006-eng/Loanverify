"""
Generate all organizer-specified data files:
- loan_tape.csv
- servicer_update.csv
- document_manifest.csv
- validation_rules.json
- users.json
- expected_exception_sample.csv
"""
import csv, json, random, os
from datetime import date, timedelta

random.seed(42)
OUT = os.path.join(os.path.dirname(__file__), "../../data")
os.makedirs(OUT, exist_ok=True)

US_STATES = ["AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA",
             "KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
             "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT",
             "VA","WA","WV","WI","WY","DC"]

def rdate(y1=2010, y2=2023):
    s = date(y1,1,1); e = date(y2,12,31)
    return s + timedelta(days=random.randint(0,(e-s).days))

def fmt(d): return d.strftime("%Y-%m-%d") if d else ""

SERVICERS = ["Wells Fargo","JPMorgan Chase","Bank of America","Quicken Loans","US Bank","PNC Bank","Freedom Mortgage"]
PAY_STATUS = ["CURRENT","DELINQUENT","DEFAULT","PAID_OFF","CLOSED"]
DOC_STATUS = ["COMPLETE","INCOMPLETE","MISSING"]
LOAN_TYPES = ["CONVENTIONAL","FHA","VA","JUMBO"]
CREDIT_GRADES = ["A","B","C","D","A+","B+"]
INCOME_BANDS = ["LOW","MEDIUM","HIGH","VERY_HIGH"]

# ── loan_tape.csv ─────────────────────────────────────────────────────────────
rows = []
for i in range(1, 2001):
    lid = f"L{i:06d}"
    orig = rdate()
    try:
        mat = orig.replace(year=orig.year + random.choice([15,20,30]))
    except ValueError:
        mat = orig.replace(year=orig.year + 20, day=28)
    principal = random.randint(50000, 750000)
    balance = round(principal * random.uniform(0.3, 0.95), 2)
    status = random.choices(PAY_STATUS, weights=[60,15,5,15,5])[0]
    dpd = 0
    if status == "DELINQUENT": dpd = random.randint(30,89)
    elif status == "DEFAULT": dpd = random.randint(90,365)
    elif status in ("PAID_OFF","CLOSED"): balance = 0.0
    last_pay = orig + timedelta(days=random.randint(30, 365*11))

    # Inject errors ~7% of rows
    err = random.random()
    if err < 0.005: lid = ""                              # missing loan_id
    elif err < 0.010: principal = -abs(principal)         # negative principal
    elif err < 0.018: balance = principal * 1.25          # balance > principal
    elif err < 0.023: status = "PENDING"                  # invalid status
    elif err < 0.030: dpd = 45; status = "CURRENT"        # status/DPD conflict
    elif err < 0.035: status = "CLOSED"; balance = 15000  # closed with balance
    elif err < 0.042: last_pay = date.today() - timedelta(days=220)  # stale

    rows.append({
        "loan_id": lid, "borrower_id": f"B{random.randint(1000,9999):04d}",
        "loan_type": random.choice(LOAN_TYPES),
        "origination_date": fmt(orig), "maturity_date": fmt(mat),
        "original_principal": f"{principal:.2f}", "current_balance": f"{balance:.2f}",
        "interest_rate": str(round(random.uniform(2.5,8.5),3)),
        "term_months": str(random.choice([180,240,360])),
        "borrower_state": random.choice(US_STATES) if random.random() > 0.03 else "XX",
        "loan_purpose": random.choice(["PURCHASE","REFINANCE","CASH_OUT"]),
        "credit_grade": random.choice(CREDIT_GRADES),
        "employment_length": str(random.randint(0,30)),
        "income_band": random.choice(INCOME_BANDS),
        "payment_status": status, "days_past_due": str(dpd),
        "servicer_name": random.choice(SERVICERS),
        "last_payment_date": fmt(last_pay),
        "last_updated_at": fmt(last_pay + timedelta(days=random.randint(0,30))),
        "document_status": random.choices(DOC_STATUS, weights=[75,15,10])[0],
        "source_system": random.choice(["ORIGINATION_SYS","SERVICING_SYS","MANUAL_ENTRY"]),
    })

with open(f"{OUT}/loan_tape.csv","w",newline="",encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(f"✅ loan_tape.csv — {len(rows)} rows")

# ── servicer_update.csv ───────────────────────────────────────────────────────
svc_rows = []
loan_ids = [r["loan_id"] for r in rows if r["loan_id"]]
for lid in random.sample(loan_ids, min(600, len(loan_ids))):
    orig_row = next((r for r in rows if r["loan_id"]==lid), None)
    if not orig_row: continue
    try:
        orig_bal = float(orig_row["current_balance"])
        new_bal = round(orig_bal * random.uniform(0.80, 0.99), 2)
    except ValueError:
        new_bal = 0.0
    svc_rows.append({
        "loan_id": lid,
        "current_balance": f"{new_bal:.2f}",
        "payment_status": orig_row["payment_status"],
        "days_past_due": orig_row["days_past_due"],
        "last_payment_date": fmt(date.today() - timedelta(days=random.randint(5,60))),
        "last_updated_at": fmt(date.today() - timedelta(days=random.randint(1,30))),
        "servicer_name": random.choice(SERVICERS),
        "document_status": random.choices(DOC_STATUS, weights=[80,12,8])[0],
        "source_system": "SERVICER_PORTAL",
    })

with open(f"{OUT}/servicer_update.csv","w",newline="",encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(svc_rows[0].keys())); w.writeheader(); w.writerows(svc_rows)
print(f"✅ servicer_update.csv — {len(svc_rows)} rows")

# ── document_manifest.csv ─────────────────────────────────────────────────────
doc_rows = []
for lid in loan_ids:
    doc_rows.append({
        "loan_id": lid,
        "note_available": random.choice(["Y","Y","Y","N"]),
        "deed_available": random.choice(["Y","Y","N","N"]),
        "title_available": random.choice(["Y","Y","Y","N"]),
        "appraisal_available": random.choice(["Y","N","N"]),
        "insurance_available": random.choice(["Y","Y","N"]),
        "document_status": random.choices(DOC_STATUS, weights=[75,15,10])[0],
        "last_verified_at": fmt(date.today() - timedelta(days=random.randint(1,365))),
    })

with open(f"{OUT}/document_manifest.csv","w",newline="",encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(doc_rows[0].keys())); w.writeheader(); w.writerows(doc_rows)
print(f"✅ document_manifest.csv — {len(doc_rows)} rows")

# ── validation_rules.json ─────────────────────────────────────────────────────
rules = [
    {"rule_id":"R001","name":"Required Fields","description":"loan_id, original_principal, origination_date must be present","category":"REQUIRED_FIELD","severity":"HIGH","is_active":True,"rule_expression":"loan_id IS NOT NULL AND original_principal IS NOT NULL AND origination_date IS NOT NULL"},
    {"rule_id":"R002","name":"Valid Origination Date","description":"Origination date must be a valid past date","category":"DATE","severity":"HIGH","is_active":True,"rule_expression":"origination_date <= TODAY()"},
    {"rule_id":"R003","name":"Valid Maturity Date","description":"Maturity date must be after origination date","category":"DATE","severity":"HIGH","is_active":True,"rule_expression":"maturity_date > origination_date"},
    {"rule_id":"R004","name":"No Negative Principal","description":"Original principal must be greater than zero","category":"FINANCIAL","severity":"HIGH","is_active":True,"rule_expression":"original_principal > 0"},
    {"rule_id":"R005","name":"Valid Interest Rate","description":"Interest rate must be between 0.5 and 50 percent","category":"FINANCIAL","severity":"HIGH","is_active":True,"rule_expression":"0.5 <= interest_rate <= 50"},
    {"rule_id":"R006","name":"Balance Does Not Exceed Principal","description":"Current balance must not exceed original principal","category":"FINANCIAL","severity":"HIGH","is_active":True,"rule_expression":"current_balance <= original_principal"},
    {"rule_id":"R007","name":"No Invalid Balance","description":"Current balance must be >= 0","category":"FINANCIAL","severity":"HIGH","is_active":True,"rule_expression":"current_balance >= 0"},
    {"rule_id":"R008","name":"Valid Payment Status","description":"Payment status must be a recognized value","category":"STATUS","severity":"MEDIUM","is_active":True,"rule_expression":"payment_status IN (CURRENT,DELINQUENT,DEFAULT,PAID_OFF,CLOSED,FORECLOSURE)"},
    {"rule_id":"R009","name":"Duplicate Loan Detection","description":"Loan ID must be unique within the upload","category":"DUPLICATE","severity":"HIGH","is_active":True,"rule_expression":"COUNT(loan_id) = 1"},
    {"rule_id":"R010","name":"Document Status Present","description":"Document status must not be missing","category":"DOCUMENT","severity":"MEDIUM","is_active":True,"rule_expression":"document_status IS NOT NULL"},
    {"rule_id":"R011","name":"Stale Record Detection","description":"Records not updated in over 180 days","category":"DATE","severity":"LOW","is_active":True,"rule_expression":"last_payment_date >= TODAY() - 180"},
    {"rule_id":"R012","name":"Valid US State","description":"Property state must be a valid 2-letter US state code","category":"GEOGRAPHIC","severity":"MEDIUM","is_active":True,"rule_expression":"borrower_state IN (valid_states)"},
    {"rule_id":"R013","name":"Closed Account Positive Balance","description":"Closed loans must have zero balance","category":"STATUS","severity":"HIGH","is_active":True,"rule_expression":"NOT (payment_status=CLOSED AND current_balance > 0)"},
    {"rule_id":"R014","name":"Payment Status vs DPD Conflict","description":"CURRENT status loans must have 0 days past due","category":"STATUS","severity":"HIGH","is_active":True,"rule_expression":"NOT (payment_status=CURRENT AND days_past_due > 0)"},
    {"rule_id":"R015","name":"Suspicious Borrower Repetition","description":"Same borrower on more than 5 loans in same upload","category":"DUPLICATE","severity":"MEDIUM","is_active":True,"rule_expression":"COUNT(borrower_id) <= 5"},
]
with open(f"{OUT}/validation_rules.json","w") as f:
    json.dump(rules, f, indent=2)
print(f"✅ validation_rules.json — {len(rules)} rules")

# ── users.json ────────────────────────────────────────────────────────────────
users = [
    {"id":"a0000001-0000-0000-0000-000000000001","email":"operator@loanverify.ai","full_name":"Alex Operator","role":"DATA_OPERATOR","password":"password123"},
    {"id":"a0000002-0000-0000-0000-000000000002","email":"reviewer@loanverify.ai","full_name":"Riley Reviewer","role":"REVIEWER","password":"password123"},
    {"id":"a0000003-0000-0000-0000-000000000003","email":"consumer@loanverify.ai","full_name":"Casey Consumer","role":"DATA_CONSUMER","password":"password123"},
]
with open(f"{OUT}/users.json","w") as f:
    json.dump(users, f, indent=2)
print(f"✅ users.json — {len(users)} users")

# ── expected_exception_sample.csv ────────────────────────────────────────────
exc_samples = [
    {"loan_id":"L000010","rule_id":"R006","exception_type":"BALANCE_GREATER_THAN_PRINCIPAL","severity":"HIGH","field":"current_balance","actual":"937500.00","expected":"<= 750000.00","message":"Balance exceeds original principal"},
    {"loan_id":"L000020","rule_id":"R004","exception_type":"INVALID_PRINCIPAL","severity":"HIGH","field":"original_principal","actual":"-150000.00","expected":"> 0","message":"Negative principal balance"},
    {"loan_id":"L000030","rule_id":"R008","exception_type":"INVALID_PAYMENT_STATUS","severity":"MEDIUM","field":"payment_status","actual":"PENDING","expected":"CURRENT|DELINQUENT|DEFAULT|PAID_OFF|CLOSED","message":"Unrecognised payment status"},
    {"loan_id":"L000040","rule_id":"R014","exception_type":"STATUS_DPD_CONFLICT","severity":"HIGH","field":"days_past_due","actual":"CURRENT, DPD=45","expected":"CURRENT requires DPD=0","message":"Status CURRENT but 45 days past due"},
    {"loan_id":"L000050","rule_id":"R013","exception_type":"CLOSED_WITH_POSITIVE_BALANCE","severity":"HIGH","field":"current_balance","actual":"15000.00","expected":"0 (loan is CLOSED)","message":"Closed loan has positive balance"},
    {"loan_id":"L000060","rule_id":"R011","exception_type":"STALE_RECORD","severity":"LOW","field":"last_payment_date","actual":"2023-12-01","expected":">= 180 days ago threshold","message":"Record not updated in over 180 days"},
    {"loan_id":"L000070","rule_id":"R001","exception_type":"MISSING_REQUIRED_FIELDS","severity":"HIGH","field":"loan_id","actual":"NULL","expected":"NOT NULL","message":"Missing loan_id"},
    {"loan_id":"L000080","rule_id":"R012","exception_type":"INVALID_STATE","severity":"MEDIUM","field":"borrower_state","actual":"XX","expected":"Valid 2-letter US state","message":"Invalid state code XX"},
]
with open(f"{OUT}/expected_exception_sample.csv","w",newline="",encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(exc_samples[0].keys())); w.writeheader(); w.writerows(exc_samples)
print(f"✅ expected_exception_sample.csv — {len(exc_samples)} samples")

print("\nAll data files generated in /data/")
