Noesi Assurance · manual supplement · Kestrel walk-through

# Audit Code Atlas

Ten stops, one audit. At each stop: the audit question, what you do in Excel, the Noesi screen, and the route the request takes through the code, from the screen down to the record. Click any function to read its real source, with the lines that matter highlighted. Each stop ends with the maths and with what that stop can't establish.

Tap a layer to hide it. Use "Walk this stop" to step through a stop's code in order.

Your idea · receipts for the system's own process

## A run sheet: Noesi's own lab-book page, printed by the machine

Most of this is already built. Every run freezes a **job manifest** before it executes: the procedure, the engine version, a SHA-256 and row count for each input table, and every policy value in force. The job ID is the hash of all of that (). Before running, re-checks that the tables still match those hashes, and the result gets its own digest (). So the system already keeps a receipt of its own process. It just never shows it to you as a page.

### What a run sheet would print

RUN SHEET ar.confirmations_mus · rerun 0 job job|4be1…9c07 result 7f2a…e1d0 engine cycles-v2 → procedures_cycles/receivables.py:273 confirmations_mus → sampling.mus_evaluate inputs AR_listing 212 rows sha256 9d1c… Confirmations 38 rows sha256 03be… dials ar_tolerable_misstatement 36,000 ar_risk_incorrect_acceptance 0.05 mus_interval 9,400 verdicts AGREE 1 · CLASH 2 receipts 3 · each re-hashes in verify_packet limits Overstatement bound only; understatements are listed separately.

Invented figures. The policy names are the procedure's real required policies; the limits line is its contract's own text (procedures_cycles/contracts.py).

### The variable tweaks (dials)

already takes per-run policy values on top of the engagement's, and already reruns procedures in memory and compares findings without recording anything. Put the two together and you get a **sensitivity sheet**: "at 10% risk of incorrect acceptance instead of 5%, which findings change, and does the evaluation still exceed tolerable?"

**One design rule I'd hold firm on:** a what-if must never land in the engagement record. A real run is journalled and exported, so a run made only to explore would read as a test you performed. Copy the pattern of revision_impact, which reruns in memory and records nothing. The what-if is computed, shown and printable, and never sealed.

### How this ties your three ideas together

1. **This atlas is the static half.** It shows where the code is at each stop, and it's the same for every audit.
2. **The run sheet is the live half.** It shows which code ran on your data, with which dials, and what it found. Print one per stop as you do Kestrel and it becomes a lab-book page you didn't have to write.
3. **Receipt-based reports** (fraud leads, untested areas, everything about existence) are run sheets filtered by a question.

Suggested order: the working paper's leftover "Approved" wording (stop 10) was fixed on 3 Oct. Then do Kestrel by hand with this atlas open. Then build the run sheet (read-only, from the manifest already stored), then in-memory what-ifs, then question-filtered reports. A run sheet proves the computation was recorded consistently. It doesn't prove the client's data was real or complete.