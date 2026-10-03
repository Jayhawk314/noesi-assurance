// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** Typed client for the workbench API — the shapes mirror the server contract. */

export interface Engagement {
  engagement_id: string;
  client_name: string;
  period_end: string;
  /** "locked" only on engagements read before locks were removed (1 Oct 2026). */
  status: "open" | "locked" | "archived";
  version: number;
}

export interface Artifact {
  artifact_id: string;
  sha256: string;
  size_bytes: number;
  media_type: string;
  original_name: string;
  provenance: string;
  state: "promoted" | "retired";
  created_at: string;
  /** Filename-based role suggestion; null when nothing is inferable. */
  inferred_role: string | null;
  /** how the role was suggested: from the file's name or from its columns */
  inferred_from?: "filename" | "columns" | "";
  /** The schedule the Workbench built from this file, if any: its input,
   *  so "map all" leaves it out. */
  built_into?: string | null;
}

/** One item of a batch outcome; exactly one of the statuses applies. */
export interface BatchItem {
  artifact_id?: string;
  spec_id?: string;
  role?: string;
  status: "confirmed" | "normalized" | "skipped" | "error";
  reason?: string;
  error?: string;
  reconciliation?: Record<string, unknown>;
}

export interface BatchOutcome {
  results: BatchItem[];
  skipped: number;
  errors: number;
  confirmed?: number;
  normalized?: number;
}

export interface MappingSpec {
  spec_id: string;
  role: string;
  artifact_id: string;
  /** "approved" means confirmed; "proposed" only on mappings from before
   *  2 Oct 2026 that were never approved. */
  status: "proposed" | "approved" | "superseded";
  proposed_by: string;
  approved_by: string;
  column_map: Record<string, string>;
  unmapped_headers: string[];
  refused_fields: string[];
  created_at: string;
  /** For an Excel source: the sheet and header row this spec reads, and the
   *  QuickBooks recipe that flattened it, if any. */
  extraction?: { converter: string; sheet: string; header_row: number;
                 recipe?: string; recipe_version?: string } | null;
  /** What a QuickBooks recipe checked, kept and left out. */
  recipe_report?: RecipeReport | null;
}

/** A QuickBooks report recognized on a sheet, with the role it can feed. */
export interface RecipeMatch {
  recipe: string; label: string; report: string; role: string;
  header_row: number; note: string;
}

export interface TotalCheck {
  group: string; column: string; sheet_row: number; computed: string;
  stated: string | null; agrees: boolean;
}

export interface RecipeReport {
  recipe: string; report: string; role: string; rows_kept: number;
  subtotals_checked: number; grand_total: TotalCheck[] | null;
  totals_disagreeing: TotalCheck[]; note: string;
  missing_required?: { field: string; heading: string; rows: number; of: number }[];
  transaction_types?: Record<string, { kept: number; left_out: number }>;
  amount_signs_by_account?: Record<string, { negative: number; positive: number; zero: number }>;
}

/** An uploaded workbook's sheets, first rows and suggested header rows. */
export interface WorkbookPreview {
  artifact_id: string;
  sheets: { sheet: string; rows: string[][]; row_count: number; suggested_header_row: number;
            recipes?: RecipeMatch[];
            /** A recognized QuickBooks export with no recipe, and why. */
            quickbooks_note?: string | null }[];
}

export interface Extraction { sheet?: string; header_row?: number; recipe?: string }

/** Uploaded QuickBooks exports that can serve as each side of the AP tie. */
export interface ApControlCandidates {
  subledger: { artifact_id: string; original_name: string }[];
  ledger: { artifact_id: string; original_name: string }[];
}

export interface ApControlBuilt {
  artifact_id: string; period_end: string; subledger_balance: string;
  gl_balance: string; difference: string; notes: string[];
}

/** Uploaded QuickBooks Trial Balance exports, each with the date it is as of. */
export interface TrialBalanceCandidates {
  trial_balances: { artifact_id: string; original_name: string; as_of: string | null;
                    period: string }[];
}

export interface TrialBalanceBuilt {
  artifact_id: string; as_of: string | null; prior_as_of: string | null;
  accounts: number; notes: string[];
}

export type LoadMode = "replace" | "add";

