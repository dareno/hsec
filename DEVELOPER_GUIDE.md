# Developer Guide: I2C Sensor Refactor

## Purpose
This guide explains the **why** and **how** behind each step in our refactor plan. You'll learn the Python patterns, language features, and architectural principles that make this codebase maintainable and testable.
Normative system specs live in `docs/`; this guide describes how to work with them (process, tooling, coding patterns).

## Where to find what

| Document                                               | Purpose                                           | Use when                                             |
|:-------------------------------------------------------|:--------------------------------------------------|:-----------------------------------------------------|
| [Context Map](docs/04-context-map.md)                  | Bounded contexts, responsibilities, relationships | Scoping changes; checking cross-context links        |
| [Domain Model](docs/05-domain-model.md)                | Ubiquitous language; entities/VOs/services/events | Naming; modeling behavior/events                      |
| [Architecture Overview](docs/06-architecture-overview.md) | High-level structure, layering, component index   | Navigating architecture; see 07/08 for details       |
| [Interface Contracts](docs/07-interface-contracts.md)  | Wire-level details (hardware, schemas, OPA, versions) | Integrating/validating interfaces                |
| [Runtime Flows](docs/08-runtime-flows.md)              | Sequences and timing                              | Understanding runtime interactions                     |
| [Testing Strategy](docs/09-testing-strategy.md)        | Test types, markers, env, commands                | Running tests; hardware is opt-in                      |
| [Release Plan](docs/03-release-plan.md)                | Priorities and story backlog with FR traceability | Planning work; referencing FR/Story IDs               |
| [Product Vision](docs/01-project-vision.md)            | North star and goals                              | Validating alignment                                   |
| [Product Requirements](docs/02-product-requirements.md)| Functional requirements and acceptance criteria    | Deriving stories; validating behavior                  |
| [Requirements Traceability](docs/10-requirements-traceability.md) | Requirement→design/tests mapping               | Verifying coverage/compliance                          |
| [ADRs](docs/adr/)                                      | Decision records (options, decision, consequences) | Making/revisiting architectural decisions              |

## Core Concepts

### 1. Protocol-Based Design (Duck Typing with Type Safety)

**What it is**: Python's `Protocol` class (from `typing`) lets you define interfaces without inheritance. Any class that implements the required methods automatically satisfies the protocol.

**Why we use it**: 
- **Testability**: Easy to create mock objects for testing
- **Loose coupling**: Components depend on interfaces, not concrete classes
- **Flexibility**: Multiple implementations without inheritance hierarchies

**Example**:
```python
from typing import Protocol

class I2CReader(Protocol):
    def read_register(self, address: int) -> bytes: ...
    def write_register(self, address: int, data: bytes) -> None: ...

# Any class with these methods satisfies I2CReader
class MockI2CReader:
    def read_register(self, address: int) -> bytes:
        return b'\x42'  # Mock data
    
    def write_register(self, address: int, data: bytes) -> None:
        pass  # Mock implementation

# Type checker knows this is valid
def use_reader(reader: I2CReader):
    data = reader.read_register(0x20)  # Works with any I2CReader
```

### 2. Dependency Injection

**What it is**: Instead of creating dependencies inside a class, you pass them in from outside.

**Why we use it**:
- **Testing**: Inject mocks instead of real hardware
- **Flexibility**: Swap implementations without changing code
- **Single Responsibility**: Classes focus on their job, not creating dependencies

**Before (tightly coupled)**:
```python
class MCP23017:
    def __init__(self):
        self.bus = smbus2.SMBus(1)  # Hard-coded dependency
```

**After (dependency injection)**:
```python
class MCP23017:
    def __init__(self, i2c_reader: I2CReader):
        self.i2c_reader = i2c_reader  # Injected dependency
```

### 3. Dataclasses for Data Transfer Objects (DTOs)

**What it is**: `@dataclass` decorator automatically generates `__init__`, `__repr__`, `__eq__` methods.

