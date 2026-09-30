// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** Declarative flow-map layouts: the money's path through a cycle.
 *
 * A diagram is inherently hand-authored — coverage can tell us what a
 * procedure needs, but not where to draw it. So the geometry lives here as
 * data and the *state* (supplied / missing, executable / blocked) is filled
 * in from the live API. Adding a cycle means adding an entry, not editing
 * the renderer.
 */

export const NODE_W = 176;
export const NODE_H = 62;

export interface MapNode {
  /** Canonical dataset role, as the ingest layer names it. */
  role: string;
  label: string;
  x: number;
  y: number;
  /** Procedures that test this dataset alone, with no counterparty. */
  procedures?: string[];
}

export interface MapEdge {
  id: string;
  from: string;
  to: string;
  /** Polyline in viewBox units; explicit so routing never guesses. */
  points: [number, number][];
  /** Where the status chip sits. */
  labelAt: [number, number];
  /** Procedures that test this link. Empty = structural arrow only. */
  procedures: string[];
}

export interface CycleMap {
  cycle: string;
  title: string;
  caption: string;
  width: number;
  height: number;
  nodes: MapNode[];
  edges: MapEdge[];
}

/** Accounts payable: order → receive → record → pay → clear → post. */
const PAYABLES: CycleMap = {
  cycle: "payables",
  title: "Purchase-to-pay",
  caption:
    "Each box is a set of records you supplied. Each arrow is a procedure "
    + "that tests whether one set agrees with the next.",
  width: 800,
  height: 454,
  nodes: [
    {
      role: "Vendors", label: "Vendors", x: 24, y: 28,
      procedures: ["ap.vendor_relational_twins"],
    },
    { role: "Purchase_orders", label: "Purchase orders", x: 312, y: 28 },
    { role: "Goods_receipts", label: "Goods receipts", x: 600, y: 28 },
    {
      role: "Vouchers", label: "Vouchers / invoices", x: 312, y: 140,
      procedures: ["ap.duplicate_bills"],
    },
    { role: "Direct_payments", label: "Checks with no bill", x: 24, y: 140 },
    { role: "Disbursement_inspection", label: "Payments inspected", x: 24, y: 252 },
    {
      role: "Payments", label: "Payments", x: 312, y: 252,
      procedures: ["ap.segregation_of_duties", "ap.split_payment_review"],
    },
    { role: "Bank", label: "Bank", x: 600, y: 252 },
    { role: "GL", label: "General ledger", x: 312, y: 364 },
    {
      role: "AP_control_balance", label: "AP control balance",
      x: 600, y: 364,
    },
    {
      role: "Value_flows", label: "Value flows", x: 24, y: 364,
      procedures: ["forensic.closed_value_flow"],
    },
  ],
  edges: [
    {
      id: "vendors-po", from: "Vendors", to: "Purchase_orders",
      points: [[200, 59], [312, 59]], labelAt: [256, 59], procedures: [],
    },
    {
      id: "po-vouchers", from: "Purchase_orders", to: "Vouchers",
      points: [[400, 90], [400, 140]], labelAt: [400, 115],
      procedures: ["ap.voucher_po_reference"],
    },
    {
      id: "gr-vouchers", from: "Goods_receipts", to: "Vouchers",
      points: [[688, 90], [688, 171], [488, 171]], labelAt: [600, 171],
      procedures: ["ap.three_way_receipt_match"],
    },
    {
      id: "vouchers-payments", from: "Vouchers", to: "Payments",
      points: [[400, 202], [400, 252]], labelAt: [400, 227],
      procedures: ["ap.payment_voucher_reference", "ap.document_chain"],
    },
    {
      id: "payments-bank", from: "Payments", to: "Bank",
      points: [[488, 283], [600, 283]], labelAt: [544, 283],
      procedures: ["cash.bank_clearing"],
    },
    {
      id: "payments-gl", from: "Payments", to: "GL",
      points: [[400, 314], [400, 364]], labelAt: [400, 339],
      procedures: ["gl.payment_posting"],
    },
    {
      id: "direct-vouchers", from: "Direct_payments", to: "Vouchers",
      points: [[200, 171], [312, 171]], labelAt: [256, 171],
      procedures: ["ap.payments_without_bills"],
    },
    {
      id: "inspection-payments", from: "Disbursement_inspection", to: "Payments",
      points: [[200, 283], [312, 283]], labelAt: [256, 283],
      procedures: ["ap.unrecorded_liabilities_search"],
    },
    {
      id: "gl-control", from: "GL", to: "AP_control_balance",
      points: [[488, 395], [600, 395]], labelAt: [544, 395],
      procedures: ["ap.subledger_gl_balance_tie"],
    },
  ],
};

