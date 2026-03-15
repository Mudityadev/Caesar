# Phase 2 Build (Weeks 5-8): Trading Core

Phase 2 introduces an executable **OMS + pre-trade risk gate** foundation to follow the Phase 1 market-data pipeline.

## Scope
- Deterministic order state machine with explicit transition rules.
- Pre-trade risk checks before order acceptance.
- Reject path that records risk reason and blocks unsafe orders.
- Basic exposure tracking through fill events.

## Components
1. `tools/oms_core.py`
   - `RiskLimits`: max order quantity, max notional, max net position, fat-finger band.
   - `RiskEngine`: validates candidate orders against limits and current position.
   - `OrderManager`: creates orders, enforces risk checks, applies exchange-style events (`ack`, `partial_fill`, `fill`, `cancel`, `reject`), and updates position.

2. `tests/test_oms_core.py`
   - Covers risk rejection, valid lifecycle transitions, invalid transitions, and position updates.

## Lifecycle model
`PENDING_NEW -> ACKED -> PARTIALLY_FILLED -> FILLED`

Supported terminal/side transitions:
- Any non-terminal order can move to `CANCELED` on cancel.
- Any non-terminal order can move to `REJECTED` on reject.
- `partial_fill` requires prior `ACKED` or `PARTIALLY_FILLED`.
- `fill` requires prior `ACKED` or `PARTIALLY_FILLED`.

## Why this is latency-aligned
The state machine and risk checks are implemented as in-process Python objects with constant-time checks and no network/database dependency on hot-path validation.
