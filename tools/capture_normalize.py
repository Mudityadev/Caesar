#!/usr/bin/env python3
"""Capture raw feed, normalize events, and produce quality metrics."""

from __future__ import annotations

import argparse
import json
import time
import sys
from collections import defaultdict
from pathlib import Path

REQUIRED_FIELDS = {
    "venue",
    "symbol",
    "event_type",
    "sequence",
    "exchange_ts_ns",
    "best_bid",
    "best_ask",
    "bid_size",
    "ask_size",
    "trade_price",
    "trade_size",
    "side",
}


def normalize_event(event: dict) -> dict:
    missing = REQUIRED_FIELDS - set(event)
    if missing:
        raise ValueError(f"missing fields: {sorted(missing)}")

    return {
        "venue": str(event["venue"]),
        "symbol": str(event["symbol"]),
        "event_type": str(event["event_type"]),
        "sequence": int(event["sequence"]),
        "exchange_ts_ns": int(event["exchange_ts_ns"]),
        "ingest_ts_ns": time.monotonic_ns(),
        "best_bid": float(event["best_bid"]),
        "best_ask": float(event["best_ask"]),
        "bid_size": float(event["bid_size"]),
        "ask_size": float(event["ask_size"]),
        "trade_price": None if event["trade_price"] is None else float(event["trade_price"]),
        "trade_size": None if event["trade_size"] is None else float(event["trade_size"]),
        "side": event["side"],
    }


def process_stream(lines, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_path = out_dir / "raw.jsonl"
    normalized_path = out_dir / "normalized.jsonl"

    last_seq = {}
    gap_count = defaultdict(int)
    total_events = 0
    parse_errors = 0

    with raw_path.open("w", encoding="utf-8") as raw_f, normalized_path.open("w", encoding="utf-8") as norm_f:
        for line in lines:
            line = line.strip()
            if not line:
                continue

            raw_f.write(line + "\n")

            try:
                event = json.loads(line)
                normalized = normalize_event(event)
            except Exception:
                parse_errors += 1
                continue

            key = (normalized["venue"], normalized["symbol"])
            prev_seq = last_seq.get(key)
            if prev_seq is not None and normalized["sequence"] != prev_seq + 1:
                gap_count[f"{key[0]}:{key[1]}"] += 1
            last_seq[key] = normalized["sequence"]

            norm_f.write(json.dumps(normalized, separators=(",", ":")) + "\n")
            total_events += 1

    quality_report = {
        "total_events": total_events,
        "parse_errors": parse_errors,
        "gap_count": dict(gap_count),
        "feeds_tracked": len(last_seq),
    }

    (out_dir / "quality_report.json").write_text(
        json.dumps(quality_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return quality_report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="./artifacts")
    args = parser.parse_args()

    process_stream(lines=sys.stdin, out_dir=Path(args.out_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
