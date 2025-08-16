# I2C Sensor Software Refactor Plan (Simplified)

## Goals
- Separate concerns into clear layers: hardware access, configuration, deserialization, semantics, and orchestration.
- Centralize configuration (single source of truth).
- Maximize unit testability; keep HIL optional and unaffected.
- **Keep it simple**: Start minimal, add complexity only when needed.

## Scope
- Refactor current `hardware/mcp23017.py`, `hardware/mygpio.py`, `sensor_monitor.py`.
- Introduce minimal new modules: `models.py`, `interfaces.py`, `configuration_manager.py`, `hardware_access.py`, `deserializer.py`, `semantic_mapper.py`, `event_manager.py`.

## Out of Scope (for now)
- `pipeline_manager.py` (optional in architecture doc)
- Separate directories for deserializer/semantic_mapper
- Complex config view classes (`HardwareConfig`/`ParsingConfig`/`SemanticConfig`)
- Multiple error types beyond `I2CError`
- Async rewrite or analytics integrations

## Phases

### Phase 1 — Foundations & Hardware Isolation
- Create `models.py`: `SensorReading`, `Event`, `I2CError`.
- Create `interfaces.py`: `I2CReader`, `SensorDeserializer`, `SemanticMapper`, `EventManager`.
- Create `configuration_manager.py`: load single config dict from `config.json`.
- Create `hardware_access.py`: concrete `I2CReader` using `smbus2`.
- Refactor `hardware/mcp23017.py` → thin device adapter (injected `I2CReader`, uses config).
- Refactor `hardware/mygpio.py` → pure INT GPIO handler.
- Add `config.json` skeleton.
- DoD: HIL smoke test passes; unit tests for config manager and adapters.

### Phase 2 — Processing & Orchestration
- Create `deserializer.py`: parse MCP23017 port bytes to `SensorReading`.
- Create `semantic_mapper.py`: map readings to domain `Event`s.
- Replace `sensor_monitor.py` with `event_manager.py`: queue management and orchestration.
- DoD: End-to-end flow works (INT → read → deserialize → map → enqueue).

## Migration Strategy
- Introduce new modules alongside existing ones.
- Keep current HIL tests passing throughout.
- Migrate `sensor_monitor.py` last, directly (no compatibility shim).
- Read env vars via `configuration_manager` to avoid drift.

## File Structure (Final)
```
hsec/
├── models.py                    # SensorReading, Event, I2CError
├── interfaces.py                # Protocols
├── configuration_manager.py     # Config loading
├── hardware_access.py           # I2CReader impl
├── deserializer.py             # Raw bytes → SensorReading
├── semantic_mapper.py          # SensorReading → Event
├── event_manager.py            # Queue + orchestration
├── config.json                 # Configuration
├── hardware/
│   ├── mcp23017.py            # Device adapter (refactored)
│   └── mygpio.py              # INT GPIO handler (refactored)
└── tests/
    ├── unit/                  # New modules
    ├── integration/           # End-to-end with mocks
    └── hardware/              # HIL (opt-in)
```

## Testing Plan
- **Unit**: models, config manager, deserializer, semantic mapper, event manager.
- **Integration**: pipeline with mocks, error propagation.
- **HIL** (`-m hardware`): MCP23017 INT behavior, end-to-end events.
- **uv groups**: `test` (pytest, ruff), `hardware` (gpiozero, smbus2).

## Checklist
- [ ] models.py
- [ ] interfaces.py  
- [ ] configuration_manager.py + config.json
- [ ] hardware_access.py
- [ ] hardware/mcp23017.py (refactor)
- [ ] hardware/mygpio.py (refactor)
- [ ] deserializer.py
- [ ] semantic_mapper.py
- [ ] event_manager.py (replace sensor_monitor.py)
- [ ] Tests updated
- [ ] pyproject.toml: optional hardware deps

## Success Criteria
- Clean separation of concerns
- Config-driven behavior
- All tests pass (unit/integration by default, HIL opt-in)
- No regression in current functionality
- Foundation for future complexity if needed
