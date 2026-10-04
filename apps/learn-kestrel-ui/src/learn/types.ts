// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** Shapes for the Kestrel Learn course (docs/LEARN-KESTREL-PLAN.md). Each
 *  module has four steps: the idea, by hand, in Noesi, compare with the key.
 *  Inline text supports **bold** and `code` only.
 *
 *  No figure is typed into a lesson: the compare step reads every figure from
 *  kestrel-key.json (written by scripts/export_key.py from the finish-line
 *  check), and scripts/check-lessons.mjs refuses prose numbers the key does
 *  not hold. */

export type Block =
  | { p: string }
  | { list: string[] }
  | { steps: string[] }
  | { terms: [string, string][] }
  | { table: { head: string[]; rows: string[][] } }
  | { kestrel: string }
  | { watch: string };

export interface Section {
  heading: string;
  blocks: Block[];
}

export interface Question {
  q: string;
  options: string[];
  answer: number;
  why: string;
}

/** One answer the learner writes down by hand. `row` names a line of the
 *  finish-line check for this module (its Workbench value and status);
 *  `key`, when given, is a path into the answer key whose value is shown
 *  instead of the row's own key value (for a line whose key is yes/no). */
export interface Ask {
  label: string;
  row: string;
  key?: string;
  /** The finish-line module holding `row`, when not the lesson's keyModule
   *  (fraud lessons draw on several). */
  module?: string;
}

export interface Lesson {
  n: number;
  slug: string;
  /** Optional teaching video (public/videos/; the single-file page plays it through jsDelivr). */
  video?: { file: string; poster?: string; title: string; minutes: number; credits: string };
  title: string;
  phase: "Planning" | "Fieldwork" | "Completion" | "Fraud";
  question: string;
  minutes: number;
  objectives: string[];
  /** Step 1: the idea. */
  sections: Section[];
  standards: [string, string][];
  check: Question[];
  /** Step 2: by hand, on the Kestrel files. */
  byHand: { files: string[]; intro: string; steps: string[]; asks: Ask[] };
  /** Step 3: the same work in the Workbench. */
  inNoesi: { procedures: string[]; steps: string[] };
  /** Step 4 reads the rows of this finish-line module from kestrel-key.json. */
  keyModule: string;
  /** Instead of a whole module, these lines ([module, item]) of the check. */
  keyLines?: [string, string][];
  noesi: {
    coverage: "full" | "partial" | "none";
    summary: string;
    does: string[];
    where: string[];
    doesNot: string[];
  };
}

/** A module listed on the course map with no lesson yet. */
export interface Coming {
  n: number;
  title: string;
  phase: Lesson["phase"];
  waitsFor: string;
}
