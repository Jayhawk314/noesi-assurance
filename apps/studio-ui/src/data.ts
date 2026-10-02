// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** One engagement, loaded whole, and the journey read off it.
 *
 *  The studio never decides anything the server has not already recorded:
 *  every stage status below is a direct reading of coverage, runs,
 *  findings, SAD or readiness. "Next step" names the first stage
 *  that is not done and — only where the server offers a one-shot
 *  action — the button that does it. */

import {
  Client, Coverage, Engagement, Finding, Impact,
  Readiness, Run, Sad, Sources, WorkflowDocument,
} from "../../workbench-ui/src/api";

export const ROLES = [
  "Vendors", "Employees", "Purchase_orders", "Goods_receipts", "Vouchers",
  "Payments", "Bank", "GL", "AP_control_balance", "Value_flows",
] as const;

export interface Bundle {
  engagement: Engagement;
  sources: Sources;
  coverage: Coverage;
  runs: Run[];
  findings: Finding[];
  sad: Sad;
  readiness: Readiness;
  workflow: WorkflowDocument;
  workflowVersion: number;
  impact: Impact | null;
}

export async function loadBundle(client: Client, engagement: Engagement): Promise<Bundle> {
  const eid = engagement.engagement_id;
  const [sources, coverage, runs, findings, sad, readiness, workflow,
         impact] = await Promise.all([
    client.sources(eid), client.coverage(eid),
    client.runs(eid), client.findings(eid), client.sad(eid),
    client.readiness(eid), client.workflow(eid),
    // The impact report rebuilds every file version; an older server
    // without the endpoint simply has nothing to show.
    client.impact(eid).catch(() => null),
  ]);
  return {
    engagement, sources, coverage, runs: runs.runs,
    findings: findings.findings, sad, readiness,
    workflow: workflow.document, workflowVersion: workflow.version,
    impact,
  };
}

/** The newest run of each procedure — earlier reruns are history. */
export function latestRuns(runs: Run[]): Map<string, Run> {
  const out = new Map<string, Run>();
  for (const run of runs) out.set(run.procedure_id, run);
  return out;
}

/** Findings from the newest run of each procedure only. */
export function currentFindings(bundle: Bundle): Finding[] {
  const current = new Set([...latestRuns(bundle.runs).values()].map((r) => r.run_id));
  return bundle.findings.filter((f) => current.has(f.run_id));
}

export type StageId =
  | "plan" | "collect" | "scope" | "test" | "judge"
  | "conclude" | "export";
export type StageState = "done" | "active" | "waiting" | "attention";

export interface Stage {
  id: StageId;
  title: string;
  question: string;
  state: StageState;
  progress: [number, number];
  detail: string;
}

export interface NextStep {
  stage: StageId;
  headline: string;
  why: string;
  action: NextAction | null;
}

export type NextAction =
  | { kind: "run"; procedureIds: string[] }
  | { kind: "materiality" }
  | { kind: "view"; view: ViewId }
  | { kind: "workbench"; tab: string };

export type ViewId = "overview" | "findings" | "changes" | "conclude";

