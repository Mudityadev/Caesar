# Phase 1 Build Start (Weeks 1-4)

This repository now starts **Phase 1** for a latency-first HFT MVP.

## Scope for Phase 1
- Single normalized market-data schema.
- Deterministic capture pipeline with local monotonic timestamps.
- Sequence-gap detection and quality report generation.
- Raw + normalized data persistence in JSONL.
- Deterministic replay input compatibility.

## Deliverables included here
1. `tools/mock_feed.py`
   - Generates deterministic mock L2-like tick events for local development.
2. `tools/capture_normalize.py`
   - Consumes newline-delimited JSON tick events.
   - Applies normalization and strict schema fields.
   - Adds ingest timestamp (`ingest_ts_ns`) using `time.monotonic_ns()`.
   - Detects sequence gaps per symbol.
   - Emits:
     - `raw.jsonl`
     - `normalized.jsonl`
     - `quality_report.json`
3. Unit tests for normalization and gap tracking.

## Quick start
```bash
python3 tools/mock_feed.py --events 20 | python3 tools/capture_normalize.py --out-dir ./artifacts
```

Then inspect:
- `artifacts/raw.jsonl`
- `artifacts/normalized.jsonl`
- `artifacts/quality_report.json`

## Why this is Phase-1 aligned
This establishes the first low-latency data path contract and quality instrumentation needed before strategy/OMS work starts.
