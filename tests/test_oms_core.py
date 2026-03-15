import unittest

from tools.oms_core import OrderManager, OrderStatus, RiskEngine, RiskLimits, Side


class OmsCoreTests(unittest.TestCase):
    def _manager(self) -> OrderManager:
        limits = RiskLimits(
            max_order_qty=10.0,
            max_order_notional=20_000.0,
            max_net_position=15.0,
            fat_finger_bps=100.0,
        )
        return OrderManager(risk_engine=RiskEngine(limits), reference_price=100.0)

    def test_rejects_order_when_notional_exceeds_limit(self):
        om = self._manager()
        order = om.submit_order(symbol="BTCUSDT", side=Side.BUY, price=5000.0, qty=5.0)
        self.assertEqual(order.status, OrderStatus.REJECTED)
        self.assertIn("max_order_notional", order.reject_reason)

    def test_valid_order_lifecycle_and_position_update(self):
        om = self._manager()
        order = om.submit_order(symbol="BTCUSDT", side=Side.BUY, price=100.0, qty=4.0)

        self.assertEqual(order.status, OrderStatus.PENDING_NEW)

        om.apply_event(order.order_id, "ack")
        self.assertEqual(order.status, OrderStatus.ACKED)

        om.apply_event(order.order_id, "partial_fill", fill_qty=1.5)
        self.assertEqual(order.status, OrderStatus.PARTIALLY_FILLED)
        self.assertAlmostEqual(order.filled_qty, 1.5)
        self.assertAlmostEqual(om.position, 1.5)

        om.apply_event(order.order_id, "fill")
        self.assertEqual(order.status, OrderStatus.FILLED)
        self.assertAlmostEqual(order.filled_qty, 4.0)
        self.assertAlmostEqual(om.position, 4.0)

    def test_invalid_transition_raises(self):
        om = self._manager()
        order = om.submit_order(symbol="BTCUSDT", side=Side.SELL, price=100.0, qty=2.0)

        with self.assertRaises(ValueError):
            om.apply_event(order.order_id, "partial_fill", fill_qty=1.0)

    def test_terminal_order_rejects_new_event(self):
        om = self._manager()
        order = om.submit_order(symbol="BTCUSDT", side=Side.BUY, price=100.0, qty=1.0)
        om.apply_event(order.order_id, "ack")
        om.apply_event(order.order_id, "fill")

        with self.assertRaises(ValueError):
            om.apply_event(order.order_id, "cancel")


if __name__ == "__main__":
    unittest.main()
