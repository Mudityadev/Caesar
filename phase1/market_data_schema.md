# Normalized Market Data Schema (Phase 1)

Each normalized record in `normalized.jsonl` uses this schema:

```json
{
  "venue": "string",
  "symbol": "string",
  "event_type": "book_update|trade",
  "sequence": 123,
  "exchange_ts_ns": 1700000000000000000,
  "ingest_ts_ns": 1700000000000009999,
  "best_bid": 100.12,
  "best_ask": 100.15,
  "bid_size": 2.0,
  "ask_size": 1.0,
  "trade_price": null,
  "trade_size": null,
  "side": null
}
```

## Notes
- `ingest_ts_ns` is assigned on receipt to support tick-to-decision latency baselining.
- `sequence` continuity is tracked per `(venue, symbol)`.
- Any sequence jump increments `gap_count` in the quality report.
