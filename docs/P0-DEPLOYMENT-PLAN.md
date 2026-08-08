# P0 deployment plan — from teaching instrument to system of record

The independent review (2026-08-07) drew the honest line: usable today for
teaching and research; **not a system of record or the basis of an issued
opinion** until the platform gaps close. This is the plan for closing
them. It sequences the work; it does not start it. The trigger is James
saying *pilot → real users*.

The plan leans on the one architectural decision made for exactly this
moment: `WorkbenchService` and everything below it (domain, procedures,
persistence spine) do not change. Every arc replaces an *adapter* around
that core — the HTTP boundary, the key store, the storage layer — so the
audit logic the review could not break is never reopened.

Tracker references are to `PRODUCTION-READINESS.md`.

## Arc order and rationale

Ordered by dependency, not severity: identities before keys (keys must
bind to authenticated people), keys before encryption (something must
hold the data keys), platform before retention (you archive what finally
exists). Trusted time goes **first** despite its P1 label because it is
the smallest arc and strengthens every lock and packet already being
produced.

### Arc 1 — Trusted time (tracker 1.3) — small

Every signature today proves "when" only by the local clock, and the
packet says so in-band. Add an RFC 3161 timestamp authority
countersignature over the lock digest and the packet digest at signing
time; store the TSA token alongside the signature so packets verify
offline, including the timestamp. Two independent TSAs configurable;
refusal to reach one is a *named* degradation recorded in the manifest,
never a silent fallback.

**Exit:** a packet's independent verifier proves not just *which key over
which bytes* but *no later than when* — and the in-band limits text is
rewritten to claim exactly that much and no more.

### Arc 2 — Per-person authentication (tracker 1.1) — large

The pilot's one-token-many-chairs model is honest role-play; real users
need real sessions. Swap the stdlib HTTP module for the planned
ASGI/FastAPI boundary; one authenticated session per human (passkeys
preferred, OIDC/SSO where a firm brings it); a principal directory maps
identities to the same principal ids the domain already journals. Chair
switching is deleted in the hosted profile — a request acts as the person
who authenticated, full stop. Separation-of-duties gates change *not at
all*: they already treat principals as people.

**Exit:** two humans on two machines complete an engagement end to end;
every journal row binds to an authenticated session; the `--principal`
flag and `X-Acting-Principal` header exist only in the local
teaching profile, clearly labeled.

### Arc 3 — Key custody (tracker 1.2) — medium

Signing keys currently live as PEM files in a local directory. Bind keys
to the authenticated person from Arc 2: OS keystore (DPAPI/Keychain) for
the local profile, KMS/HSM for hosted. Add rotation and revocation with a
re-signing policy. Verification of old packets survives rotation by
construction — public material already travels in-band — and a test
proves it against packets sealed before the migration.

**Exit:** no private key readable as a file on disk; a rotated key
verifies old packets and signs new ones; revocation is journaled.

### Arc 4 — Encryption at rest (tracker 5.1) — medium

Client data is confidential (AICPA ET 1.700). Encrypt the control DB
(SQLCipher or equivalent) and envelope-encrypt vault blobs with data keys
held by Arc 3's custody layer. Interim milestone, honestly labeled:
full-disk encryption with a documented boundary ("protects a stolen
disk, not a live session") ships first if the application layer slips.

**Exit:** a cold read of the data directory yields no plaintext client
data; digest verification and packet export behave identically; the
recovery path (Arc 5) is tested against encrypted stores.

### Arc 5 — Retention, archive, and disaster recovery (tracker 2.1, 2.3) — medium

Nothing is deletable *through the app*, but the OS owner can delete
everything. On lock, ship an archive unit — packet, DB snapshot, vault
blobs — to WORM/object-lock storage with a retention schedule (5 years
AICPA AU-C 230, 7 years PCAOB AS 1215, longer where a state board says
so) and a legal-hold override. Write and *rehearse* the restore runbook;
the design already enforces honesty here — a restored DB without its
vault fails digest verification — so the drill proves DB, vault, and
keys restore together. Document RPO/RTO.

**Exit:** a locked engagement deleted from the working machine is fully
restored from archive and its packet re-verifies offline; retention
cannot be shortened from inside the app.

## Cross-cutting rules

- **The limits text never lies mid-arc.** Every packet states in-band
  what its signatures do and do not prove; each arc updates that text
  the moment the claim strengthens, and not a commit sooner.
- **Each arc ends with an independent review pass** scoped to the arc
  (`docs/INDEPENDENT-REVIEW.md` arrangement), and the whole plan ends
  with a full re-review whose verdict should upgrade the "must not be
  used yet" line. The plan is done when the *reviewer* says the line
  moved, not when the builder does.
- **The teaching profile survives.** Local single-operator mode, chair
  switching and all, remains the classroom configuration — clearly
  labeled, never the deployed one.
- **Out of scope here:** EQR role, workflow-edit review, XLSX ingestion,
  scale work — tracked as P1/P2; nothing in this plan blocks them.

## Standing risks this plan does not remove

Signatures will still not prove the accounting source was complete or
authentic; procedures still test what the data supports and refuse the
rest. Those are permanent properties of the honest design, stated in
every packet, and no platform arc changes them.