**Why we use it**:
- **Less boilerplate**: No manual `__init__` writing
- **Type hints**: Built-in support for type checking
- **Immutability**: Use `frozen=True` for immutable objects
- **Clear data contracts**: Explicit field definitions

**Example**:
```python
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)  # Immutable
class SensorReading:
    sensor_id: str
    value: float
    timestamp: float
    metadata: Optional[dict] = None

# Usage
reading = SensorReading("door_1", 1.0, 1234567890.0)
print(reading)  # SensorReading(sensor_id='door_1', value=1.0, ...)
```

### 4. Configuration as Code

**What it is**: Centralize all configuration in a single, structured format (JSON/YAML).

**Why we use it**:
- **Single source of truth**: No scattered magic numbers or env vars
- **Environment-specific**: Different configs for dev/test/production
- **Validation**: Catch config errors early
- **Documentation**: Config structure documents system capabilities

**Pattern**:
```python
# config.json
{
  "i2c": {
    "bus": 1,
    "mcp23017_address": "0x20"
  },
  "sensors": {
    "door_1": {
      "pin": 0,
      "threshold": 0.5,
      "debounce_ms": 50
    }
  }
}

# configuration_manager.py
class ConfigurationManager:
    def __init__(self, config_path: str):
        with open(config_path) as f:
            self._config = json.load(f)
    
    def get_i2c_config(self) -> dict:
        return self._config["i2c"]
```

## Step-by-Step Breakdown

### Phase 1: Foundations & Hardware Isolation

#### Step 1: `models.py` - Data Structures
**Purpose**: Define the data that flows through our system.

**Key concepts**:
- **Dataclasses**: Automatic method generation
- **Type hints**: Runtime and static type checking
- **Immutability**: `frozen=True` prevents accidental modification

**Why this matters**: Clear data contracts prevent bugs and make the system easier to understand.

```python
@dataclass(frozen=True)
class SensorReading:
    sensor_id: str      # Which sensor
    value: float        # Raw or processed value
    timestamp: float    # When it was read
```

#### Step 2: `interfaces.py` - Contracts
**Purpose**: Define what each component must do, without specifying how.

**Key concepts**:
- **Protocols**: Interface definitions without inheritance
- **Abstract methods**: `...` indicates "implement this"
- **Type annotations**: Document expected inputs/outputs

**Why this matters**: Interfaces let you test components in isolation and swap implementations.

```python
class SensorDeserializer(Protocol):
    def parse_sensor_data(self, raw_data: bytes) -> SensorReading: ...
    # Any class with this method signature satisfies the protocol
```

#### Step 3: `configuration_manager.py` - Centralized Config
**Purpose**: Single place to load and access all configuration.

**Key concepts**:
- **JSON loading**: `json.load()` for structured data
- **Error handling**: Validate config and provide helpful errors
- **Encapsulation**: Hide config structure from other modules

**Why this matters**: Eliminates scattered magic numbers and makes the system configurable.

#### Step 4: `hardware_access.py` - I2C Abstraction
**Purpose**: Thin wrapper around `smbus2` that implements our `I2CReader` protocol.

**Key concepts**:
- **Protocol implementation**: Concrete class that satisfies interface
- **Error translation**: Convert `smbus2` exceptions to our `I2CError`
- **Resource management**: Handle I2C bus lifecycle

**Why this matters**: Isolates hardware dependencies and enables testing without real hardware.

#### Step 5: Refactor `hardware/mcp23017.py` - Device Adapter
**Purpose**: Transform from a monolithic class to a focused device adapter.

**Key changes**:
- **Dependency injection**: Accept `I2CReader` instead of creating `smbus2.SMBus`
- **Single responsibility**: Only MCP23017-specific logic, no queues or GPIO
- **Configuration-driven**: Use injected config instead of hardcoded values

