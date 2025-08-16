---
trigger: glob
globs: src/**/*, hardware/**/*, tests/**/*
---

- Practice TDD (see DEVELOPER_GUIDE.md).
- When changing code, ensure a failing test exists first, implement minimal code to pass, then refactor.
- Add or update tests under tests/unit or tests/integration as appropriate.
- Default test runs exclude hardware; mark HIL with @pytest.mark.hardware.
- Traceability: reference FR and Story IDs per docs/02-release-plan.md.