export function journey(bundle: Bundle): { stages: Stage[]; next: NextStep | null } {
  const materiality = Number(bundle.workflow.materiality?.amount || 0);
  const loadedRoles = new Set(bundle.sources.datasets.map((d) => d.role));
  const executable = bundle.coverage.procedures.filter(
    (p) => p.selected && p.status === "executable");
  const partial = bundle.coverage.procedures.filter(
    (p) => p.selected && p.status === "partial");
  const latest = latestRuns(bundle.runs);
  const stale = new Set((bundle.impact?.stale_runs ?? []).map((r) => r.procedure_id));
  const toRun = executable
    .filter((p) => {
      const run = latest.get(p.procedure_id);
      return !run || run.status === "error" || stale.has(p.procedure_id);
    })
    .map((p) => p.procedure_id);
  const ran = executable.length - toRun.length;
  const findings = currentFindings(bundle);
  const undisposed = findings.filter((f) => f.disposition.status === "undisposed");

  const state = (done: boolean, attention = false): StageState =>
    done ? "done" : attention ? "attention" : "waiting";

  const stages: Stage[] = [
    {
      id: "plan", title: "Plan", question: "How big a mistake would matter?",
      state: state(materiality > 0), progress: [materiality > 0 ? 1 : 0, 1],
      detail: materiality > 0
        ? `Materiality ${money(materiality)}; clearly trivial ${money(bundle.sad.clearly_trivial)}`
        : "No materiality set yet",
    },
    {
      id: "collect", title: "Collect", question: "What did the client give us?",
      state: state(loadedRoles.size >= ROLES.length, loadedRoles.size > 0),
      progress: [loadedRoles.size, ROLES.length],
      detail: `${loadedRoles.size} of ${ROLES.length} record sets loaded`,
    },
    {
      id: "scope", title: "Scope", question: "What can this data actually prove?",
      state: state(executable.length > 0 && partial.length === 0, executable.length > 0),
      progress: [executable.length, bundle.coverage.procedures.length],
      detail: `${executable.length} procedures runnable` +
        (partial.length ? `, ${partial.length} waiting on a policy` : ""),
    },
    {
      id: "test", title: "Test", question: "Run the procedures",
      state: state(executable.length > 0 && toRun.length === 0, ran > 0),
      progress: [ran, executable.length],
      detail: stale.size
        ? `${stale.size} run(s) rest on a replaced file`
        : `${ran} of ${executable.length} run`,
    },
    {
      id: "judge", title: "Judge", question: "What does each exception mean?",
      state: state(findings.length > 0 && undisposed.length === 0, findings.length > 0),
      progress: [findings.length - undisposed.length, findings.length],
      detail: `${undisposed.length} need a judgment`,
    },
    {
      id: "conclude", title: "Conclude", question: "Is the total material?",
      state: state(bundle.sad.conclusion !== null),
      progress: [bundle.sad.conclusion !== null ? 1 : 0, 1],
      detail: bundle.sad.conclusion ? `SAD: ${bundle.sad.conclusion}` : "SAD not concluded",
    },
    {
      // Noesi supplements the audit; there is no sign-off (removed 1 Oct 2026).
      id: "export", title: "Export", question: "Is anything still open?",
      state: state(bundle.readiness.ready),
      progress: [bundle.readiness.ready ? 1 : 0, 1],
      detail: bundle.readiness.ready
        ? "Nothing open: export the record"
        : `${bundle.readiness.blockers.length} item(s) still open`,
    },
  ];
  const firstOpen = stages.findIndex((s) => s.state !== "done");
  if (firstOpen >= 0) stages[firstOpen].state = "active";

  const open = stages[firstOpen]?.id;
  let next: NextStep | null = null;
  switch (open) {
    case "plan":
      next = { stage: open, action: { kind: "materiality" },
               headline: "Set materiality",
               why: "Every later judgment — what is trivial, what needs a second opinion, what goes on the SAD — is measured against it." };
      break;
    case "collect":
      next = { stage: open,
               action: { kind: "workbench", tab: "Sources & Mappings" },
               headline: `Load the client's files (${ROLES.length - loadedRoles.size} record sets missing)`,
               why: "Upload, map and confirm each file's columns, then load it. Refused columns are real facts about the data." };
      break;
    case "scope":
      next = { stage: open,
               action: { kind: "workbench", tab: "Coverage" },
               headline: partial.length
                 ? `Approve ${partial.flatMap((p) => p.missing_policies).join(", ")}`
                 : "Nothing is runnable yet",
               why: "Some procedures need an engagement decision, like the client's approval limit, before they can test anything." };
      break;
    case "test":
      next = { stage: open, action: { kind: "run", procedureIds: toRun },
               headline: stale.size
                 ? `Rerun ${toRun.length} procedure(s) on the corrected file`
                 : `Run ${toRun.length} procedure(s)`,
               why: "Each run tests the whole population and freezes exactly which data it used." };
      break;
    case "judge":
      next = { stage: open, action: { kind: "view", view: "findings" },
               headline: `Judge ${undisposed.length} exception(s)`,
               why: "An exception is a lead, not a conclusion. Each needs a disposition and a note saying why." };
      break;
    case "conclude":
      next = { stage: open, action: { kind: "workbench", tab: "SAD & Completion" },
               headline: "Conclude the SAD",
               why: "Compare uncorrected differences to materiality: every misstatement candidate needs a disposition." };
      break;
    case "export":
      next = { stage: open, action: { kind: "workbench", tab: "Export" },
               headline: "See what is still open, then export the record",
               why: "Readiness lists what stands between the record and an opinion; the record exports any time, unsigned, and checks itself with no tool." };
      break;
  }
  return { stages, next };
}

export function money(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return value.toLocaleString(undefined, { style: "currency", currency: "USD",
                                           maximumFractionDigits: 0 });
}
