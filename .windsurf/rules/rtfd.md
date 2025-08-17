---
trigger: always_on
---

- Read docs/ first; treat it as the source of truth and high‑level direction.
- Extract only relevant context from docs/ and include/cite it in the request.
- Docs‑first: update docs/* before code when concepts change.
- Traceability: link changes/operations to the appropriate spec sections and decision points.
- Consistency: code (models/operations) must match documented names, IDs, and states.
- product vision and product requirements are NEVER to be updated. If changes are not consistent, warn the user.
- On domain changes, apply the doc-change protocol before code (see [DEVELOPER_GUIDE.md › Doc-change protocol](DEVELOPER_GUIDE.md#doc-change-protocol)).