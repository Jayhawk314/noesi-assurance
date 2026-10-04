# Session summary, 3–4 Oct 2026: Kestrel Learn videos, manual, Code Atlas, links

## Result
- **Videos:** all 22 Kestrel Learn videos (13 audit modules, 9 fraud lessons) are made, in the Learn
  app, and pushed. Narration: ElevenLabs "Guy".
- **Manual:**
  - the 8 chapters were brought up to date with the code;
  - new: `docs/manual/HOW-NOESI-WORKS.md`, covering the maths, what makes Noesi different, its limits and
    open items, and its value;
  - the Code Atlas was refreshed and extended with every Learn lesson.
- **Links (opening from the desktop "Noesi Workbench"):**
  - the Workbench header **Learn ↗** opens the Kestrel Learn course at `/kestrel/`;
  - that course has **Workbench ↗**, **Manual**, **How Noesi works** and **Code Atlas**;
  - the Code Atlas opens interactive at `/kestrel/code-atlas.html`.
- **Pushed:** everything is on GitHub; the last commits are 55b7bb0 and 38b756d.

## What was done

### Videos
- **Scripts:** 13 new scripts with FACTS tables (m02–m04, m06, m07, f02–f09). `check_facts.py` passes
  for all 22. A second agent reviewed them (`komposos-labs-videos/noesi_learn_videos/kestrel/REVIEW-2026-10-03-new-scripts.md`),
  and the fixes were applied before voicing.
- **Voicing:** 23,818 characters sent for the 13 new videos, about 4,800 credits at the measured 0.2 a
  character. The other nine reused their 3 Oct narration.
- **Screens:**
  - all clips re-captured on 4 Oct, after the header contrast fix (ef07c2e);
  - the "Now you" shots show the exercise unanswered;
  - the South Korean bike-shop photo was replaced.
- **Learn module 1:** the "three roles" step now says review happens in the firm, outside Noesi. Team
  roles, review and sign-off are parked as possible future features (ROADMAP, Parking lot).
- **Tools** (`komposos-labs-videos/noesi_learn_videos/kestrel/`):
  - `build_kestrel.py` builds fraud lessons separately from modules;
  - shots stop before the next screen;
  - `wire.py` puts a video into the app.

  How to run them: `START-HERE.md`.

### Manual and Code Atlas
- **Chapter 5:** the stale-result rules after 11b4038, including the exception for procedures the draft
  opinion reads.
- **HOW-NOESI-WORKS.md:** written from the code, then corrected after an independent review
  (`docs/reviews/REVIEW-2026-10-04-manual-docs.md`). The corrections:
  - vendor twins match names (and activity), not address or phone;
  - analytics need both thresholds unless the rule is "or";
  - 587 tests, not 523;
  - the round-trip limits are fixed in code.
- **Code Atlas** (`docs/manual/Noesi Audit Code Atlas.html`):
  - `refresh_atlas.py` re-reads the 10 stops' 139 excerpts from the code;
  - `build_atlas_lessons.py` adds one stop per lesson (22), built only from the lesson text, the engine
    registries, the procedure contracts and the answer key;
  - all 197 excerpts were checked line for line against the files after the last code edit;
  - the stale "Approved" warning was removed.
- **Interactive in the Workbench:**
  - the Workbench sends a strict security policy, and online previews (htmlpreview, githack) don't run
    the Atlas's scripts;
  - so `atlas_copy.py` writes a Workbench copy, `apps/learn-kestrel-ui/public/code-atlas.html`, with its
    script and styles in separate files and a saved highlight.js 11.9.0 (BSD);
  - both Atlas scripts keep that copy in sync;
  - the claude.ai page "Noesi Audit Code Atlas" (private) was updated to the same version.

### Workbench and Studio
- **The Workbench now serves the Kestrel Learn build at `/kestrel/`:** `server.py` and `__main__.py`, with
  the same security rules as `/studio/`.
- **The manual panel** keeps links to `/kestrel/` pages (`manual.py`).
- **The Studio's Learn page** (Harborline) has Manual, How Noesi works and Code Atlas links. The Studio itself
  is otherwise unchanged.

### Codex's uncommitted work, reviewed and committed
- **Related-party matching (`estimates.py`):** a party who matches an employee by name is no longer called "a
  family member" (the Jo Kestrel / E01 case). The code reads correctly, `test_estimates` passes 6 of 6,
  and the Kestrel calibration is unchanged at 174 of 176, 0 unexplained.
- **Codex's 3 Oct records:** the verification notes and the roadmap note were committed as written.

## How it was checked
- **Frames:** sheets read paragraph by paragraph for the 13 new videos, f01, and m01, m05 and m12 of the
  re-renders.
- **Spreadsheet figures:** each one asserted against the answer key (`sheets.py`).
- **Builds:** `npm run build` passed for Kestrel Learn (lesson checker plus types), the Workbench UI and the Studio.
- **Browser, against the running Workbench:**
  - the Learn button goes to `/kestrel/`;
  - Kestrel Learn's top-bar links are right;
  - the Studio's Code Atlas link is right;
  - the Atlas shows 10 stops and 22 lessons, the code drawers open, the colouring works, and there are
    no script or security errors.
- **Tests:** 25 server and manual tests and 6 estimates tests passed. The **full suite was not run** (James
  stopped that run).

## Not checked / open
- **Not checked:**
  - no video was watched end to end with sound;
  - no second-agent check of the finished videos other than f01;
  - frames of m08–m11, m13 and f01 after the final re-render.
- **Streamlit:**
  - its address isn't recorded in the repo, and the live page wasn't opened;
  - there, the Code Atlas link goes to the private claude.ai page, which others can't open unless it's
    shared.
- **From the manual review, left for later:**
  - the glossary's blocker-code table is missing 5 codes, and 3 listed codes can't fire;
  - the API still carries a "partner" role label for older records;
  - the chapters don't mention either.
- **Possible software bugs, not investigated:**
  - the six hand-prepared files are all labelled "from the QuickBooks export";
  - going concern uses the current ratio before adjustments;
  - a recipe version change turns every page red.

  (The Jo Kestrel wording one is fixed.)
- **The Studio home** (flow map, Harborline case) is old. James liked its first visual and thinks it could
  be used elsewhere in the system: parking-lot idea, not started.
- **Internal audit module:** discussed, not started. Recommendation: build it as a layer on the shared
  engine, not a copy or a new system. Not yet in the roadmap.

## What went wrong this session (for the next agent)
- **Planning:** the Codex prompt written on 3 Oct listed six steps and no single deliverable, and Codex
  produced no video. `START-HERE.md` now enforces one deliverable per session.
- **Wrong assumptions about where James works:**
  - the Learn links were added to an app the desktop link doesn't open;
  - a desktop "Noesi Learn.bat" was created without asking (removed);
  - the Workbench's Studio button first pointed at the flow map.

  **Rule:** James works from the desktop "Noesi Workbench" link. Check what that link opens before
  changing or adding any link.
- **Communication:** fixes were made and pushed without telling James first, and James had to stop the
  work. **Rule:** say what will change before changing it.

## How to use it (James)
- **Start:** the desktop "Noesi Workbench", then **Learn ↗** for the Kestrel course with its 22 videos.
- **The documents:** use Manual, How Noesi works and Code Atlas in the course's top bar, or the
  Workbench's "📖 manual".
- **Learning:** go in module order, and do each "By hand" step yourself before opening the key.
- **Video work:** start from `komposos-labs-videos/noesi_learn_videos/kestrel/START-HERE.md`.
