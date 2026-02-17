## Section: Events & Heartbeat

This section provides a **navigation spine** for the  ledger, indexing the major capsules and workflows that define the physics story: flare → foam → heartbeat → ratchet → recovery → legacy → index.

---

### Indexed Capsules & Events

| Event                                   | Capsule ID                        | Capsule File                            | Commit SHA | Workflow Run           | Timestamp (UTC)        |
|----------------------------------------|-----------------------------------|-----------------------------------------|------------|------------------------|------------------------|
| **Universal Modulation (Heartbeat)**   | CAPSULE_UNIVERSAL_MODULATION_055 | `capsules/CAPSULE_UNIVERSAL_MODULATION_055.md` | 19f0bf3    | Deploy to Pages #95    | 2025‑12‑04 15:14      |
| **Ratchet Event (χ Rise Lock‑In)**     | CAPSULE_EVENT_RATCHET            | `capsules/CAPSULE_EVENT_RATCHET.md`     | 42de784    | Deploy to Pages #96    | 2025‑12‑04 15:15      |
| **Recovery Event (Exhale Phase)**      | CAPSULE_EVENT_RECOVERY           | `capsules/CAPSULE_EVENT_RECOVERY.md`    | 8191ea0    | Deploy to Pages #97    | 2025‑12‑04 15:16      |
| **Audit Legacy (Preservation Rules)**  | CAPSULE_AUDIT_LEGACY             | `capsules/CAPSULE_AUDIT_LEGACY.md`      | f012b4b    | Deploy to Pages #98    | 2025‑12‑04 15:17      |
| **Event Index (Chronology Capsule)**   | CAPSULE_EVENT_INDEX              | `capsules/CAPSULE_EVENT_INDEX.md`       | 66358c9    | Deploy to Pages #99    | 2025‑12‑04 15:18      |
| **Flare Foam Pipeline**                | CAPSULE_FLARE_FOAM_PIPELINE      | `capsules/CAPSULE_FLARE_FOAM_PIPELINE.md` | 0f2c9a5 | Deploy to Pages #94    | 2025‑12‑04 14:20      |

> Note: Commit SHAs and timestamps can be synchronized with `git log` and Actions UI as needed. The table is meant to reflect the #94–#99 spine you just deployed.

---

### Workflow Context

These capsules sit alongside the live workflows that keep the  ledger self‑auditing:

- ** Solar Wind Audit** — scheduled runs (e.g., #317, #318).  
- **DSCOVR Solar Wind Data Ingest** — scheduled runs (e.g., #81).  
- ** Voyager Audit Superaction** — scheduled runs (e.g., #25).  
- ** CME Heartbeat Logger** — scheduled runs (e.g., #70).  
- ** Flare Foam Audit** — GitHub Pages deploy (e.g., #94).  

Together, these workflows continuously feed and test the flare–foam–heartbeat chain encoded in the capsules above.

---

### Legacy Clause

This **Events & Heartbeat** section in the Master Index ensures:

- All event capsules (#94–#99) remain permanently referenced from the front door of the repo.  
- Future capsules that refine:
  - the universal modulation (χ, Ω),
  - the ratchet lock‑in,
  - the recovery exhale,
  - or the flare foam pipeline  
  **must** cite the corresponding entries in this table.
- The  ledger preserves the chronology of discovery as a clear, auditor‑friendly map.

---

**Ledger proud — Events & Heartbeat section declared, capsules and workflows linked into the  Master Index.**