export interface Dataset {
  dataset_id: string;
  role: string;
  mapping_spec_id: string;
  artifact_id: string;
  rows_in: number;
  rows_loaded: number;
  rows_rejected: number;
  control_total: string | null;
  output_digest: string;
  created_at: string;
  /** Whether procedures read this dataset: only the latest per role is used. */
  in_use?: boolean;
  /** first load, a replacement (revised file), or added rows (e.g. another account). */
  load_mode?: "first" | "replace" | LoadMode;
  /** Why rows were set aside (quarantined), with their source row numbers. */
  rejected_reasons?: { reason: string; rows: number; source_rows: number[] }[];
}

export interface Sources {
  artifacts: Artifact[];
  mapping_specs: MappingSpec[];
  datasets: Dataset[];
  /** every data type the engine can load */
  roles?: string[];
}

export interface CoverageRow {
  procedure_id: string;
  name: string;
  objective: string;
  cycle: string;
  status: "executable" | "partial" | "blocked" | "unsupported";
  selected: boolean;
  default_selected?: boolean;
  missing_roles: string[];
  /** Present when an alternative input set (not the required one) serves. */
  satisfied_by?: string[];
  missing_fields: Record<string, string[]>;
  missing_policies: string[];
  population: number | null;
  execution_status: string;
  required_policies: string[];
  limitations: string;
  /** Present only when no executor is registered for this procedure. */
  unsupported_reason?: string;
}

export interface EvidenceRequest {
  request_id: string;
  kind: "dataset" | "field" | "policy";
  item: string;
  owner: string;
  unlocks: string[];
  cycles: string[];
  assertions: string[];
}

export interface Coverage {
  procedures: CoverageRow[];
  summary: Record<string, number>;
  evidence_requests: EvidenceRequest[];
  /** What a builder noted about a file in use (e.g. a trial balance not at period end). */
  source_notes?: { role: string; file: string; note: string }[];
}

export interface Run {
  run_id: string;
  procedure_id: string;
  job_id: string;
  /** "reviewed" and "approved" appear only on runs from before 1 Oct 2026. */
  status: "completed" | "error" | "reviewed" | "approved";
  summary: Record<string, unknown>;
  error: string;
  executed_by: string;
  version: number;
  created_at: string;
  /** What a completed run tested: a refusal is a part not tested (null on error). */
  tested?: "all" | "partly" | "nothing" | "limited" | null;
}

export interface Verdict {
  domain: string;
  key: unknown[];
  verdict: string;
  policy: string;
  score: number | null;
  reason: string;
  evidence: Record<string, unknown>;
  receipt_id: string;
}

export interface Finding {
  finding_uid: string;
  run_id: string;
  procedure_id: string;
  verdict: Verdict;
  tags: { cycle: string; class: string; phase: string; assertion: string };
  disposition: {
    status: string; note: string; version: number;
    proposed_by: string;
  };
}

/** One assessed risk: auditor judgment, tracked like a disposition. */
export interface Risk {
  risk_id: string;
  title: string;
  assertion: string;
  level: "unassessed" | "low" | "moderate" | "high" | "significant";
  /** The auditor marked this a fraud risk (AU-C 240). */
  fraud: boolean;
  rationale: string;
  response: string;
  procedure_ids: string[];
  /** Procedures whose contract addresses this risk's assertion. */
  candidate_procedures: string[];
  proposed_by: string;
  version: number;
}

/** One fraud test and whether it could run on these records. */
export interface FraudTest {
  procedure_id: string; scheme: string; basis: string; name: string;
  coverage: string; in_scope: boolean; missing: string[]; limitations: string;
  last_run: { status: string; at: string; run_id: string } | null;
  findings: number; open: number;
  /** Why the test did not test (a refusal), one reason per refusal. */
  not_tested: string[];
  tested: "all" | "partly" | "nothing" | "limited" | null;
}

export interface FraudView {
  tests: FraudTest[];
  risks: Risk[];
  findings: Finding[];
  not_tested: Finding[];
  summary: { tests: number; run: number; cannot_run: number; partly: number; findings: number;
             open_findings: number; not_tested: number; partly_tested: number; limited: number;
             fraud_risks: number };
  presumed_risks: string[];
}

export interface RiskRegister {
  risks: Risk[];
  assertions: string[];
  levels: string[];
}

export interface Sad {
  overall_materiality: number;
  performance_materiality: number | null;
  clearly_trivial: number;
  unadjusted: { finding_id: string; account: string; reason: string; amount: number }[];
  total_unadjusted: number;
  total_adjusted: number;
  candidates: number;
  disposed: number;
  open_count: number;
  invalid_waiver_count: number;
  conclusion: "immaterial" | "material" | null;
  schedule: {
    run_id: string; materiality: string; lines: Record<string, string>;
    identified: string | null; likely: string | null; likely_basis: string | null;
    material_lines: string[]; note: string;
  } | null;
}

