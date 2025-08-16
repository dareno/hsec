---
doc_type: domain_model
upstream:
  - 02-product-requirements.md
  - 03-context-map.md
---
# Order Context Specification

## Roles and Responsibilities
| Role              | Responsibilities |
|-------------------|-----------------|
| Software Architect | Lead: Define ubiquitous language, entities, value objects, operations, and invariants. |
| Product Manager   | Input: Validate terms and responsibilities align with business intent. |
| Stakeholders      | Input: Confirm domain terms reflect business processes. |

## Upstream Documents
- Project Vision (01-project-vision.md)
- Product Requirements Document (02-product-requirements.md)
- Context Map (03-context-map.md)

## Downstream Documents
- None (leads to implementation).

## Ubiquitous Language
- **Order**: Customer purchase with items, total amount, and status (PENDING, CONFIRMED).
- **Money**: Amount and currency (e.g., 100.00 USD).
- **Discount**: Percentage reduction (0 to 1).
- **OrderId**: Unique identifier for an order.
- **CustomerId**: Unique identifier for a customer.

## Domain Model
- **Entities**:
  - Order: Identified by OrderId, includes Money (total), CustomerId, status.
- **Value Objects**:
  - Money: Amount and currency.
  - Discount: Percentage (0 to 1).
- **Operations**:
  - Create Order: Initializes with OrderId, CustomerId, total.
  - Apply Discount: Reduces total by percentage.
  - Confirm Order: Sets status to CONFIRMED, publishes `OrderConfirmed` event.
- **Invariants**:
  - Total must be non-negative.
  - Status transitions: PENDING → CONFIRMED or CANCELLED.

## Implementation Notes (DDD Boundaries)
- `src/order_context/model.py` contains immutable entities/value objects only (`@dataclass(frozen=True, slots=True)`).
- No policy checks, event creation, or time acquisition in the model.
- Use cases are implemented in `src/order_context/operations.py` and:
  - Accept/return model types (`Order`, `Money`, `Discount`).
  - Invoke policy decision points via injected adapters (OPA).
  - Create domain events (`OrderConfirmed`) and use an injected clock for timestamps.
- Domain events are defined in `src/order_context/events.py`.

## Policy Traceability (OPA)
- Invariants → OPA rules
  - Total non-negative → `policy.order.validation.total_non_negative`
  - Status transitions allowed → `policy.order.validation.status_transition_allowed`
  - Discount bounds (0–100%) → `policy.order.validation.discount_allowed`
- Operations → Decision rules
  - Create Order → `policy.order.validation.create_allowed`
  - Apply Discount → `policy.order.validation.discount_allowed`
  - Confirm Order → `policy.order.validation.confirm_allowed`

## Decision Points (PEPs)
- Before Create Order: evaluate `policy.order.validation.create_allowed`
- Before Apply Discount: evaluate `policy.order.validation.discount_allowed`
- Before Confirm Order: evaluate `policy.order.validation.confirm_allowed`

## Policy Decision API (summary)
- Input keys: `operation`, `actor`, `resource.{order, discount}`, `context`
- Output keys: `allow`, `violations[]`
- Violations: machine-readable codes mapped to domain errors