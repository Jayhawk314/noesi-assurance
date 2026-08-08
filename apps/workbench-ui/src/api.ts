/** Typed client for the workbench API — the shapes mirror the server contract. */

export interface Engagement {
  engagement_id: string;
  client_name: string;
  period_end: string;
  status: "open" | "locked" | "archived";
  version: number;
}

export interface TeamMember {
  principal_id: string;
  role: "preparer" | "reviewer" | "partner";
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
}

/** One item of a batch outcome; exactly one of the statuses applies. */
export interface BatchItem {
  artifact_id?: string;
  spec_id?: string;
  role?: string;
  status: "proposed" | "approved" | "normalized" | "skipped" | "error";
  reason?: string;
  error?: string;
  reconciliation?: Record<string, unknown>;
}

export interface BatchOutcome {
  results: BatchItem[];
  skipped: number;
  errors: number;
  proposed?: number;
  approved?: number;
  normalized?: number;
}

export interface MappingSpec {
  spec_id: string;
  role: string;
  artifact_id: string;
  status: "proposed" | "approved" | "superseded";
  proposed_by: string;
  approved_by: string;
  column_map: Record<string, string>;
  unmapped_headers: string[];
  refused_fields: string[];
  created_at: string;
}

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
}

export interface Sources {
  artifacts: Artifact[];
  mapping_specs: MappingSpec[];
  datasets: Dataset[];
}

export interface CoverageRow {
  procedure_id: string;
  name: string;
  objective: string;
  cycle: string;
  status: "executable" | "partial" | "blocked" | "unsupported";
  selected: boolean;
  missing_roles: string[];
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
}

export interface Run {
  run_id: string;
  procedure_id: string;
  job_id: string;
  status: "completed" | "error" | "reviewed" | "approved";
  summary: Record<string, unknown>;
  error: string;
  executed_by: string;
  reviewed_by: string;
  approved_by: string;
  version: number;
  created_at: string;
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
  disposition: { status: string; note: string; version: number };
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
}

export interface Blocker {
  code: string;
  count: number;
  items?: string[];
}

export interface Readiness {
  ready: boolean;
  status: string;
  report_implication: string;
  blockers: Blocker[];
  completion_done: number;
  completion_total: number;
  workpaper_locked: boolean;
}

export interface WorkflowDocument {
  materiality: { amount: number; basis: string; rationale: string };
  stages: Record<string, { status: string; note: string }>;
  completion: Record<string, { done: boolean; note: string }>;
  procedures?: Record<string, { selected: boolean; rationale: string }>;
  policies?: Record<string, string>;
}

export interface LockVerification {
  locked: boolean;
  error?: string;
  snapshot_ok?: boolean;
  drift?: string[];
  signature_ok?: boolean;
  signer?: { principal: string; key_id: string; algorithm: string; signed_at: string };
  journal_ok?: boolean;
  journal_events_checked?: number;
  verified?: boolean;
  sequence?: number;
  history?: LockHistoryEntry[];
  limits?: string;
}

