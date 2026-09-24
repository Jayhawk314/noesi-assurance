// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** Shapes for the "Learn the audit" course. Content lives in lessons.ts;
 *  the research and verification notes behind it are in
 *  docs/learn/CURRICULUM.md. Inline text supports **bold** only. */

export type Block =
  | { p: string }
  | { list: string[] }
  | { steps: string[] }
  | { terms: [string, string][] }
  | { table: { head: string[]; rows: string[][] } }
  | { harborline: string }
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

export interface Lesson {
  n: number;
  slug: string;
  title: string;
  phase: "Planning" | "Fieldwork" | "Completion" | "Fraud";
  question: string;
  minutes: number;
  objectives: string[];
  sections: Section[];
  standards: [string, string][];
  check: Question[];
  task: { title: string; intro: string; steps: string[]; deliver: string };
  noesi: {
    coverage: "full" | "partial" | "none";
    summary: string;
    does: string[];
    where: string[];
    doesNot: string[];
    tryIt?: string;
  };
}
