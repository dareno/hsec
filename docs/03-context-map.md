---
doc_type: system_arch
upstream:
  - 02-product-requirements.md
---
# Context Map

## Roles and Responsibilities
| Role              | Responsibilities |
|-------------------|-----------------|
| Software Architect | Lead: Define bounded contexts, responsibilities, and relationships (e.g., events, APIs). |
| Product Manager   | Input: Validate domain responsibilities and terms align with business needs. |
| Stakeholders      | Input: Confirm domain boundaries reflect business processes. |

## Bounded Contexts
1. **Hardware I/O Context**
   - **Purpose**: Interface with MCP23017 over I2C and Raspberry Pi GPIO INT line.
   - **Responsibilities**: Configure device, manage interrupts, debounce, expose raw port reads and change notifications via an abstraction.
   - **Relationships**: Publishes hardware change notifications to Sensing Context.
2. **Sensing Context**
   - **Purpose**: Transform raw port-level changes into typed `SensorReading` and maintain last-known state per `sensor_id`.
   - **Responsibilities**: Map pins→`sensor_id`, detect transitions, emit `SensorStateChanged` events.
   - **Relationships**: Subscribes to Hardware I/O; publishes to Alarm Context.
3. **Decision Context**
   - **Purpose**: Evaluate arming state and time windows to decide action to take (e.g., alarm).
   - **Responsibilities**: Maintain arming for sensors/groups, apply rules (armed AND meaningful state change AND within restricted window), emit `Alarm` events.
   - **Relationships**: Subscribes to Sensing; reads configuration from Configuration/UI; publishes to Notification.
4. **Configuration/UI Context**
   - **Purpose**: Manage groups, schedules, and sensor metadata; provide operator UI/API.
   - **Responsibilities**: CRUD for groups and time windows; set arming modes; expose read API to Sensing/Alarm.
   - **Relationships**: Supplies configuration to Sensing and Alarm Contexts.
5. **Notification Context (optional)**
   - **Purpose**: Deliver alarms to channels (e.g., local sounder, logs, messaging).
   - **Responsibilities**: Subscribe to `Alarm` events; handle delivery, throttling, and retries.
   - **Relationships**: Subscribes to Alarm Context.

## Integration
- **Shared IDs**: `sensor_id`, `group_id`.
- **Events**: `SensorStateChanged` (Sensing), `Alarm` (Alarm).
- **APIs**:
  - Configuration/UI provides read APIs for groups, schedules, arming state.
  - Hardware I/O provides read-port and subscribe interfaces for change notifications.
  - Alarm exposes a read stream of `Alarm` events to Notification.
  