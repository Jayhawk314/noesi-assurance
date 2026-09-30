# Learn the audit on Kestrel — Streamlit host

Hosts Noesi's Kestrel Valley course (docs/LEARN-KESTREL-PLAN.md): one module
per audit area, each in four steps (the idea, by hand, in Noesi, compare with
the key), the documents page, "Follow a number", "Excel for audit" and the
course map. The pages are static; nothing here talks to a
Noesi server. The Harborline course (`apps/learn-streamlit`) is a separate
app at its own address and is unchanged.

**Streamlit Community Cloud settings** (a second app)

| Field | Value |
|---|---|
| Repository | `Jayhawk314/noesi-assurance` |
| Branch | the branch that contains this folder |
| Main file path | `apps/learn-kestrel-streamlit/streamlit_app.py` |

Streamlit installs `requirements.txt` from this folder.

**Updating the course.** `learn.html` is a build product. After changing
lessons in `apps/learn-kestrel-ui`, or after the Kestrel answer key or the
Workbench changes:

```
.venv\Scripts\python case-studies\kestrel-valley-cycle\instructor\finish_line_check.py
.venv\Scripts\python apps\learn-kestrel-ui\scripts\export_key.py
.venv\Scripts\python apps\learn-kestrel-ui\scripts\export_records.py
cd apps/learn-kestrel-ui
npm run build
node scripts/build-learn-standalone.mjs
```

then commit the regenerated `src/learn/kestrel-key.json`,
`src/learn/kestrel-records.json` and `learn.html`.
`export_key.py` refuses if any figure differs from FINISH-LINE-REPORT.md;
`npm run build` refuses a lesson whose answers or numbers the key does not hold.

**Run locally:** `pip install streamlit`, then
`streamlit run apps/learn-kestrel-streamlit/streamlit_app.py`.
