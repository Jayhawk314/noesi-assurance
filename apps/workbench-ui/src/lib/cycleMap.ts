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
    { role: "Vouchers", label: "Vouchers / invoices", x: 312, y: 140 },
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
      id: "gl-control", from: "GL", to: "AP_control_balance",
      points: [[488, 395], [600, 395]], labelAt: [544, 395],
      procedures: ["ap.subledger_gl_balance_tie"],
    },
  ],
};

export const CYCLE_MAPS: CycleMap[] = [PAYABLES];

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