// ------------------------------------------------------------ the other cycles
// Same grid as purchase-to-pay: columns at x 24 / 312 / 600, rows at y 28 /
// 140 / 252 / 364. Every arrow joins neighbours in one row or one column, so
// arrows never cross a box; grid() computes their points.

const COL = [24, 312, 600];
const ROW = [28, 140, 252, 364];
const CAPTION = "Each box is a set of records you supplied. Each arrow is a procedure "
  + "that tests whether one set agrees with the next; a procedure inside a box tests "
  + "that set alone.";

function at(col: number, row: number) { return { x: COL[col], y: ROW[row] }; }

/** An arrow between two neighbouring boxes of the grid, in either direction. */
function grid(nodes: MapNode[], id: string, from: string, to: string,
              procedures: string[]): MapEdge {
  const a = nodes.find((n) => n.role === from)!, b = nodes.find((n) => n.role === to)!;
  let points: [number, number][];
  if (a.y === b.y) {
    const y = a.y + NODE_H / 2;
    points = a.x < b.x ? [[a.x + NODE_W, y], [b.x, y]] : [[a.x, y], [b.x + NODE_W, y]];
  } else {
    const x = a.x + NODE_W / 2;
    points = a.y < b.y ? [[x, a.y + NODE_H], [x, b.y]] : [[x, a.y], [x, b.y + NODE_H]];
  }
  const labelAt: [number, number] = [(points[0][0] + points[1][0]) / 2,
                                     (points[0][1] + points[1][1]) / 2];
  return { id, from, to, points, labelAt, procedures };
}

function cycle(cycleId: string, title: string, rows: number,
               nodes: MapNode[], edges: [string, string, string[]][]): CycleMap {
  return {
    cycle: cycleId, title, caption: CAPTION, width: 800, height: ROW[rows - 1] + NODE_H + 28,
    nodes, edges: edges.map(([from, to, procs]) => grid(nodes, `${from}-${to}`, from, to, procs)),
  };
}

const TB = "Trial_balance";

const REVENUE = cycle("receivables", "Revenue and receivables", 3, [
  { role: "Sales_invoices", label: "Sales invoices", ...at(0, 0), procedures: ["rev.sales_cutoff"] },
  { role: "Credit_memos", label: "Credit memos", ...at(0, 1) },
  { role: "AR_listing", label: "Receivables listing", ...at(1, 1) },
  { role: "Confirmations", label: "Confirmations", ...at(1, 2) },
  { role: TB, label: "Trial balance", ...at(2, 1) },
], [
  ["Credit_memos", "Sales_invoices", ["rev.credit_memos_after_period_end"]],
  ["AR_listing", TB, ["ar.listing_tie"]],
  ["Confirmations", "AR_listing", ["ar.confirmations_nonstatistical", "ar.confirmations_mus",
                                   "ar.confirmations_difference"]],
]);

const CASH = cycle("cash", "Cash", 2, [
  { role: "Cutoff_statement", label: "Cutoff bank statement", ...at(0, 0) },
  { role: "Bank_reconciliation", label: "Bank reconciliation", ...at(1, 0) },
  { role: "Transfers", label: "Bank transfers", ...at(1, 1) },
], [
  ["Cutoff_statement", "Bank_reconciliation", ["cash.bank_reconciliation"]],
  ["Transfers", "Bank_reconciliation", ["cash.interbank_transfers"]],
]);

