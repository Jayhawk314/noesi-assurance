// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** The ten-lesson course, in engagement order. */

import { COMPLETION } from "./lessons-completion";
import { FIELDWORK } from "./lessons-fieldwork";
import { PLANNING } from "./lessons-planning";
import { Lesson } from "./types";

export const LESSONS: Lesson[] = [...PLANNING, ...FIELDWORK, ...COMPLETION];