export interface Blocker {
  code: string;
  count: number;
  items?: string[];
  /** Open findings counted by the procedure that found them (FINDINGS_OPEN). */
  by_procedure?: Record<string, number>;
}

export interface Readiness {
  ready: boolean;
  status: string;
  report_implication: string;
  blockers: Blocker[];
}

export interface WorkflowDocument {
  materiality: { amount: number; basis: string; rationale: string;
                 benchmark_amount?: string; percentage?: string };
  procedures?: Record<string, { selected: boolean; rationale: string; decided_by?: string }>;
  policies?: Record<string, string>;
  cycles?: string[];
  period?: { start: string };
}

/** The audit areas a partner can switch on, from GET /api/cycles. */
export interface CycleArea {
  scope: string;
  procedures: { procedure_id: string; title: string; required_policies: string[] }[];
  required_policies: string[];
  optional_policies: string[];
}
export interface CycleCatalog {
  areas: CycleArea[]; engagement_policies: string[]; general_policies: string[];
  /** Each setting in words: label, kind of value (amount, percent, days...), meaning. */
  policy_text?: Record<string, { label: string; kind: string; meaning: string }>;
}

/** The loaded trial balance's own labels and how they map to statement lines. */
export interface TrialBalanceLines {
  lines: string[];
  labels: { label: string; accounts: string[]; recognized: boolean;
            mapped_to: string | null; suggestion: string | null }[];
  /** Accounts whose own label is not a statement line, each with a suggestion from its name. */
  accounts: { account: string; description: string; label: string;
              mapped_to: string | null; suggestion: string | null }[];
  account_overrides: Record<string, string>;
  has_trial_balance: boolean;
}

/** The draft opinion (a proposal; the partner decides). */
export interface DraftOpinion {
  status: string;
  proposed_opinion: string;
  /** the opinion once every judgment is recorded; null while any is open */
  opinion: string | null;
  going_concern_section: boolean;
  recorded_decisions: Record<string, { answer: string; note: string; decided_by: string }>;
  decision_answers: Record<string, string[]>;
  basis: string[];
  decisions_required: { decision: string; why: string }[];
  readiness_blockers: Blocker[];
  misstatements: { source: string; largest_line: string; amount: string };
  materiality: string;
  open_scope_limitations: number;
  missing_representations: string[];
  going_concern_indicators: string[];
  note: string;
}

export type Significance = "none" | "below_trivial" | "not_measured" | "above_trivial" | "above_performance";

export interface RowChange {
  key: string;
  amount?: number | null;
  amount_change?: number | null;
  fields?: { field: string; before: unknown; after: unknown }[];
  significance: Significance;
}

export interface FileRevision {
  role: string;
  versions: number;
  /** how the latest file was loaded: a replacement or added rows */
  load_mode?: "first" | "replace" | "add";
  before: { dataset_id: string; file: string; files?: string[]; loaded_at: string };
  after: { dataset_id: string; file: string; files?: string[]; loaded_at: string };
  diff: {
    key_fields: string[]; rows_before: number; rows_after: number;
    added: RowChange[]; removed: RowChange[]; changed: RowChange[];
    duplicate_keys: string[]; net_amount_change: number;
    significance: Significance;
  };
}

export interface StaleRun {
  run_id: string; procedure_id: string; status: Run["status"];
  changed_inputs: string[]; findings_before: number; findings_after: number;
  rerun_error: string; action: string;
}

export interface ImpactCard {
  finding_uid: string; procedure_id: string; run_id: string;
  domain: string; key: unknown[]; reason: string;
  change: "amount_changed" | "resolved_by_revision" | "new_after_revision";
  amount_before: number | null; amount_after: number | null;
  amount_change: number; significance: Significance;
  disposition: string;
  action: "dispose" | "revisit_disposition" | "reassess_disposition" | "none_after_rerun";
  what_it_means: string;
}

