# Learn the audit — Streamlit host

Hosts Noesi's ten-lesson audit course, the documents page and the course map
on Streamlit. The pages are static; nothing here talks to a Noesi server.

**Streamlit Community Cloud settings**

| Field | Value |
|---|---|
| Repository | `Jayhawk314/noesi-assurance` |
| Branch | the branch that contains this folder |
| Main file path | `apps/learn-streamlit/streamlit_app.py` |

Streamlit installs `requirements.txt` from this folder.

**Updating the course.** `learn.html` is a build product. After changing
lessons or pages in `apps/studio-ui`:

```
cd apps/studio-ui
npm run build
node scripts/build-learn-standalone.mjs
```

then commit the regenerated `learn.html`.

**Run locally:** `pip install streamlit`, then
`streamlit run apps/learn-streamlit/streamlit_app.py`.
