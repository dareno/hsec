# I2C Sensor Software Architecture

## Initial Prompt
In the context of software engineering and device drivers, this architecture document outlines a Python3-based system for reading a custom circuit via I2C using the `smbus2` library. The system reads registers on the device to establish the hardware state of sensors. It includes configuration to provide semantic meaning to the readings and tracks state changes to understand sensor behavior. The architecture emphasizes a clear separation between the hardware layer and layers that add semantic meaning to the hardware readings. A deserializer layer converts raw register data into structured sensor readings, followed by a layer that transforms these readings into meaningful domain events. An event manager orchestrates the pipeline, coordinating multiple deserializers and placing their events into a common queue. The design aims to be idiomatic, use clear naming, follow common patterns, and avoid unnecessary complexity. Serialization is not required, as the system focuses solely on reading and processing sensor data.

## Overview
The system follows a pipeline architecture to process raw I2C register data into structured sensor readings, transform them into semantic events, and enqueue these events for downstream consumption. The architecture is modular, loosely coupled, and testable, using Python's protocol-based interfaces to define component boundaries. It is designed to support multiple sensors while maintaining simplicity and clarity.

### Core Data Flow
Raw I2C register data → Structured sensor readings → Semantic events → Event queue

## Components

### 1. Hardware Access Layer (HAL)
- **Module Name**: `hardware_access`
- **Interface**: `I2CReader`
- **Responsibility**: Handles low-level I2C communication using the `smbus2` library to read raw register bytes from the device.
- **Inputs**: I2C addresses and register layouts from `HardwareConfig`.
- **Outputs**: Raw bytes from specified registers.
- **Error Handling**: Raises `I2CError` for communication failures (e.g., bus errors, timeouts).
- **Dependencies**: `smbus2` library, `HardwareConfig` from `configuration_manager`.

### 2. Configuration Manager
- **Module Name**: `configuration_manager`
- **Responsibility**: Centralizes configuration data and provides tailored views for different layers.
- **Configuration Views**:
  - **HardwareConfig**: Defines I2C addresses and register layouts (e.g., register offsets, sizes).
  - **ParsingConfig**: Specifies data types, scaling factors, and bit masks for parsing raw bytes into structured readings.
  - **SemanticConfig**: Defines thresholds, event rules, and labels for mapping readings to domain events.
- **Implementation Notes**:
  - Configurations are loaded from a static JSON file (e.g., `config.json`) with sections for each view.
  - Each view is exposed as a distinct interface to ensure layers only access relevant configuration.
- **Error Handling**: Raises `ConfigurationError` for invalid or missing configuration data.
- **Dependencies**: None (standalone module).

### 3. Deserializer Layer
- **Module Name**: `deserializer`
- **Interface**: `SensorDeserializer`
- **Responsibility**: Converts raw register bytes into structured `SensorReading` objects using `ParsingConfig`.
- **Inputs**: Raw bytes from `I2CReader`, `ParsingConfig` from `configuration_manager`.
- **Outputs**: `SensorReading` objects (e.g., with fields like `sensor_id`, `value`, `timestamp`).
- **Error Handling**: Raises `DeserializationError` for invalid or malformed raw data.
- **Dependencies**: `hardware_access` (`I2CReader`), `configuration_manager` (`ParsingConfig`).

### 4. Semantic Mapping Layer
- **Module Name**: `semantic_mapper`
- **Interface**: `SemanticMapper`
- **Responsibility**: Transforms `SensorReading` objects into meaningful domain events based on `SemanticConfig`.
- **Inputs**: `SensorReading` objects from `SensorDeserializer`, `SemanticConfig` from `configuration_manager`.
- **Outputs**: `Event` objects (e.g., with fields like `event_type`, `sensor_id`, `data`) or `None` if no event is triggered.
- **Error Handling**: Returns `None` or an `ErrorEvent` for invalid readings or rule violations.
- **Dependencies**: `deserializer` (`SensorDeserializer`), `configuration_manager` (`SemanticConfig`).

### 5. Event Manager
- **Module Name**: `event_manager`
- **Interface**: `EventManager`
- **Responsibility**: Orchestrates the pipeline by coordinating multiple `SensorDeserializer` instances, collecting events from `SemanticMapper`, and managing a common event queue for downstream consumers.
- **Inputs**: Events from `SemanticMapper`.
- **Outputs**: Enqueues events to a thread-safe queue (e.g., `queue.Queue`) for processing by consumers.
- **Implementation Notes**:
  - Manages a single event queue to decouple event producers from consumers.
  - Supports multiple sensors by coordinating their deserializers and mappers.
  - Optionally supports polling schedules for sensor reads (configured via `configuration_manager`).
- **Error Handling**: Enqueues `ErrorEvent` objects for errors propagated from lower layers (e.g., `I2CError`, `DeserializationError`).
- **Dependencies**: `semantic_mapper` (`SemanticMapper`), Python `queue` module.

### 6. Pipeline Manager (Optional)
- **Module Name**: `pipeline_manager`
- **Responsibility**: Initializes and coordinates the pipeline, including sensor instances, polling schedules, and data flow through the layers.
- **Inputs**: Configurations from `configuration_manager`, instances of `I2CReader`, `SensorDeserializer`, and `SemanticMapper`.
- **Outputs**: Passes data through the pipeline to the `EventManager`.
- **Implementation Notes**:
  - Optional component to separate pipeline orchestration from event queue management.
  - Useful for complex systems with multiple sensors or varying polling intervals.
- **Error Handling**: Logs errors and may trigger system-wide error handling (e.g., restarting failed sensors).
- **Dependencies**: All other modules (`hardware_access`, `configuration_manager`, `deserializer`, `semantic_mapper`, `event_manager`).

