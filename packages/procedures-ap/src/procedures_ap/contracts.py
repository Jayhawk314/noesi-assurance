"""The eleven versioned AP procedure contracts, ported from noesi-cpa.

Contract content is frozen against the Phase 0 golden bundle
(`contracts.json`); the shadow test asserts exact equality. Do not edit a
contract in place — methodology changes require a new version.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

SCHEMA_VERSION = "noesis-procedure-coverage-v1"


@dataclass(frozen=True)
class ProcedureContract:
    procedure_id: str
    name: str
    objective: str
    cycle: str
    assertions: tuple[str, ...]
    required_fields: dict[str, tuple[str, ...]]
    required_policies: tuple[str, ...] = ()
    evidence_source: str = "client accounting export"
    policy_version: str = "v1"
    denominator_role: str = "Payments"
    default_selected: bool = True
    limitations: str = ""

    def to_dict(self) -> dict:
        value = asdict(self)
        value["assertions"] = list(self.assertions)
        value["required_fields"] = {
            role: list(fields) for role, fields in self.required_fields.items()
        }
        value["required_policies"] = list(self.required_policies)
        return value


PROCEDURES: tuple[ProcedureContract, ...] = (
    ProcedureContract(
        "ap.payment_voucher_reference", "Payment-to-voucher reference",
        "Determine whether every recorded payment references an observed voucher.",
        "payables", ("occurrence", "accuracy"),
        {"Payments": ("payment_number", "voucher_number"),
         "Vouchers": ("voucher_number",)},
    ),
    ProcedureContract(
        "ap.voucher_po_reference", "Voucher-to-purchase-order reference",
        "Determine whether every voucher expected to have a PO references an observed PO.",
        "payables", ("occurrence", "authorization"),
        {"Vouchers": ("voucher_number", "po_number"),
         "Purchase_orders": ("po_number",)}, denominator_role="Vouchers",
    ),
    ProcedureContract(
        "ap.document_chain", "PO → voucher → payment chain coherence",
        "Test whether the supplied AP document chain closes and amounts/dates cohere.",
        "payables", ("occurrence", "accuracy", "cutoff"),
        {"Purchase_orders": ("po_number", "vendor_number", "po_amount", "po_date"),
         "Vouchers": ("voucher_number", "po_number", "vendor_number",
                      "voucher_amount", "voucher_date"),
         "Payments": ("payment_number", "voucher_number", "vendor_number",
                      "payment_amount", "payment_date")},
        limitations="Document-chain coherence does not authenticate any document.",
    ),
    ProcedureContract(
        "ap.segregation_of_duties", "Payment segregation of duties",
        "Evaluate observed separation between payment creation and approval.",
        "payables", ("authorization",),
        {"Payments": ("payment_number", "created_by", "approved_by")},
        evidence_source="payment workflow or approval log",
        limitations="Field semantics and compensating controls require auditor evaluation.",
    ),
    ProcedureContract(
        "ap.vendor_relational_twins", "Vendor relational-twin screening",
        "Identify vendors with unusually similar observed identities or relationships.",
        "payables", ("occurrence",),
        {"Vendors": ("vendor_number", "vendor_name")}, denominator_role="Vendors",
        limitations="A structural twin is an investigation lead, not proof of duplication or fraud.",
    ),
    ProcedureContract(
        "cash.bank_clearing", "Payment-to-bank clearing",
        "Determine whether recorded payments clear through independent bank evidence.",
        "cash", ("occurrence", "completeness", "accuracy"),
        {"Payments": ("payment_number", "payment_amount", "payment_date"),
         "Bank": ("bank_txn_id", "payment_number", "amount", "bank_date")},
        evidence_source="independent bank or cash-disbursements feed",
    ),
    ProcedureContract(
        "gl.payment_posting", "Payment-to-general-ledger posting",
        "Determine whether payments post to the GL at the expected amount and period.",
        "financial_statements", ("completeness", "accuracy", "cutoff"),
        {"Payments": ("payment_number", "voucher_number", "payment_amount", "payment_date"),
         "GL": ("gl_entry_id", "reference", "amount", "gl_date")},
        evidence_source="general ledger export",
    ),
    ProcedureContract(
        "ap.subledger_gl_balance_tie", "AP subledger-to-GL control-account tie",
        "Reconcile the period-end AP subledger balance to the GL control account.",
        "financial_statements", ("completeness", "accuracy"),
        {"AP_control_balance": ("period_end", "subledger_balance", "gl_balance")},
        evidence_source="period-end AP reconciliation and GL control balance",
    ),
    ProcedureContract(
        "ap.three_way_receipt_match", "PO/invoice/goods-receipt three-way match",
        "Determine whether invoiced and paid goods were ordered and received.",
        "payables", ("occurrence", "accuracy", "authorization"),
        {"Purchase_orders": ("po_number", "po_amount"),
         "Vouchers": ("voucher_number", "po_number", "voucher_amount"),
         "Goods_receipts": ("receipt_number", "po_number", "received_amount")},
        evidence_source="PO, invoice, and receiving records",
    ),
    ProcedureContract(
        "ap.split_payment_review", "Split-payment review",
        "Identify payments clustered below an approved authorization threshold.",
        "payables", ("authorization",),
        {"Payments": ("payment_number", "vendor_number", "payment_amount", "payment_date")},
        required_policies=("split_threshold",),
        limitations="A cluster is advisory and requires business-purpose review.",
    ),
    ProcedureContract(
        "forensic.closed_value_flow", "Closed-population value-flow review",
        "Screen complete directed value flows for coherent round trips.",
        "forensic", ("occurrence",),
        {"Value_flows": ("source_entity", "target_entity", "amount", "flow_date")},
        evidence_source="complete counterparty-to-company inflow and outflow feed",
        denominator_role="Value_flows",
        limitations="A coherent cycle is a lead, not an allegation of fraud.",
    ),
)

CONTRACTS_BY_ID = {contract.procedure_id: contract for contract in PROCEDURES}
