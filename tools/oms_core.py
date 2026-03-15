#!/usr/bin/env python3
"""Phase 2 OMS core with pre-trade risk checks and deterministic transitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(str, Enum):
    PENDING_NEW = "PENDING_NEW"
    ACKED = "ACKED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"


TERMINAL_STATUSES = {OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.REJECTED}


@dataclass(frozen=True)
class RiskLimits:
    max_order_qty: float
    max_order_notional: float
    max_net_position: float
    fat_finger_bps: float


@dataclass
class Order:
    order_id: str
    symbol: str
    side: Side
    price: float
    qty: float
    status: OrderStatus = OrderStatus.PENDING_NEW
    filled_qty: float = 0.0
    reject_reason: Optional[str] = None


@dataclass
class RiskResult:
    accepted: bool
    reason: Optional[str] = None


@dataclass
class RiskEngine:
    limits: RiskLimits

    def validate(self, *, side: Side, price: float, qty: float, current_position: float, reference_price: float) -> RiskResult:
        if qty <= 0:
            return RiskResult(False, "qty must be positive")

        if qty > self.limits.max_order_qty:
            return RiskResult(False, "max_order_qty exceeded")

        notional = price * qty
        if notional > self.limits.max_order_notional:
            return RiskResult(False, "max_order_notional exceeded")

        projected_position = current_position + (qty if side == Side.BUY else -qty)
        if abs(projected_position) > self.limits.max_net_position:
            return RiskResult(False, "max_net_position exceeded")

        deviation_bps = abs(price - reference_price) / reference_price * 10_000
        if deviation_bps > self.limits.fat_finger_bps:
            return RiskResult(False, "fat_finger band exceeded")

        return RiskResult(True)


@dataclass
class OrderManager:
    risk_engine: RiskEngine
    reference_price: float
    position: float = 0.0
    _seq: int = 0
    orders: dict[str, Order] = field(default_factory=dict)

    def submit_order(self, *, symbol: str, side: Side, price: float, qty: float) -> Order:
        self._seq += 1
        order_id = f"ord-{self._seq}"

        order = Order(order_id=order_id, symbol=symbol, side=side, price=price, qty=qty)

        result = self.risk_engine.validate(
            side=side,
            price=price,
            qty=qty,
            current_position=self.position,
            reference_price=self.reference_price,
        )
        if not result.accepted:
            order.status = OrderStatus.REJECTED
            order.reject_reason = result.reason
            self.orders[order_id] = order
            return order

        self.orders[order_id] = order
        return order

    def apply_event(self, order_id: str, event: str, fill_qty: float = 0.0) -> Order:
        if order_id not in self.orders:
            raise KeyError(f"unknown order_id: {order_id}")

        order = self.orders[order_id]
        if order.status in TERMINAL_STATUSES:
            raise ValueError(f"cannot apply event {event} to terminal order {order.status}")

        if event == "ack":
            if order.status != OrderStatus.PENDING_NEW:
                raise ValueError("ack requires PENDING_NEW")
            order.status = OrderStatus.ACKED
            return order

        if event == "partial_fill":
            if order.status not in {OrderStatus.ACKED, OrderStatus.PARTIALLY_FILLED}:
                raise ValueError("partial_fill requires ACKED or PARTIALLY_FILLED")
            self._apply_fill(order, fill_qty)
            if order.filled_qty < order.qty:
                order.status = OrderStatus.PARTIALLY_FILLED
            else:
                order.status = OrderStatus.FILLED
            return order

        if event == "fill":
            if order.status not in {OrderStatus.ACKED, OrderStatus.PARTIALLY_FILLED}:
                raise ValueError("fill requires ACKED or PARTIALLY_FILLED")
            remaining = order.qty - order.filled_qty
            self._apply_fill(order, remaining)
            order.status = OrderStatus.FILLED
            return order

        if event == "cancel":
            order.status = OrderStatus.CANCELED
            return order

        if event == "reject":
            order.status = OrderStatus.REJECTED
            order.reject_reason = order.reject_reason or "exchange reject"
            return order

        raise ValueError(f"unknown event: {event}")

    def _apply_fill(self, order: Order, fill_qty: float) -> None:
        if fill_qty <= 0:
            raise ValueError("fill_qty must be positive")

        if order.filled_qty + fill_qty > order.qty:
            raise ValueError("overfill")

        order.filled_qty += fill_qty
        signed = fill_qty if order.side == Side.BUY else -fill_qty
        self.position += signed