## Protocol Interfaces
The following protocol interfaces define the contracts between components, ensuring loose coupling and testability. These are implemented in Python using `typing.Protocol`.

- **Data Structures**:
  - **SensorReading**: A dataclass object with fields like `sensor_id: str`, `value: float`, `timestamp: float`. Represents a structured sensor reading.
  - **Event**: A dataclass object with fields like `event_type: str`, `sensor_id: str`, `data: dict`. Represents a meaningful domain event.

- **I2CReader** (Module: `hardware_access`):
  - `read_register(address: int) -> bytes`: Reads raw bytes from the specified I2C register.
  - `write_register(address: int, data: bytes) -> None`: Writes bytes to the specified register (optional, for device configuration).

- **SensorDeserializer** (Module: `deserializer`):
  - `parse_sensor_data(raw_data: bytes) -> SensorReading`: Converts raw bytes into a structured `SensorReading` object.

- **SemanticMapper** (Module: `semantic_mapper`):
  - `map_to_event(reading: SensorReading) -> Optional[Event]`: Maps a `SensorReading` to a domain event or `None` if no event is triggered.

- **EventManager** (Module: `event_manager`):
  - `enqueue_event(event: Event) -> None`: Adds an event to the queue.
  - `process_queue() -> None`: Processes queued events for downstream consumers.

## Key Principles
- **Loose Coupling**: Each layer depends only on protocol interfaces, not concrete implementations, enabling easy mocking for testing.
- **Single Responsibility**: Each component has a clear, focused role (I/O, parsing, semantic mapping, orchestration).
- **Configuration-Driven**: The `configuration_manager` centralizes configuration, providing tailored views to each layer to avoid tight coupling.
- **Error Handling**: Errors are explicitly handled at each layer (e.g., `I2CError`, `DeserializationError`, `ErrorEvent`) and propagated to the `event_manager` for logging or enqueuing.
- **Testability**: Protocol-based design allows unit testing of each layer by mocking dependencies.
- **Simplicity**: The architecture avoids unnecessary abstractions, focusing on a clear pipeline suitable for a Python-based I2C sensor system.

## Error Handling
- **I2CReader**: Raises `I2CError` for communication failures (e.g., bus errors, device timeouts).
- **SensorDeserializer**: Raises `DeserializationError` for invalid or malformed raw data.
- **SemanticMapper**: Returns `None` or an `ErrorEvent` for invalid readings or rule violations.
- **EventManager**: Enqueues `ErrorEvent` objects for errors from lower layers and logs critical failures.
- **ConfigurationManager**: Raises `ConfigurationError` for invalid or missing configuration data.
- **PipelineManager** (if used): Logs errors and may implement recovery strategies (e.g., reinitializing failed sensors).

## Extensibility
- **Multiple Sensors**: The `event_manager` and optional `pipeline_manager` support multiple sensors by coordinating multiple `SensorDeserializer` and `SemanticMapper` instances, each configured via `configuration_manager`.
- **Configuration Scalability**: The `configuration_manager` supports unique configurations per sensor using a dictionary of sensor IDs to configs.
- **Queue Consumers**: The event queue allows flexible integration with downstream systems (e.g., logging, analytics, or UI updates).

## Implementation Notes
- **Configuration Loading**: Use a JSON file (e.g., `config.json`) with sections for `HardwareConfig`, `ParsingConfig`, and `SemanticConfig`. Example structure:
  ```json
  {
    "sensors": {
      "sensor1": {
        "hardware": { "address": 0x68, "registers": [...] },
        "parsing": { "data_types": [...], "scaling": [...] },
        "semantic": { "thresholds": [...], "event_rules": [...] }
      }
    }
  }
  ```
- **Dataclasses**: Use Python's `dataclasses` module to define `SensorReading` and `Event` data structures. This reduces boilerplate code, improves readability, and leverages type hints for clarity without adding external dependencies.
- **Concurrency**: Use a thread-safe queue (`queue.Queue`) in `event_manager` for simplicity. If asynchronous operation is needed, consider `asyncio.Queue`.
- **Polling vs. Interrupts**: The `pipeline_manager` (if used) can implement polling schedules or react to hardware interrupts, configured via `HardwareConfig`.
- **Dependencies**: Use Python standard libraries (`queue`, `typing`, `dataclasses`) and `smbus2` for I2C communication. Avoid heavy frameworks to keep the system lightweight.

## Example Protocol Structure
The following protocols define the interfaces for key components, ensuring consistency and testability:

```python
from dataclasses import dataclass
from typing import Protocol, Optional

@dataclass
class SensorReading:
    sensor_id: str
    value: float
    timestamp: float

@dataclass
class Event:
    event_type: str
    sensor_id: str
    data: dict

class I2CReader(Protocol):
    def read_register(self, address: int) -> bytes: ...
    def write_register(self, address: int, data: bytes) -> None: ...

class SensorDeserializer(Protocol):
    def parse_sensor_data(self, raw_data: bytes) -> SensorReading: ...

class SemanticMapper(Protocol):
    def map_to_event(self, reading: SensorReading) -> Optional[Event]: ...

class EventManager(Protocol):
    def enqueue_event(self, event: Event) -> None: ...
    def process_queue(self) -> None: ...
```

## Usage
This architecture serves as a blueprint for implementing a Python3-based I2C sensor system. Developers can use the module names, interfaces, and data flow to structure their code. The `configuration_manager` loads sensor-specific configurations, the `hardware_access` module reads raw data, the `deserializer` converts it to structured readings, the `semantic_mapper` generates domain events, and the `event_manager` handles event queuing. The optional `pipeline_manager` can be added for complex systems with multiple sensors or custom polling logic.