**Pattern**:
```python
class MCP23017:
    def __init__(self, i2c_reader: I2CReader, config: dict):
        self.i2c_reader = i2c_reader
        self.address = config["address"]
    
    def read_ports(self) -> tuple[int, int]:
        # Device-specific logic only
        port_a = self.i2c_reader.read_register(self.address, 0x12)
        port_b = self.i2c_reader.read_register(self.address, 0x13)
        return port_a[0], port_b[0]
```

#### Step 6: Refactor `hardware/mygpio.py` - Pure GPIO Handler
**Purpose**: Handle only GPIO interrupt line, nothing else.

**Key changes**:
- **Single responsibility**: Only GPIO setup and callback invocation
- **Callback pattern**: Accept a function to call when interrupt occurs
- **No I2C knowledge**: Doesn't know about MCP23017 or sensors

### Phase 2: Processing & Orchestration

#### Step 7: `deserializer.py` - Raw Data Processing
**Purpose**: Convert raw bytes into structured `SensorReading` objects.

**Key concepts**:
- **Bit manipulation**: Extract meaningful data from raw bytes
- **Configuration-driven parsing**: Use config to define bit masks, scaling
- **Error handling**: Validate input and handle malformed data

**Pattern**:
```python
class MCP23017Deserializer:
    def parse_sensor_data(self, raw_data: bytes) -> SensorReading:
        # Extract bits, apply scaling, create SensorReading
        port_a, port_b = raw_data[0], raw_data[1]
        door_state = (port_a & 0x01) == 0  # Bit 0, inverted logic
        return SensorReading("door_1", float(door_state), time.time())
```

#### Step 8: `semantic_mapper.py` - Business Logic
**Purpose**: Transform sensor readings into meaningful domain events.

**Key concepts**:
- **State tracking**: Remember previous values to detect changes
- **Business rules**: Apply thresholds, debouncing, validation
- **Event generation**: Create domain-specific events

**Pattern**:
```python
class DoorMapper:
    def __init__(self):
        self.previous_state = {}
    
    def map_to_event(self, reading: SensorReading) -> Optional[Event]:
        # Detect state changes and generate events
        if self._state_changed(reading):
            return Event("door_state_change", reading.sensor_id, 
                        {"new_state": reading.value})
        return None
```

#### Step 9: `event_manager.py` - Orchestration
**Purpose**: Coordinate the entire pipeline and manage the event queue.

**Key concepts**:
- **Queue management**: Thread-safe event queuing
- **Pipeline coordination**: Wire together all components
- **Error handling**: Catch and handle errors from any layer

**Pattern**:
```python
class EventManager:
    def __init__(self, deserializer: SensorDeserializer, 
                 mapper: SemanticMapper):
        self.queue = queue.Queue()
        self.deserializer = deserializer
        self.mapper = mapper
    
    def process_interrupt(self, raw_data: bytes):
        # Pipeline: raw data → reading → event → queue
        reading = self.deserializer.parse_sensor_data(raw_data)
        event = self.mapper.map_to_event(reading)
        if event:
            self.queue.put(event)
```

## Testing Strategy

## Test-Driven Development (TDD) Workflow

- **Principle (always-on for code changes)**: New or changed behavior starts with a failing test, implement the minimal code to pass, then refactor.
- **Scope**: Applies to changes under `src/`, `hardware/`, and top-level application components (Sensor Monitor, Event Processor). Docs-only edits are excluded.
- **Definition of Done**:
  - Failing test written that expresses the acceptance criteria or unit contract.
  - Minimal implementation makes tests pass; no out-of-scope features.
  - Refactor and keep tests green; ensure coverage for edge cases relevant to the story.
  - Traceability: commits/PR reference FR and Story IDs (see `docs/03-release-plan.md`).
- **Test organization/execution**: See `docs/09-testing-strategy.md` for directory layout, markers, and commands.

### Unit Tests
**Purpose**: Test individual components in isolation.

**Key techniques**:
- **Mocking**: Use mock objects that implement protocols
- **Synthetic data**: Create test data without hardware
- **Edge cases**: Test error conditions and boundary values

