---
trigger: glob
description: use this to be sure that the model.py files are aligned to the files in docs/ especially docs/*-context-specification.md
globs: */model.py
---

- Align to docs/*; code follows docs, never vice versa (e.g., 04-<context>-context-specification.md, 03-context-map.md).
- Define entities/value objects as immutable dataclasses (frozen=True).
- Use exact ubiquitous language names (types/fields) from the bounded context spec.
- Enforce invariants at construction (e.g., __post_init__); no cross-context logic.
- Include only shared IDs defined in the Context Map.
- No I/O, persistence, policy checks, or orchestration—data structures only