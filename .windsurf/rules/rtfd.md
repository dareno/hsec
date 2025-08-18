---
trigger: always_on
---

- Source of truth: Read docs/ first; cite files/sections in replies.
- PRD/Vision immutability: Never modify documents with doc_type: prd or doc_type: vision.
- PRD suggestions only: Propose “PRD Suggestions” (anchor, proposed wording, type, rationale, citations). Do not write files unless asked.
- Docs-first: For domain/interface changes, update docs per DEVELOPER_GUIDE.md › Doc-change protocol (Context Map, Domain Model, Architecture Overview, Interface Contracts, ADR) before code.
- UL and naming: PRD uses human terms. Domain Model holds UL + mapping to code/wire. Interface Contracts define exact field names/types. Code must match docs.
- Time semantics: Domain “Instant”; wire ISO-8601 UTC; code UNIX seconds. Avoid encodings in PRD wording.
- Execution mode: Discuss-only by default. Proceed on explicit “Proceed: docs-only” or “Proceed: code+docs”.
- TDD: For code changes, start with tests (see docs/09-testing-strategy.md). Docs-only edits don’t require tests.
- Resolution & citation: Resolve by doc_type; if ambiguous, use conventional path or title; cite file path + section.