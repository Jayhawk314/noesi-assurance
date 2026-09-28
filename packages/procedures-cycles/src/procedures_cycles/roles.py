# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Canonical roles the cycle procedures read, registered into ingestion.

Two kinds of role live here. Client records (trial balance, AR listing,
bank reconciliation, inventory listing and count, check register) come from
the client. Auditor evidence (confirmation replies, inspected liability
dates, attribute-test results, pricing-test results, the summary of
uncorrected misstatements) is produced by the engagement team; its
contracts say so, and the engines evaluate it without inventing any of it.

Registration extends ``procedures_ap.ingest`` in place — the same review,
approval and normalization path, no second ingestion pipeline.
"""

from __future__ import annotations

ROLE_SCHEMAS: dict[str, dict[str, list[str]]] = {
    # ------------------------------------------------ client records
    "Trial_balance": {
        "account": ["account", "account number", "account no", "acct", "gl account"],
        "description": ["description", "account name", "account description", "name"],
        "balance": ["balance", "current balance", "unadjusted balance", "amount",
                    "current year", "cy balance"],
        "prior_balance": ["prior balance", "prior year", "prior year balance",
                          "py balance", "comparative balance"],
        "side": ["side", "dr cr", "drcr", "debit credit", "normal balance"],
        "line": ["line", "fs line", "statement line", "classification", "category",
                 "grouping"],
    },
    "AR_listing": {
        "customer_number": ["customer number", "customer no", "customer id",
                            "account number", "customer"],
        "customer_name": ["customer name", "name"],
        "balance": ["balance", "amount", "total", "balance due", "amount due"],
        "current": ["current", "0 30", "030"],
        "days_31_60": ["31 60", "3160"],
        "days_61_90": ["61 90", "6190"],
        "days_over_90": ["over 90", "91", "91 120", "90"],
    },
    "Bank_reconciliation": {
        "account": ["account", "bank account", "cash account"],
        "item_type": ["item type", "type", "item", "line type"],
        "reference": ["reference", "check number", "check no", "ref", "number"],
        "amount": ["amount", "value"],
        "item_date": ["item date", "date", "check date", "deposit date"],
    },
    "Cutoff_statement": {
        "account": ["account", "bank account"],
        "reference": ["reference", "check number", "check no", "ref"],
        "item_type": ["item type", "type"],
        "amount": ["amount", "value"],
        "cleared_date": ["cleared date", "date cleared", "bank date", "date"],
    },
    "Transfers": {
        "transfer_id": ["transfer id", "check number", "check no", "reference", "id"],
        "from_account": ["from account", "disbursing account", "from"],
        "to_account": ["to account", "receiving account", "to"],
        "amount": ["amount", "value"],
        "disbursed_books": ["disbursed books", "disbursing date per books",
                            "date disbursed per books"],
        "disbursed_bank": ["disbursed bank", "disbursing date per bank",
                           "date disbursed per bank"],
        "received_books": ["received books", "receiving date per books",
                           "date received per books"],
        "received_bank": ["received bank", "receiving date per bank",
                          "date received per bank"],
    },
    "Inventory_listing": {
        "stock_number": ["stock number", "stock no", "item number", "item no", "sku",
                         "number"],
        "description": ["description", "manufacturer", "item description"],
        "model": ["model", "model number"],
        "quantity": ["quantity", "qty"],
        "unit_cost": ["unit cost", "cost each", "price"],
        "cost": ["cost", "extended cost", "extension", "amount", "total"],
    },
    "Inventory_count": {
        "stock_number": ["stock number", "stock no", "item number", "item no", "sku",
                         "boat stock number", "number"],
        "description": ["description", "manufacturer", "item description"],
        "model": ["model", "model number"],
        "quantity": ["quantity", "qty", "count"],
    },
    "Sales_invoices": {
        "invoice_number": ["invoice number", "invoice no", "invoice", "num", "number"],
        "invoice_date": ["invoice date", "date", "transaction date"],
        "customer": ["customer", "customer name", "customer number", "name"],
        "amount": ["amount", "invoice amount", "total", "sales amount"],
        "ship_date": ["ship date", "shipping date", "date shipped", "shipped"],
        "shipping_document": ["shipping document", "bill of lading", "bol",
                              "packing slip", "shipper", "shipping number"],
    },
    "Credit_memos": {
        "memo_number": ["memo number", "credit memo number", "credit memo", "num",
                        "number"],
        "memo_date": ["memo date", "credit memo date", "date"],
        "invoice_number": ["invoice number", "invoice no", "invoice", "applied to",
                           "original invoice"],
        "customer": ["customer", "customer name", "name"],
        "amount": ["amount", "credit amount", "total"],
        "reason": ["reason", "memo", "description"],
    },
    "Payroll_register": {
        "employee_id": ["employee id", "employee number", "employee no", "emp id",
                        "employee"],
        "pay_date": ["pay date", "check date", "payment date", "date"],
        "gross": ["gross", "gross pay", "gross wages", "total gross"],
        "tax_withheld": ["tax withheld", "taxes", "total taxes", "withholding",
                         "employee taxes"],
        "deductions": ["deductions", "other deductions", "total deductions"],
        "net": ["net", "net pay", "net amount", "check amount"],
        "hours": ["hours", "total hours", "hours worked"],
        "pay_rate": ["pay rate", "rate", "hourly rate"],
        "check_number": ["check number", "check no", "num", "payment number"],
    },
    "Payroll_master": {
        "employee_id": ["employee id", "employee number", "employee no", "emp id",
                        "employee"],
        "name": ["name", "employee name", "full name"],
        "status": ["status", "employment status"],
        "hire_date": ["hire date", "date hired", "start date"],
        "termination_date": ["termination date", "release date", "date terminated",
                             "end date"],
        "bank_account": ["bank account", "account number", "direct deposit account",
                         "deposit account"],
        "address": ["address", "home address", "street address"],
        "pay_rate": ["pay rate", "rate", "hourly rate", "salary"],
    },
    "Fixed_assets": {
        "asset_id": ["asset id", "asset number", "asset no", "asset tag", "tag number",
                     "asset"],
        "description": ["description", "asset description", "name"],
        "category": ["category", "class", "asset class", "asset type"],
        "acquired_date": ["acquired date", "acquisition date", "date acquired",
                          "in service date", "placed in service", "purchase date"],
        "cost": ["cost", "original cost", "acquisition cost", "basis", "cost basis"],
        "salvage_value": ["salvage value", "salvage", "residual value"],
        "useful_life_years": ["useful life", "life", "life years", "useful life years"],
        "method": ["method", "depreciation method"],
        "depreciation_expense": ["depreciation expense", "current depreciation",
                                 "current year depreciation", "period depreciation"],
        "accumulated_depreciation": ["accumulated depreciation", "accum depreciation",
                                     "accumulated", "ending accumulated depreciation"],
        "disposal_date": ["disposal date", "date disposed", "retired date",
                          "disposed on"],
    },
    "Debt_schedule": {
        "loan_id": ["loan id", "loan", "note", "loan number", "facility", "debt"],
        "lender": ["lender", "bank", "creditor"],
        "beginning_balance": ["beginning balance", "opening balance", "balance beginning",
                              "prior balance"],
        "borrowings": ["borrowings", "advances", "proceeds", "additions", "draws"],
        "repayments": ["repayments", "payments", "principal payments", "principal paid"],
        "ending_balance": ["ending balance", "closing balance", "balance ending",
                           "balance"],
        "interest_rate": ["interest rate", "rate", "annual rate"],
        "interest_expense": ["interest expense", "interest", "interest paid"],
        "current_portion": ["current portion", "due within one year", "current"],
    },
    "Equity_rollforward": {
        "component": ["component", "equity component", "item", "description"],
        "account": ["account", "account number", "accounts", "gl account"],
        "beginning": ["beginning", "beginning balance", "opening balance"],
        "additions": ["additions", "increases", "contributions", "net income"],
        "reductions": ["reductions", "decreases", "distributions", "dividends"],
        "ending": ["ending", "ending balance", "closing balance"],
    },
    "Accrual_schedule": {
        "item": ["item", "description", "name", "vendor", "accrual", "prepaid"],
        "kind": ["kind", "type", "category"],
        "account": ["account", "account number", "gl account"],
        "beginning": ["beginning", "beginning balance", "opening balance"],
        "additions": ["additions", "increases", "accrued", "paid in advance"],
        "reductions": ["reductions", "decreases", "amortization", "amortized",
                       "paid", "reversed"],
        "ending": ["ending", "ending balance", "closing balance", "balance"],
        "total_amount": ["total amount", "contract amount", "policy amount",
                         "total cost", "annual amount"],
        "service_start": ["service start", "period start", "coverage start",
                          "start date", "effective date"],
        "service_end": ["service end", "period end", "coverage end", "end date",
                        "expiration date"],
        "billed_to_date": ["billed to date", "invoiced to date", "billed", "paid to date"],
    },
    "Journal_entries": {
        "entry_id": ["entry id", "entry number", "entry no", "je number", "je id",
                     "journal number", "journal entry", "journal no", "num",
                     "transaction id"],
        "line": ["line", "line number", "line no"],
        "entry_date": ["entry date", "effective date", "transaction date", "je date",
                       "date"],
        "posted_date": ["posted date", "entered date", "created date", "date created",
                        "date entered", "entered on", "created on"],
        "account": ["account", "account number", "account no", "gl account", "acct",
                    "distribution account"],
        "debit": ["debit", "dr"],
        "credit": ["credit", "cr"],
        "amount": ["amount", "signed amount", "net amount"],
        "posted_by": ["posted by", "entered by", "created by", "user", "prepared by"],
        "approved_by": ["approved by", "approver"],
        "description": ["description", "memo", "memo description", "explanation"],
        "source": ["source", "journal type", "transaction type", "type"],
    },
    # ------------------------------------------------ auditor evidence
    "Additions_vouching": {
        "asset_id": ["asset id", "asset number", "asset no", "asset tag", "asset"],
        "vouched_amount": ["vouched amount", "invoice amount", "amount per invoice",
                           "supported amount", "audited amount"],
        "capitalize": ["capitalize", "capitalizable", "capital", "properly capitalized"],
        "document": ["document", "invoice", "support", "reference"],
    },
    "Covenants": {
        "covenant": ["covenant", "measure", "ratio", "name"],
        "numerator_accounts": ["numerator accounts", "numerator", "accounts"],
        "denominator_accounts": ["denominator accounts", "denominator"],
        "operator": ["operator", "direction", "test"],
        "threshold": ["threshold", "limit", "required", "minimum or maximum"],
    },
    "Confirmations": {
        "customer_number": ["customer number", "customer no", "customer id", "customer"],
        "book_value": ["book value", "balance per books", "balance per client",
                       "recorded amount", "book"],
        "confirmed_value": ["confirmed value", "balance per customer", "confirmed amount",
                            "audited value", "confirmed"],
        "client_misstatement": ["client misstatement", "misstatement",
                                "client misstatement over under"],
        "classification": ["classification", "difference type", "reason"],
        "stratum": ["stratum", "group"],
    },
    "Disbursement_inspection": {
        "payment_number": ["payment number", "payment no", "payment", "disbursement"],
        "voucher_number": ["voucher number", "voucher no", "voucher"],
        "liability_date": ["liability date", "receiving date", "service date",
                           "date received"],
        "liability_amount": ["liability amount", "amount owed", "amount"],
        "document": ["document", "document reference", "support"],
        "conclusion": ["conclusion", "result", "outcome"],
    },
    "Attribute_tests": {
        "attribute": ["attribute", "attribute id", "control"],
        "method": ["method", "sampling method"],
        "expected_rate": ["expected rate", "eper", "expected population exception rate"],
        "tolerable_rate": ["tolerable rate", "ter", "tolerable exception rate"],
        "risk": ["risk", "aro", "risk of overreliance", "risk of assessing control risk too low"],
        "planned_size": ["planned size", "planned sample size", "initial sample size"],
        "sample_size": ["sample size", "actual sample size"],
        "deviations": ["deviations", "exceptions", "number of exceptions"],
        "estimated_sampling_risk": ["estimated sampling risk", "sampling risk allowance"],
    },
    "Pricing_tests": {
        "stock_number": ["stock number", "stock no", "item number", "sku"],
        "recorded_cost": ["recorded cost", "recorded amount", "book cost", "per books"],
        "audited_cost": ["audited cost", "vendor invoice", "amount per vendor invoice",
                         "audited amount"],
    },
    "Adjusting_entries": {
        "entry_id": ["entry id", "entry", "aje", "je number", "entry number"],
        "account": ["account", "account number", "acct"],
        "debit": ["debit", "dr"],
        "credit": ["credit", "cr"],
        "description": ["description", "explanation", "memo"],
    },
    "Misstatements": {
        "description": ["description", "description of misstatement", "misstatement"],
        "reference": ["reference", "wp reference", "w p reference", "workpaper"],
        "identified": ["identified", "identified misstatement", "known"],
        "likely": ["likely", "likely aggregate misstatement", "projected"],
        "current_assets": ["current assets"],
        "noncurrent_assets": ["noncurrent assets", "non current assets"],
        "current_liabilities": ["current liabilities"],
        "noncurrent_liabilities": ["noncurrent liabilities", "non current liabilities"],
        "income_before_taxes": ["income before taxes", "pretax income", "ibt"],
    },
    "Performance_materiality": {
        "account": ["account", "account name", "balance"],
        "performance_materiality": ["performance materiality", "tolerable misstatement",
                                    "allocation"],
    },
}

AMOUNT_FIELDS = {"balance", "prior_balance", "book_value", "confirmed_value",
                 "client_misstatement", "liability_amount", "recorded_cost",
                 "audited_cost", "debit", "credit", "identified", "likely",
                 "current_assets", "noncurrent_assets", "current_liabilities",
                 "noncurrent_liabilities", "income_before_taxes",
                 "performance_materiality", "unit_cost", "cost", "current",
                 "days_31_60", "days_61_90", "days_over_90", "gross", "net",
                 "tax_withheld", "deductions", "pay_rate", "salvage_value",
                 "depreciation_expense", "accumulated_depreciation", "vouched_amount",
                 "beginning_balance", "borrowings", "repayments", "ending_balance",
                 "interest_expense", "current_portion", "beginning", "additions",
                 "reductions", "ending", "total_amount", "billed_to_date"}
# Note: "amount" is already an AP amount field; cycle roles reuse it.

DATE_FIELDS = {"item_date", "cleared_date", "disbursed_books", "disbursed_bank",
               "received_books", "received_bank", "liability_date", "entry_date",
               "posted_date", "invoice_date", "ship_date", "memo_date", "pay_date",
               "hire_date", "termination_date", "acquired_date", "disposal_date",
               "service_start", "service_end"}

REQUIRED: dict[str, tuple[str, ...]] = {
    "Trial_balance": ("account",),
    "AR_listing": ("customer_number",),
    "Bank_reconciliation": ("account", "item_type"),
    "Cutoff_statement": ("account",),
    "Transfers": ("transfer_id",),
    "Inventory_listing": ("stock_number",),
    "Inventory_count": ("stock_number",),
    "Sales_invoices": ("invoice_number",),
    "Credit_memos": ("memo_number",),
    "Accrual_schedule": ("item",),
    "Debt_schedule": ("loan_id",),
    "Equity_rollforward": ("component",),
    "Covenants": ("covenant",),
    "Fixed_assets": ("asset_id",),
    "Additions_vouching": ("asset_id",),
    "Payroll_register": ("employee_id",),
    "Payroll_master": ("employee_id",),
    "Journal_entries": ("entry_id", "account"),
    "Confirmations": ("customer_number",),
    "Disbursement_inspection": ("payment_number",),
    "Attribute_tests": ("attribute",),
    "Pricing_tests": ("stock_number",),
    "Adjusting_entries": ("entry_id", "account"),
    "Misstatements": ("description",),
    "Performance_materiality": ("account",),
}

FILENAME_HINTS: dict[str, list[str]] = {
    "Trial_balance": ["trial balance", "tb", "working trial balance"],
    "AR_listing": ["ar listing", "accounts receivable", "receivables", "ar aging", "aging"],
    "Bank_reconciliation": ["bank reconciliation", "bank rec", "reconciliation"],
    "Cutoff_statement": ["cutoff statement", "cutoff bank statement", "cutoff"],
    "Transfers": ["transfers", "interbank transfers", "transfer schedule"],
    "Inventory_listing": ["inventory listing", "final inventory", "inventory"],
    "Inventory_count": ["inventory count", "count sheet", "count sheets", "counts"],
    "Sales_invoices": ["sales invoices", "sales invoice listing", "sales listing",
                       "sales by invoice"],
    "Credit_memos": ["credit memos", "credit memo listing", "credits issued"],
    "Accrual_schedule": ["accruals schedule", "accrual schedule", "prepaids schedule",
                         "prepaid schedule", "accruals and prepaids"],
    "Debt_schedule": ["debt schedule", "notes payable schedule", "loan schedule",
                      "debt rollforward"],
    "Equity_rollforward": ["equity rollforward", "statement of equity",
                           "changes in equity", "equity schedule"],
    "Covenants": ["covenants", "covenant calculations", "loan covenants"],
    "Fixed_assets": ["fixed assets", "fixed asset register", "asset register",
                     "depreciation schedule", "fixed asset listing"],
    "Additions_vouching": ["additions vouching", "fixed asset additions testing",
                           "additions testing"],
    "Payroll_register": ["payroll register", "payroll journal", "payroll summary",
                         "payroll details"],
    "Payroll_master": ["payroll master", "payroll employee list", "employee payroll"],
    # "journal entries" alone stays the GL's hint (payables GL detail).
    "Journal_entries": ["journal entry listing", "je listing", "general journal",
                        "journal report"],
    "Confirmations": ["confirmations", "confirmation results", "confirms"],
    "Disbursement_inspection": ["disbursement inspection", "subsequent disbursements inspection",
                                "unrecorded liabilities"],
    "Attribute_tests": ["attribute tests", "attribute sampling", "tests of controls"],
    "Pricing_tests": ["pricing tests", "price tests", "inventory pricing"],
    "Adjusting_entries": ["adjusting entries", "ajes", "adjusting journal entries"],
    "Misstatements": ["misstatements", "uncorrected misstatements", "sum", "sud"],
    "Performance_materiality": ["performance materiality", "materiality allocation"],
}

_REGISTERED = False


def register_roles() -> None:
    """Add the cycle roles to the shared ingestion tables (idempotent).

    Existing roles are never modified: a name collision is a programming
    error, not something to merge silently.
    """
    global _REGISTERED
    if _REGISTERED:
        return
    from procedures_ap import ingest

    clash = set(ROLE_SCHEMAS) & set(ingest.ROLE_SCHEMAS)
    if clash:
        raise RuntimeError(f"cycle roles collide with existing roles: {sorted(clash)}")
    ingest.ROLE_SCHEMAS.update(ROLE_SCHEMAS)
    ingest._AMOUNT_FIELDS.update(AMOUNT_FIELDS)
    ingest._DATE_FIELDS.update(DATE_FIELDS)
    ingest._REQUIRED.update(REQUIRED)
    ingest.ROLE_FILENAME_HINTS.update(FILENAME_HINTS)
    _REGISTERED = True