```python
def test_deserializer():
    deserializer = MCP23017Deserializer()
    raw_data = b'\x01\x00'  # Synthetic data
    reading = deserializer.parse_sensor_data(raw_data)
    assert reading.sensor_id == "door_1"
    assert reading.value == 1.0
```

### Integration Tests
**Purpose**: Test component interactions with mocked dependencies.

**Key techniques**:
- **Mock injection**: Inject mocks that behave like real components
- **End-to-end flow**: Test complete pipeline with synthetic data
- **Error propagation**: Verify errors are handled correctly

### Hardware-in-Loop (HIL) Tests
**Purpose**: Test with real hardware (optional, marked with `@pytest.mark.hardware`). Manual HIL that needs operator actions are also marked `@pytest.mark.manual`.

**Key techniques**:
- **Environment detection**: Skip if hardware not available
- **Pytest markers**:
  - Only hardware: `pytest -m hardware`
  - Automatic HIL (no operator): `pytest -m 'hardware and not manual'`
  - Manual HIL (operator-driven): `pytest -m 'hardware and manual'`
- **Safety checks**: Verify hardware state before testing

**Output capture for manual tests**:
- Tests marked `manual` automatically disable PyTest's output capture so prompts/prints are shown live when running multiple tests. This is handled by `_show_output_for_manual_tests` in `conftest.py`.
- If you still don't see prompts due to environment/plugins, run with `-s` as a fallback: `pytest -m 'hardware and manual' -s`.

### Manual sequence helpers (HIL)

To reduce duplication and standardize operator prompts, manual HIL tests use shared helpers in `tests/hardware/fixtures/devices.py`:

- `run_reed_edge_sequence(dev, pi_int_button, bit_index, location, port='A', open_timeout_s=..., close_timeout_s=..., quiet_lead_s=...)`
- `run_pir_motion_sequence(dev, pi_int_button, bit_index, location, port='A', motion_timeout_s=..., settle_timeout_s=..., quiet_lead_s=...)`

Both helpers delegate to a common internal `_run_toggle_sequence()` and share the same defaults:

- `DEFAULT_FIRST_TIMEOUT_S = 90.0` (phase 1 window)
- `DEFAULT_SECOND_TIMEOUT_S = 90.0` (phase 2 window)
- `DEFAULT_QUIET_LEAD_S = 3.0` seconds

Notes:

- `quiet_lead_s` provides a brief calm period before baseline capture to avoid capturing a transient as the baseline (particularly helpful around motion sensors). It's harmless for reed tests and can be left at the default.
- Timeouts can be overridden per-test if the physical device exhibits slower behavior.
- PIR helper does not use any countdown; prompts are concise and consistent with the reed helper.

## Benefits of This Architecture

1. **Testability**: Each component can be tested independently
2. **Maintainability**: Clear separation of concerns
3. **Flexibility**: Easy to swap implementations or add features
4. **Debuggability**: Errors are isolated to specific layers
5. **Documentation**: Interfaces serve as contracts and documentation

## Common Pitfalls to Avoid

1. **Circular imports**: Keep dependencies flowing in one direction
2. **Leaky abstractions**: Don't let hardware details leak into business logic
3. **Over-engineering**: Start simple, add complexity only when needed
4. **Tight coupling**: Always depend on interfaces, not concrete classes
5. **Missing error handling**: Every layer should handle its own error cases

## Next Steps

Once you understand these concepts, you'll be ready to implement the refactor step by step. Each component builds on the previous ones, creating a clean, maintainable architecture that's easy to test and extend.


## Doc-change protocol

Purpose: Keep docs the source of truth and in sync with the evolving domain. Apply BEFORE code when the domain model or boundaries change.

### When to trigger
- Changes to entities, value objects, domain services, domain events, aggregates/repositories
- Changes to bounded contexts, integration contracts, layering/dependency rules, or diagram structure