const INVENTORY = cycle("inventory", "Inventory", 2, [
  { role: "Inventory_count", label: "Count tags", ...at(0, 0) },
  { role: "Inventory_listing", label: "Inventory listing", ...at(1, 0) },
  { role: "Pricing_tests", label: "Pricing tests", ...at(1, 1) },
], [
  ["Inventory_count", "Inventory_listing", ["inventory.count_listing_trace"]],
  ["Pricing_tests", "Inventory_listing", ["inventory.pricing_projection"]],
]);

const PAYROLL = cycle("payroll", "Payroll", 1, [
  { role: "Payroll_master", label: "Employee master", ...at(0, 0) },
  { role: "Payroll_register", label: "Payroll register", ...at(1, 0) },
  { role: TB, label: "Trial balance", ...at(2, 0) },
], [
  ["Payroll_master", "Payroll_register", ["payroll.register_tests"]],
  ["Payroll_register", TB, ["payroll.register_to_ledger"]],
]);

const LONG_LIVED = cycle("ppe", "Property, debt and equity", 3, [
  { role: "Additions_vouching", label: "Additions vouched", ...at(0, 0) },
  { role: "Fixed_assets", label: "Fixed asset register", ...at(1, 0),
    procedures: ["ppe.depreciation_recompute"] },
  { role: TB, label: "Trial balance", ...at(1, 1) },
  { role: "Debt_schedule", label: "Debt schedule", ...at(0, 1) },
  { role: "Covenants", label: "Loan covenants", ...at(2, 1) },
  { role: "Equity_rollforward", label: "Equity rollforward", ...at(1, 2),
    procedures: ["equity.rollforward"] },
], [
  ["Additions_vouching", "Fixed_assets", ["ppe.additions_vouching"]],
  ["Fixed_assets", TB, ["ppe.rollforward"]],
  ["Debt_schedule", TB, ["debt.rollforward_and_interest"]],
  ["Covenants", TB, ["debt.covenants"]],
]);

const CLOSE = cycle("completion", "Journal, planning and completion", 4, [
  { role: "Journal_entries", label: "Journal entries", ...at(0, 1),
    procedures: ["je.journal_entry_testing", "completion.subsequent_events"] },
  { role: TB, label: "Trial balance", ...at(1, 1),
    procedures: ["fs.trial_balance_analytics", "completion.going_concern_indicators"] },
  { role: "Adjusting_entries", label: "Adjusting entries", ...at(2, 1) },
  { role: "Performance_materiality", label: "PM allocations", ...at(1, 0),
    procedures: ["planning.performance_materiality"] },
  { role: "Attribute_tests", label: "Control tests", ...at(0, 0),
    procedures: ["controls.attribute_evaluation"] },
  { role: "Accrual_schedule", label: "Accruals and prepaids", ...at(0, 2),
    procedures: ["accruals.rollforward", "accruals.recompute"] },
  { role: "Estimates", label: "Prior-year estimates", ...at(1, 2),
    procedures: ["estimates.retrospective_review"] },
  { role: "Related_parties", label: "Related parties", ...at(2, 2),
    procedures: ["related_parties.matching"] },
  { role: "Misstatements", label: "Misstatements", ...at(0, 3),
    procedures: ["completion.uncorrected_misstatements"] },
  { role: "Representations", label: "Representation letter", ...at(1, 3),
    procedures: ["completion.representation_letter"] },
], [
  ["Journal_entries", TB, ["je.population_completeness"]],
  ["Adjusting_entries", TB, ["fs.adjusted_trial_balance"]],
]);

export const CYCLE_MAPS: CycleMap[] = [PAYABLES, REVENUE, CASH, INVENTORY, PAYROLL, LONG_LIVED, CLOSE];

/** Every procedure the maps account for — the rest are listed separately. */
export function mappedProcedureIds(): Set<string> {
  const ids = new Set<string>();
  for (const map of CYCLE_MAPS) {
    for (const node of map.nodes) {
      for (const id of node.procedures ?? []) ids.add(id);
    }
    for (const edge of map.edges) {
      for (const id of edge.procedures) ids.add(id);
    }
  }
  return ids;
}
