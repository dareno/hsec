---
trigger: glob
globs: */operations.py
---

- Implement use cases that compose model.py types.
- Accept/return model instances; avoid in-place mutation—return new instances.
- Orchestrate via injected ports/repos/UoW; no infrastructure details inline.
- Delegate policy to adapters (OPA) using policy.<context>.validation.*.
- Name functions in ubiquitous language (e.g., confirm_order, cancel_order)