#include "hft/oms_core.hpp"

#include <cmath>
#include <iostream>
#include <stdexcept>
#include <string>

namespace {

using hft::OrderManager;
using hft::OrderStatus;
using hft::RiskEngine;
using hft::RiskLimits;
using hft::Side;

void Expect(bool condition, const std::string& message) {
  if (!condition) {
    throw std::runtime_error(message);
  }
}

OrderManager BuildManager() {
  RiskLimits limits{.max_order_qty = 10.0,
                    .max_order_notional = 20000.0,
                    .max_net_position = 15.0,
                    .fat_finger_bps = 100.0};
  return OrderManager(RiskEngine(limits), 100.0);
}

void TestRiskRejection() {
  auto om = BuildManager();
  auto& order = om.SubmitOrder("BTCUSDT", Side::Buy, 5000.0, 5.0);
  Expect(order.status == OrderStatus::Rejected, "expected rejected status");
  Expect(order.reject_reason.has_value(), "expected reject reason");
}

void TestLifecycleAndPosition() {
  auto om = BuildManager();
  auto& order = om.SubmitOrder("BTCUSDT", Side::Buy, 100.0, 4.0);
  Expect(order.status == OrderStatus::PendingNew, "expected pending_new");

  om.ApplyEvent(order.order_id, "ack");
  Expect(order.status == OrderStatus::Acked, "expected acked");

  om.ApplyEvent(order.order_id, "partial_fill", 1.5);
  Expect(order.status == OrderStatus::PartiallyFilled, "expected partially filled");
  Expect(std::abs(order.filled_qty - 1.5) < 1e-9, "expected 1.5 filled_qty");
  Expect(std::abs(om.position() - 1.5) < 1e-9, "expected position 1.5");

  om.ApplyEvent(order.order_id, "fill");
  Expect(order.status == OrderStatus::Filled, "expected filled");
  Expect(std::abs(order.filled_qty - 4.0) < 1e-9, "expected 4.0 filled_qty");
  Expect(std::abs(om.position() - 4.0) < 1e-9, "expected position 4.0");
}

void TestInvalidTransition() {
  auto om = BuildManager();
  auto& order = om.SubmitOrder("BTCUSDT", Side::Sell, 100.0, 2.0);
  bool threw = false;
  try {
    om.ApplyEvent(order.order_id, "partial_fill", 1.0);
  } catch (const std::logic_error&) {
    threw = true;
  }
  Expect(threw, "expected invalid transition to throw");
}

void TestTerminalProtection() {
  auto om = BuildManager();
  auto& order = om.SubmitOrder("BTCUSDT", Side::Buy, 100.0, 1.0);
  om.ApplyEvent(order.order_id, "ack");
  om.ApplyEvent(order.order_id, "fill");

  bool threw = false;
  try {
    om.ApplyEvent(order.order_id, "cancel");
  } catch (const std::logic_error&) {
    threw = true;
  }
  Expect(threw, "expected terminal protection to throw");
}

}  // namespace

int main() {
  try {
    TestRiskRejection();
    TestLifecycleAndPosition();
    TestInvalidTransition();
    TestTerminalProtection();
    std::cout << "All OMS core tests passed\n";
    return 0;
  } catch (const std::exception& ex) {
    std::cerr << "Test failure: " << ex.what() << '\n';
    return 1;
  }
}