export interface Impact {
  engagement_id: string;
  thresholds: { materiality: number; clearly_trivial: number; performance: number };
  revisions: FileRevision[];
  stale_runs: StaleRun[];
  cards: ImpactCard[];
  summary: {
    revised_files: number; stale_runs: number; affected_findings: number;
    judgments_to_revisit: number; new_findings: number;
    actions: Record<string, number>; significance: Significance;
    sad_effect: { unadjusted: number; adjusted: number };
  };
  limits: string;
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export class Client {
  constructor(private token: string) {}

  private async request<T>(method: string, path: string, body?: unknown,
                           raw?: { data: Blob | ArrayBuffer; headers: Record<string, string> }): Promise<T> {
    const headers: Record<string, string> = { Authorization: `Bearer ${this.token}` };
    let payload: BodyInit | undefined;
    if (raw) {
      payload = raw.data;
      Object.assign(headers, raw.headers);
    } else if (body !== undefined) {
      headers["Content-Type"] = "application/json";
      payload = JSON.stringify(body);
    }
    const response = await fetch(path, { method, headers, body: payload });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new ApiError(response.status, (data as { error?: string }).error ?? response.statusText);
    }
    return data as T;
  }

  /** The working paper as HTML, rendered from the record as it stands. */
  workpaperHtml = async (eid: string): Promise<string> => {
    const headers: Record<string, string> = { Authorization: `Bearer ${this.token}` };
    const response = await fetch(`/api/engagements/${eid}/workpaper`, { headers });
    const text = await response.text();
    if (!response.ok) {
      let message = response.statusText;
      try { message = (JSON.parse(text) as { error?: string }).error ?? message; } catch { /* html */ }
      throw new ApiError(response.status, message);
    }
    return text;
  };

  session = () =>
    this.request<{ principal_id: string }>("GET", "/api/session");

  manualChapters = () =>
    this.request<{ chapters: { name: string; title: string }[] }>(
      "GET", "/api/manual");
  manualChapter = (name: string) =>
    this.request<{ name: string; title: string; html: string }>(
      "GET", `/api/manual/${name}`);

  listEngagements = () =>
    this.request<{ engagements: Engagement[] }>("GET", "/api/engagements");
  createEngagement = (client_name: string, period_end: string) =>
    this.request<{ engagement_id: string }>("POST", "/api/engagements", { client_name, period_end });
  archivedEngagements = () =>
    this.request<{ engagements: Engagement[] }>("GET", "/api/engagements/archived");
  archiveEngagement = (eid: string, reason: string) =>
    this.request("POST", `/api/engagements/${eid}/archive`, { reason });
  deleteEngagement = (eid: string, confirm_client_name: string, reason: string) =>
    this.request("POST", `/api/engagements/${eid}/delete`, { confirm_client_name, reason });
  restoreEngagement = (eid: string) =>
    this.request("POST", `/api/engagements/${eid}/restore`, {});
  cases = () =>
    this.request<{ cases: { case: string; title: string }[] }>("GET", "/api/cases");
  loadCase = (name: string) =>
    this.request<{ engagement_id: string; seeded: boolean }>("POST", `/api/cases/${name}/load`, {});

  sources = (eid: string) =>
    this.request<Sources>("GET", `/api/engagements/${eid}/sources`);
  uploadSource = (eid: string, file: File) =>
    this.request<{ artifact_id: string; sha256: string }>(
      "POST", `/api/engagements/${eid}/sources`, undefined,
      { data: file, headers: { "Content-Type": file.type || "text/csv", "X-Original-Name": file.name } });
  /** Map a file's columns and confirm the mapping, in one step. */
  confirmMapping = (eid: string, role: string, artifact_id: string, extraction?: Extraction) =>
    this.request<{ spec_id: string; column_map: Record<string, string> }>(
      "POST", `/api/engagements/${eid}/mappings`, { role, artifact_id, extraction });
  apControlCandidates = (eid: string) =>
    this.request<ApControlCandidates>("GET", `/api/engagements/${eid}/ap-control/candidates`);
  buildApControl = (eid: string, subledger_artifact_id: string, ledger_artifact_id: string) =>
    this.request<ApControlBuilt>("POST", `/api/engagements/${eid}/ap-control`,
      { subledger_artifact_id, ledger_artifact_id });
  trialBalanceCandidates = (eid: string) =>
    this.request<TrialBalanceCandidates>(
      "GET", `/api/engagements/${eid}/trial-balance/candidates`);
  buildTrialBalance = (eid: string, current_artifact_id: string, prior_artifact_id: string) =>
    this.request<TrialBalanceBuilt>("POST", `/api/engagements/${eid}/trial-balance`,
      { current_artifact_id, prior_artifact_id: prior_artifact_id || null });
  workbookPreview = (eid: string, artifact_id: string) =>
    this.request<WorkbookPreview>("GET", `/api/engagements/${eid}/artifacts/${artifact_id}/sheets`);
  /** Confirm a mapping proposed before 2 Oct 2026 and never approved. */
  confirmPendingMapping = (eid: string, spec_id: string) =>
    this.request("POST", `/api/engagements/${eid}/mappings/${spec_id}/confirm`, {});
  /** mode: required when the role already has data — "replace" or "add". */
  normalize = (eid: string, spec_id: string, mode?: LoadMode) =>
    this.request<{ dataset_id: string; load_mode: string; reconciliation: Record<string, unknown> }>(
      "POST", `/api/engagements/${eid}/mappings/${spec_id}/normalize`, mode ? { mode } : {});
  confirmMappings = (eid: string, items: { artifact_id: string; role?: string; extraction?: Extraction }[]) =>
    this.request<BatchOutcome>(
      "POST", `/api/engagements/${eid}/mappings/confirm-batch`, { items });
  normalizeBatch = (eid: string, spec_ids: string[]) =>
    this.request<BatchOutcome>(
      "POST", `/api/engagements/${eid}/mappings/normalize-batch`, { spec_ids });

