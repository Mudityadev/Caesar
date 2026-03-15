#!/usr/bin/env python3
"""Generate deterministic newline-delimited JSON market data events."""

from __future__ import annotations

import argparse
import json
import time


def generate_events(count: int, symbol: str, venue: str):
    base_ts = 1_700_000_000_000_000_000
    bid = 100.0
    ask = 100.02

    for seq in range(1, count + 1):
        bid += 0.01 if seq % 2 == 0 else -0.005
        ask = bid + 0.02
        yield {
            "venue": venue,
            "symbol": symbol,
            "event_type": "book_update",
            "sequence": seq,
            "exchange_ts_ns": base_ts + seq * 1_000_000,
            "best_bid": round(bid, 4),
            "best_ask": round(ask, 4),
            "bid_size": float(1 + (seq % 3)),
            "ask_size": float(1 + ((seq + 1) % 3)),
            "trade_price": None,
            "trade_size": None,
            "side": None,
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=int, default=10)
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--venue", default="BINANCE")
    parser.add_argument("--sleep-ms", type=int, default=0)
    args = parser.parse_args()

    for event in generate_events(args.events, args.symbol, args.venue):
        print(json.dumps(event, separators=(",", ":")))
        if args.sleep_ms > 0:
            time.sleep(args.sleep_ms / 1000.0)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