### Documents to update (in this order)
1) Context Map
   - Bounded contexts, ownership (core/supporting), upstream/downstream, integration patterns (e.g., ACL)
2) Domain Model
   - Ubiquitous language and model narrative; diagrams (entities/VOs/services/events/aggregates)
   - Clarify which repository interfaces live in the domain (aggregates only)
3) Architecture Overview
   - Layering (Application, Domain, Infrastructure, ACL, UI) inside the core BC
   - Dependency rules and code placement conventions
   - Component Index (bridging code): update IDs ↔ primary code paths for diagrammed components
   - Diagrams render cleanly (Mermaid guardrails below)
4) ADR (new or update)
   - Decision, options, rationale, consequences; link to updated sections

### Layering & dependency rules (normative)
- Domain: depends on nothing (no imports from Application/Infrastructure/ACL/UI)
- Application: may depend on Domain and ACL ports/types; not on Infrastructure
- ACL: may depend on Hardware BC and Domain types; Domain must not depend on ACL
- Infrastructure: may depend on Application/Domain to implement their interfaces; Domain/Application do not depend on Infrastructure
- UI/Presenter: depends on Application DTOs/services; avoid reaching into Domain internals directly

### Code placement conventions
- Application: orchestration and presenters (e.g., monitor/event loop, view-model builders)
- Domain: entities, value objects, domain services, domain events, repository interfaces (aggregates)
- ACL: translators/mappers (e.g., mapping config, port map, deserializers)
- Infrastructure: concrete adapters (I/O, persistence, logging)
- Supporting BCs (e.g., hardware): chip/wiring-centric code and contracts

### Mermaid diagram guardrails
- Begin diagrams with: `%%{init: {"layout":"elk"}}%%` and `graph TD` (or LR)
- Quote subgraph titles when they contain parentheses: `subgraph SECBC["Security BC (core)"]`
- Use solid arrows for data, dashed for dependency (document legend if used)
- Close every `subgraph ... end`; connect edges to nodes (not subgraph IDs)
 - Do not embed file paths in diagram nodes; use friendly names (optionally with `[Component ID]`)

### Component IDs and code breadcrumbs
- ID convention: `BC.Layer.Component` (e.g., `SEC.APP.SensorMonitor`, `HW.Drv.MCP23017`). Keep IDs stable.
- Breadcrumbs in code: add a one-liner at the top of mapped modules/classes: `# Arch: <Component ID>`.
- Mapping lives in the Architecture Overview's Component Index. Avoid duplicating paths elsewhere.

### Required outputs (per change)
- Diffs for Context Map, Domain Model, Architecture Overview, Interface Contracts, and ADR
- One-sentence “why” per document (traceability)
- Validation checklist (see below)
- Brief list of test impacts (unit/integration/hardware)
- Component Index updated for affected components
- Breadcrumbs added/updated in code for affected Component IDs

### Validation checklist
- Names/IDs/states consistent across all docs
- Diagrams render without errors
- Dependency rules respected (no domain → app/infra/acl imports)
- Product vision/requirements unchanged; inconsistencies flagged
 - Each Component ID in the Component Index is present in code via a breadcrumb comment `# Arch: <ID>`

### PR description template (copy/paste)
```
Summary: <1–2 lines of the domain/boundary change>
Traceability: links to updated sections in Context Map, Domain Model, Architecture Overview, ADR
Validation: [ ] names consistent; [ ] diagrams render; [ ] deps OK; [ ] repo placement OK
Tests: unit/integration/hardware impacts and planned updates
Out of scope: what this PR intentionally does not change
```

### ADR template (copy/paste)
```
# <Decision title>
- Context: short problem statement and constraints
- Options considered: A/B/C with pros/cons
- Decision: chosen option and why
- Consequences: trade-offs and follow-ups
- Links: updated doc sections and related PRs
```

## Resolution & Citation