/** A superseded lock: retained forever, re-verified from stored material. */
export interface LockHistoryEntry {
  sequence: number;
  snapshot_id: string;
  digest: string;
  locked_at: string;
  manifest_ok: boolean;
  signature_ok: boolean;
  journal_anchor_ok: boolean;
  signer: string | null;
  signed_at: string | null;
  unlocked_by: string;
  unlocked_at: string;
  reason: string;
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export class Client {
  /** Chair this session acts from; empty means the server's default. */
  actingAs = "";

  constructor(private token: string) {}

  private async request<T>(method: string, path: string, body?: unknown,
                           raw?: { data: Blob | ArrayBuffer; headers: Record<string, string> }): Promise<T> {
    const headers: Record<string, string> = { Authorization: `Bearer ${this.token}` };
    if (this.actingAs) headers["X-Acting-Principal"] = this.actingAs;
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

  session = () =>
    this.request<{ principal_id: string }>("GET", "/api/session");

  listEngagements = () =>
    this.request<{ engagements: Engagement[] }>("GET", "/api/engagements");
  createEngagement = (client_name: string, period_end: string) =>
    this.request<{ engagement_id: string }>("POST", "/api/engagements", { client_name, period_end });

  team = (eid: string) =>
    this.request<{ team: TeamMember[] }>("GET", `/api/engagements/${eid}/team`);
  assignTeam = (eid: string, principal_id: string, role: string) =>
    this.request("POST", `/api/engagements/${eid}/team`, { principal_id, role });

  sources = (eid: string) =>
    this.request<Sources>("GET", `/api/engagements/${eid}/sources`);
  uploadSource = (eid: string, file: File) =>
    this.request<{ artifact_id: string; sha256: string }>(
      "POST", `/api/engagements/${eid}/sources`, undefined,
      { data: file, headers: { "Content-Type": file.type || "text/csv", "X-Original-Name": file.name } });
  proposeMapping = (eid: string, role: string, artifact_id: string) =>
    this.request<{ spec_id: string; column_map: Record<string, string> }>(
      "POST", `/api/engagements/${eid}/mappings`, { role, artifact_id });
  approveMapping = (eid: string, spec_id: string) =>
    this.request("POST", `/api/engagements/${eid}/mappings/${spec_id}/approve`, {});
  normalize = (eid: string, spec_id: string) =>
    this.request<{ dataset_id: string; reconciliation: Record<string, unknown> }>(
      "POST", `/api/engagements/${eid}/mappings/${spec_id}/normalize`, {});
  proposeMappings = (eid: string, items: { artifact_id: string; role?: string }[]) =>
    this.request<BatchOutcome>(
      "POST", `/api/engagements/${eid}/mappings/propose-batch`, { items });
  approveMappings = (eid: string, spec_ids: string[]) =>
    this.request<BatchOutcome>(
      "POST", `/api/engagements/${eid}/mappings/approve-batch`, { spec_ids });
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
  reviewRun = (eid: string, run_id: string, target: "reviewed" | "approved", expected_version: number) =>
    this.request<{ version: number }>(
      "POST", `/api/engagements/${eid}/runs/${run_id}/review`, { target, expected_version });

  findings = (eid: string) =>
    this.request<{ findings: Finding[] }>("GET", `/api/engagements/${eid}/findings`);
  setDisposition = (eid: string, finding_uid: string, status: string, note: string, expected_version: number) =>
    this.request("POST", `/api/engagements/${eid}/dispositions`,
                 { finding_uid, status, note, expected_version });

  sad = (eid: string) => this.request<Sad>("GET", `/api/engagements/${eid}/sad`);
  readiness = (eid: string) =>
    this.request<Readiness>("GET", `/api/engagements/${eid}/readiness`);
  workflow = (eid: string) =>
    this.request<{ document: WorkflowDocument; version: number }>(
      "GET", `/api/engagements/${eid}/workflow`);
  updateWorkflow = (eid: string, section: string, values: Record<string, unknown>) =>
    this.request("POST", `/api/engagements/${eid}/workflow`, { section, values });

  lockStatus = (eid: string) =>
    this.request<LockVerification>("GET", `/api/engagements/${eid}/lock`);
  lock = (eid: string, expected_version: number) =>
    this.request<{ locked: boolean; blockers?: Blocker[]; digest?: string }>(
      "POST", `/api/engagements/${eid}/lock`, { expected_version });
  unlock = (eid: string, reason: string, expected_version: number) =>
    this.request<{ unlocked: boolean; version: number }>(
      "POST", `/api/engagements/${eid}/unlock`, { reason, expected_version });
  exportPacket = (eid: string) =>
    this.request<Record<string, unknown>>("POST", `/api/engagements/${eid}/export`, {});
}
