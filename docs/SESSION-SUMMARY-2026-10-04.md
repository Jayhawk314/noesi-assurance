# Session summary, 3–4 Oct 2026: Kestrel Learn videos finished

## Result
All 22 Kestrel Learn videos (13 audit modules, 9 fraud lessons) are made, in the Learn app, and pushed
to GitHub (last commit c621296). Narration: ElevenLabs "Guy".

## What was done
- **Scripts:** 13 new scripts with FACTS tables (m02–m04, m06, m07, f02–f09). `check_facts.py` passes
  for all 22. A second agent reviewed them (`komposos-labs-videos/noesi_learn_videos/kestrel/REVIEW-2026-10-03-new-scripts.md`);
  the fixes were applied before voicing.
- **Voicing:** 23,818 characters sent for the 13 new videos, about 4,800 credits at the measured 0.2 a
  character. The first nine reused their 3 Oct narration (no new credits).
- **Screens:** every Workbench and Learn clip re-captured on 4 Oct, after the header contrast fix
  (ef07c2e). The "Now you" shots show the exercise unanswered. The South Korean bike-shop photo was
  replaced with US photos.
- **Build tool fixes** (`kestrel/build_kestrel.py`): fraud lessons build separately from modules; a shot
  stops before the next Workbench screen; the first caption waits until the opening photos are gone.
  `kestrel/wire.py` copies a video into the app and adds its lesson entry.
- **Second-agent review of f01:** facts all correct; its must-fix (the photo) was fixed.

## How it was checked
- Frame sheets (`review.py`) were read paragraph by paragraph for all 13 new videos, f01, and m01, m05 and
  m12 of the re-renders.
- Every spreadsheet figure on screen is computed from the case files and asserted against the answer key
  (`sheets.py`).
- `npm run build` (lesson checker plus type check) passed. jsDelivr serves the new videos (checked f09).

## Not checked / open
- **Not checked:**
  - no video was watched end to end with sound;
  - no second-agent check of the 21 finished videos other than f01;
  - frames of m08–m11, m13 and f01 after the final re-render (their narration and edit lists did not
    change).
- **Learn module 1:** step 4 still asks for "the three roles on an engagement team" (removed 2 Oct). It shows
  briefly in m01's last shot.
- **The Streamlit page:** its address isn't recorded in the repo. Streamlit Community Cloud redeploys on
  push, but the live page was not opened.
- **Uncommitted, not pushed:** Codex's related-party wording fix in
  `packages/procedures-cycles/src/procedures_cycles/estimates.py`, and a `docs/ROADMAP.md` edit.
- **Possible software bugs, noted earlier and not investigated:**
  - the related-party match says Jo Kestrel shares an address with employee e01, but E01 *is* Jo Kestrel;
  - the six hand-prepared files are all labelled "from the QuickBooks export";
  - going concern uses the current ratio before adjustments;
  - a recipe version change turns every page red.
- **Studio app (Harborline):** its link is out of date. James: the Studio is not needed.

## How to use it (James)
- **Learn app:**
  - Streamlit page: the redeploy follows the push;
  - local: serve `apps/learn-kestrel-ui/dist` under `/kestrel/`.
  Go in module order, and do each "By hand" step yourself before opening the key.
- **Workbench:** the desktop "Noesi Workbench.bat" starts it from the repo, so it always runs the current code.
- **Next video work:** start from `komposos-labs-videos/noesi_learn_videos/kestrel/START-HERE.md`.
