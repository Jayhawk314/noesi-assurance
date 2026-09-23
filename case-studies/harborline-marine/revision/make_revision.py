# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Build the controller's "corrected" voucher extract from the original.

Deterministic: reads ../data/vouchers.csv, applies three documented edits,
writes vouchers_revised.csv beside this script. Rerunning produces the same
bytes. The edits are the exercise; see ../docs/05-revised-evidence.md.
"""

from __future__ import annotations

import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "data" / "vouchers.csv"
TARGET = HERE / "vouchers_revised.csv"

# 1. The "missing" voucher cited by PAY-2026-0013 turns up. It carries the
#    same vendor, amount, PO and self-approving clerk as VCH-2026-0013:
#    a second invoice for one purchase, not a found document.
ADDED = {"Voucher Number": "VCH-2026-9338", "PO Number": "PO-2026-0013",
         "Vendor Number": "V1006", "Voucher Amount": "21619.99",
         "Voucher Date": "2026-06-21", "Created By": "E227",
         "Approved By": "E227"}

# 2. VCH-2026-0009 "corrected" down to the goods actually received. The
#    payment already went out at the original amount.
# 3. A keying fix on a clean voucher, far below clearly trivial.
AMOUNT_EDITS = {"VCH-2026-0009": "3244.00", "VCH-2026-0030": "26871.69"}


def main() -> None:
    with SOURCE.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames
        rows = list(reader)
    for row in rows:
        if row["Voucher Number"] in AMOUNT_EDITS:
            row["Voucher Amount"] = AMOUNT_EDITS[row["Voucher Number"]]
    rows.append(ADDED)
    with TARGET.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {TARGET.name}: {len(rows)} rows")


if __name__ == "__main__":
    main()