  coverage = (eid: string) =>
    this.request<Coverage>("GET", `/api/engagements/${eid}/coverage`);

  runs = (eid: string) =>
    this.request<{ runs: Run[] }>("GET", `/api/engagements/${eid}/runs`);
  runProcedure = (eid: string, procedure_id: string, policies: Record<string, string>) =>
    this.request<{ run_id: string; status: string; findings: number; error: string }>(
      "POST", `/api/engagements/${eid}/runs`, { procedure_id, policies });

  findings = (eid: string) =>
    this.request<{ findings: Finding[] }>("GET", `/api/engagements/${eid}/findings`);
  setDisposition = (eid: string, finding_uid: string, status: string, note: string, expected_version: number) =>
    this.request("POST", `/api/engagements/${eid}/dispositions`,
                 { finding_uid, status, note, expected_version });

  fraud = (eid: string) =>
    this.request<FraudView>("GET", `/api/engagements/${eid}/fraud`);
  risks = (eid: string) =>
    this.request<RiskRegister>("GET", `/api/engagements/${eid}/risks`);
  assessRisk = (eid: string, risk: {
    risk_id?: string; title: string; assertion: string; level: string;
    rationale?: string; response?: string; expected_version?: number;
    fraud?: boolean;
  }) =>
    this.request<{ risk_id: string; version: number }>(
      "POST", `/api/engagements/${eid}/risks`, risk);
  linkRiskProcedures = (eid: string, risk_id: string, procedure_ids: string[],
                        expected_version: number) =>
    this.request<{ version: number }>(
      "POST", `/api/engagements/${eid}/risks/${risk_id}/procedures`,
      { procedure_ids, expected_version });
  archiveRisk = (eid: string, risk_id: string, expected_version: number) =>
    this.request<{ archived: boolean; version: number }>(
      "POST", `/api/engagements/${eid}/risks/${risk_id}/archive`,
      { expected_version });

  impact = (eid: string) =>
    this.request<Impact>("GET", `/api/engagements/${eid}/impact`);

  sad = (eid: string) => this.request<Sad>("GET", `/api/engagements/${eid}/sad`);
  cycleCatalog = () => this.request<CycleCatalog>("GET", "/api/cycles");
  trialBalanceLines = (eid: string) =>
    this.request<TrialBalanceLines>("GET", `/api/engagements/${eid}/trial-balance-lines`);  draftOpinion = (eid: string) =>
    this.request<DraftOpinion>("GET", `/api/engagements/${eid}/opinion`);
  readiness = (eid: string) =>
    this.request<Readiness>("GET", `/api/engagements/${eid}/readiness`);
  workflow = (eid: string) =>
    this.request<{ document: WorkflowDocument; version: number }>(
      "GET", `/api/engagements/${eid}/workflow`);
  updateWorkflow = (eid: string, section: string, values: Record<string, unknown>) =>
    this.request("POST", `/api/engagements/${eid}/workflow`, { section, values });

  exportRecord = (eid: string) =>
    this.request<Record<string, unknown>>("POST", `/api/engagements/${eid}/export`, {});
}