- Resolution order: resolve by frontmatter `doc_type` → conventional path → title match.
- Citation style: cite the resolved file path and the relevant section (heading and/or line range).
- Identifier usage: PRD citations use plain terms; Domain Model/Interface Contracts use exact identifiers.
- Examples:
  - PRD: `docs/02-product-requirements.md` › “FR7: Sensor Data Processing”
  - Domain Model: `docs/05-domain-model.md` › “Ubiquitous Language”
  - Interface Contracts: `docs/07-interface-contracts.md` › “Events › Alarm”

## Environment & Tooling (uv + ruff + pytest)

We use Astral uv for dependency and environment management. Dependencies are
organized into groups so you can install only what a task needs:

- **Base runtime**: defined under `[project].dependencies` (minimal runtime only)
- **dev**: developer tools (linters/formatters, e.g., `ruff`)
- **test**: test framework and plugins (e.g., `pytest`)
- **hardware**: optional hardware-in-loop dependencies (e.g., `gpiozero`, `lgpio`)

Example configuration (in `pyproject.toml`):

```toml
[dependency-groups]
dev = [
  "ruff",
]
test = [
  "pytest>=8.0",
  "pytest-cov>=4.0",
  "pytest-mock>=3.10",
  "pytest-xdist>=3.0",
]
hardware = [
  "gpiozero>=2.0",
  "lgpio",
]

[tool.ruff]
line-length = 88
```

Common commands:

- **Install dev tools**: `uv sync --group dev`
- **Install test tools**: `uv sync --group test`
- **Install HIL tools**: `uv sync --group test --group hardware`
- **Run linter**: `uv run ruff check .`
- **Format (code only)**: `uv run ruff format .`
- **Run tests (default excludes hardware)**: `uv run pytest`
- **Run only hardware tests**: `uv run pytest -m hardware`

CI suggestion:

- Lint job: `uv sync --group dev` then `uv run ruff check .`
- Unit test job: `uv sync --group test` then `uv run pytest -m 'not hardware'`
- HIL job: `uv sync --group test --group hardware` then `uv run pytest -m hardware`

## CLI: Port Status Watcher (`hsec-status`)

A lightweight CLI to continuously read and display MCP23017 port states with optional labels. Intended for lab bring-up and quick diagnostics.

- **Entry point**: console script `hsec-status`
- **Refresh interval**: defaults to 0.5s (configurable)
- **Displays**: `gpaX`/`gpbX` with interpreted state per sensor type

Environment variables (defaults align with HIL fixtures in `tests/hardware/conftest.py`):

- `HSEC_I2C_BUS`: I2C bus number (default `1`)
- `HSEC_MCP23017_ADDR`: I2C address (default `0x20`)
- `HSEC_PORTS_TOML`: optional path to a TOML config for port metadata

Usage examples:

```bash
# Install deps (base runtime includes smbus2)
uv sync

# Run with defaults (bus=1, addr=0x20), clear screen between updates
uv run hsec-status --clear

# Override bus/address and interval
uv run hsec-status --bus 1 --addr 0x20 --interval 0.25

# Provide explicit ports config
uv run hsec-status --config ./hsec.ports.toml
```

TOML configuration (optional):

```toml
# hsec.ports.toml
[ports]
gpa1 = { type = "pir",  label = "hallway PIR" }
gpa3 = { type = "reed", label = "kitchen door" }
gpa4 = { type = "reed", label = "family room door" }
gpa6 = { type = "reed", label = "front door" }
gpa7 = { type = "reed", label = "basement door" }
gpb7 = { type = "reed", label = "main bedroom windows" }
```

Lookup order for ports config:

- `--config` if provided
- `$HSEC_PORTS_TOML` if set
- `./hsec.ports.toml`
- `~/.config/hsec/ports.toml`
- Built-in defaults matching common HIL wiring

Notes:

- The CLI reads GPIO levels directly via `hardware/mcp23017.MCP23017.read_ports()`; no interrupt setup is required for polling.
- PIR levels render as `motion`/`no motion`; reed/contact render as `open`/`closed`.
