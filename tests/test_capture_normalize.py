import json
import tempfile
import unittest
from pathlib import Path

from tools.capture_normalize import normalize_event, process_stream


class CaptureNormalizeTests(unittest.TestCase):
    def test_normalize_adds_ingest_timestamp(self):
        event = {
            "venue": "BINANCE",
            "symbol": "BTCUSDT",
            "event_type": "book_update",
            "sequence": 1,
            "exchange_ts_ns": 1700000000000000000,
            "best_bid": 100.0,
            "best_ask": 100.02,
            "bid_size": 1.0,
            "ask_size": 2.0,
            "trade_price": None,
            "trade_size": None,
            "side": None,
        }
        normalized = normalize_event(event)
        self.assertIn("ingest_ts_ns", normalized)
        self.assertIsInstance(normalized["ingest_ts_ns"], int)

    def test_gap_count_detected(self):
        lines = [
            json.dumps({
                "venue": "BINANCE",
                "symbol": "BTCUSDT",
                "event_type": "book_update",
                "sequence": 1,
                "exchange_ts_ns": 1700000000000000000,
                "best_bid": 100.0,
                "best_ask": 100.02,
                "bid_size": 1.0,
                "ask_size": 2.0,
                "trade_price": None,
                "trade_size": None,
                "side": None,
            }),
            json.dumps({
                "venue": "BINANCE",
                "symbol": "BTCUSDT",
                "event_type": "book_update",
                "sequence": 3,
                "exchange_ts_ns": 1700000000001000000,
                "best_bid": 100.01,
                "best_ask": 100.03,
                "bid_size": 1.1,
                "ask_size": 2.1,
                "trade_price": None,
                "trade_size": None,
                "side": None,
            }),
        ]

        with tempfile.TemporaryDirectory() as tmp:
            report = process_stream(lines, Path(tmp))
            self.assertEqual(report["total_events"], 2)
            self.assertEqual(report["gap_count"].get("BINANCE:BTCUSDT"), 1)


if __name__ == "__main__":
    unittest.main()
