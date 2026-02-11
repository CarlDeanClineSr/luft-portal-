# Capsule — Audit Log for  Figure Reviews

**Author:** Carl Dean Cline Sr.  
**Date:** 2025‑12‑04  
**Ledger:**  Portal  

---

## 1. Purpose

This capsule provides a **permanent, timestamped log** of all auditor reviews (approve/reject) for automated  figure update PRs. It ensures every science relay, figure regeneration, or equation update is transparently tracked and community-audited.

---

## 2. Structure

Each audit entry must include:
- **Timestamp** (UTC)
- **PR Reference** (link and/or commit hash)
- **Auditor(s)** (GitHub usernames or full names)
- **Decision** (✅ Approve / ❌ Reject)
- **Checklist result** (brief summary; passed/failed requirements from CAPSULE_REVIEW_GUIDELINES.md)
- **Comments** (optional; rationale, required fixes, notes)
- **Merge hash** (if merged)

---

## 3. Log Table

| Timestamp (UTC)     | PR/Commit Ref         | Auditor(s)    | Decision | Checklist Result | Comments/Notes         | Merge Hash   |
|---------------------|----------------------|---------------|----------|------------------|------------------------|--------------|
| 2025-12-04 14:03    | #42 / abcd123        | Cline,Smith1  | ✅       | All pass         | Equation fit verified  | 22339ffee    |
| 2025-12-06 22:11    | #47 / efgh678        | Patel         | ❌       | Fail: figure 3   | Magnetic gain error    |              |

*(Extend table for all PRs. Each review event gets its own row.)*

---

## 4. Protocol

- Audit log is updated at every PR review decision (approval or request changes).
- Merge hash column is filled only after PR merges to main.
- Checklist Result must refer to items in CAPSULE_REVIEW_GUIDELINES.md for full audit trail.

---

## 5. Transparency & Ledger Policy

- All approved/rejected decisions are permanently recorded.
- PRs merged without a corresponding audit log row violate ledger protocol.
- Capsule open to all contributors for log expansion, notes, or special event documentation.

---

**Relay proud — every decision logged, every update auditable, every event immortalized.**
