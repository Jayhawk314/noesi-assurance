# QuickBooks exports still needed (1 Oct 2026)

Four open items wait on real exports from the QuickBooks test company ("xx",
the one behind `tests/fixtures/quickbooks/kestrel_qbo/`). James makes them:
an agent must not sign in for him. Save every file into
`tests/fixtures/quickbooks/kestrel_qbo/` with the name given, then tell the
agent "the exports are in"; each item below says what the agent then builds.

Menu names are from memory of QuickBooks Online and may differ slightly on
screen. Only the reconciliation path was used before (30 Sep handoff).

## 1. Bank reconciliation (roadmap C2, list item 10) — most important

1. Accounting → Reconcile → choose **10100 Checking - First Prairie**.
2. History by account → the 06/30/2026 reconciliation → **View report**.
3. Print → **Save as PDF** → `reconciliation_report.pdf`.

The agent then builds a recipe that reads the PDF's text (statement ending
balance, cleared and uncleared checks and deposits), foots it, and tests it
against `reconciliation_report_screen.txt`, which was copied from the screen
on 30 Sep. Kestrel's Cash module then loads its reconciliations raw instead
of prepared by hand.

## 2. Numbered accounts and sub-accounts (review L6)

1. Settings (gear) → Account and settings → Advanced → Chart of accounts →
   turn on **Enable account numbers** (and "Show account numbers").
2. Chart of accounts → New: an expense account **60000 Utilities**, then a
   second, **60100 Gas**, marked "Is sub-account" of 60000.
3. Enter one expense dated in June 2026 to 60100 Gas.
4. Export to Excel: **Trial Balance** as of 06/30/2026 → `trial_balance_numbered.xlsx`;
   **Journal** for April–June 2026 → `journal_numbered.xlsx`.

The agent then checks how QuickBooks prints a sub-account's name (for
example "60000 Utilities:60100 Gas") and fixes `account_key` to read it,
with a test on these files. Today a sub-account would be refused as a
duplicate account: loud, but blocking.

## 3. Inventory categories and A/R sub-customers (list item 12)

1. Settings → All lists → **Product categories** → new category **Tires**;
   edit the item **Gravel Tire 700x40** and put it in Tires.
2. Export **Inventory Valuation Summary** as of 06/30/2026 →
   `inventory_valuation_categories.xlsx`.
3. Sales → Customers → New customer **Big Sky Pedal Co. - Shop 2**, marked
   "Is a sub-customer" of Big Sky Pedal Co.; one invoice to it dated June 2026.
4. Export **A/R Aging Summary** as of 06/30/2026 → `ar_aging_subcustomers.xlsx`.

The agent then teaches both recipes the grouped layout (category or parent
customer, its rows, its "Total for" row, each footed), instead of refusing
it.

## 4. Bills linked to purchase orders and payments (list item 11)

The last two finish-line lines (PO overrun on Summit Tire PO 1021; the
unrecorded liability on check 4433) need a report that shows which purchase
order a bill came from, and which bills a payment paid. **Not known yet
which QuickBooks report carries those links.** To find out:

1. Create a purchase order to any vendor, then a bill **from** that PO
   (Expenses → the PO → Copy to bill), then pay the bill with a check.
2. Export each of these to Excel, whatever they contain:
   **Open Purchase Order Detail**, **Purchases by Vendor Detail**,
   **Bill Payment List**, **Transaction List by Vendor**, and
   **Transaction Detail by Account** (Customize → add any "linked
   transaction" or "PO number" column offered).
3. Save them as `po_link_<report name>.xlsx`.

The agent then reports which file, if any, carries the link. If none does,
the PO overrun stays a limitation the Workbench states (it already does),
and the finish line is reworded as "not testable from QuickBooks exports",
which needs your OK.

## B3 limit (list item 13)

Account movements still need the trial balance's prior column. Nothing to
export: it works whenever both years' Trial Balance exports are loaded
through **Build the trial balance**.
