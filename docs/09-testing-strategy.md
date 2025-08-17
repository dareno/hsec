---
doc_type: testing_guide
upstream:
  - 06-architecture-overview.md
  - 04-context-map.md
  - pyproject.toml
---

# Testing Strategy

## Organization

```
tests/
├── unit/              # Pure logic tests (no hardware)
├── integration/       # Software-only integration
└── hardware/          # Hardware-in-loop (HIL)
    ├── conftest.py    # HIL fixtures, env config, safety checks
    ├── fixtures/      # Shared hardware utilities
    ├── mcp23017/      # Device-specific tests
    └── gpio/          # Pi GPIO INT line tests
```

## Pytest Configuration

- Default excludes hardware tests via marker.
- See `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-m 'not hardware'"
markers = [
    "hardware: marks tests requiring real hardware (HIL)",
]
```

## Dependencies (uv)

- Default: `uv sync --group test`
- HIL: `uv sync --group test --group hardware`

## Hardware Configuration

- Env vars: `HSEC_I2C_BUS`, `HSEC_MCP23017_ADDR`, `HSEC_INT_GPIO`
- Auto-detect Pi/I2C availability with clear skip messages
- Generous timeouts and debouncing for hardware paths

## Execution

- Unit+integration (default): `uv run pytest`
- Hardware only: `uv run pytest -m hardware`
- Mixed by path: `uv run pytest tests/unit tests/integration`

## Seams

- Unit: edge detection and state tracking (pure functions)
- Integration: mock `hardware/mcp23017.py` and `hardware/mygpio.py` into Sensor Monitor + Event Processor components (planned)
- HIL: validate I2C+GPIO end-to-end (interrupt clearing on both ports; loopback wiring)

## Related

- Architecture: `docs/06-architecture-overview.md`
- Runtime Flows: `docs/08-runtime-flows.md`
- Interfaces: `docs/07-interface-contracts.md`
