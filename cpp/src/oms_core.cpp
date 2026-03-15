#include "hft/oms_core.hpp"

#include <cmath>
#include <stdexcept>

namespace hft {

RiskEngine::RiskEngine(RiskLimits limits) : limits_(limits) {}

RiskResult RiskEngine::Validate(Side side,
                                double price,
                                double qty,
                                double current_position,
                                double reference_price) const {
  if (qty <= 0) {
    return {false, "qty must be positive"};
  }
  if (qty > limits_.max_order_qty) {
    return {false, "max_order_qty exceeded"};
  }

  const double notional = price * qty;
  if (notional > limits_.max_order_notional) {
    return {false, "max_order_notional exceeded"};
  }

  const double projected = current_position + (side == Side::Buy ? qty : -qty);
  if (std::abs(projected) > limits_.max_net_position) {
    return {false, "max_net_position exceeded"};
  }

  if (reference_price <= 0) {
    return {false, "invalid reference price"};
  }

  const double deviation_bps = std::abs(price - reference_price) / reference_price * 10000.0;
  if (deviation_bps > limits_.fat_finger_bps) {
    return {false, "fat_finger band exceeded"};
  }

  return {true, std::nullopt};
}

OrderManager::OrderManager(RiskEngine risk_engine, double reference_price)
    : risk_engine_(std::move(risk_engine)), reference_price_(reference_price) {
  if (reference_price_ <= 0) {
    throw std::invalid_argument("reference_price must be positive");
  }
}

Order& OrderManager::SubmitOrder(const std::string& symbol, Side side, double price, double qty) {
  ++seq_;
  const std::string order_id = "ord-" + std::to_string(seq_);

  Order order{.order_id = order_id,
              .symbol = symbol,
              .side = side,
              .price = price,
              .qty = qty,
              .status = OrderStatus::PendingNew,
              .filled_qty = 0.0,
              .reject_reason = std::nullopt};

  const RiskResult risk_result = risk_engine_.Validate(side, price, qty, position_, reference_price_);
  if (!risk_result.accepted) {
    order.status = OrderStatus::Rejected;
    order.reject_reason = risk_result.reason;
  }

  auto [it, _] = orders_.emplace(order_id, std::move(order));
  return it->second;
}

Order& OrderManager::ApplyEvent(const std::string& order_id, const std::string& event, double fill_qty) {
  auto it = orders_.find(order_id);
  if (it == orders_.end()) {
    throw std::out_of_range("unknown order_id: " + order_id);
  }

  Order& order = it->second;
  if (IsTerminal(order.status)) {
    throw std::logic_error("cannot apply event to terminal order");
  }

  if (event == "ack") {
    if (order.status != OrderStatus::PendingNew) {
      throw std::logic_error("ack requires PendingNew");
    }
    order.status = OrderStatus::Acked;
    return order;
  }

  if (event == "partial_fill") {
    if (order.status != OrderStatus::Acked && order.status != OrderStatus::PartiallyFilled) {
      throw std::logic_error("partial_fill requires Acked/PartiallyFilled");
    }
    ApplyFill(order, fill_qty);
    order.status = order.filled_qty < order.qty ? OrderStatus::PartiallyFilled : OrderStatus::Filled;
    return order;
  }

  if (event == "fill") {
    if (order.status != OrderStatus::Acked && order.status != OrderStatus::PartiallyFilled) {
      throw std::logic_error("fill requires Acked/PartiallyFilled");
    }
    ApplyFill(order, order.qty - order.filled_qty);
    order.status = OrderStatus::Filled;
    return order;
  }

  if (event == "cancel") {
    order.status = OrderStatus::Canceled;
    return order;
  }

  if (event == "reject") {
    order.status = OrderStatus::Rejected;
    if (!order.reject_reason.has_value()) {
      order.reject_reason = "exchange reject";
    }
    return order;
  }

  throw std::invalid_argument("unknown event: " + event);
}

bool OrderManager::IsTerminal(OrderStatus status) {
  return status == OrderStatus::Filled || status == OrderStatus::Canceled || status == OrderStatus::Rejected;
}

void OrderManager::ApplyFill(Order& order, double fill_qty) {
  if (fill_qty <= 0) {
    throw std::invalid_argument("fill_qty must be positive");
  }
  if (order.filled_qty + fill_qty > order.qty) {
    throw std::logic_error("overfill");
  }

  order.filled_qty += fill_qty;
  const double signed_fill = order.side == Side::Buy ? fill_qty : -fill_qty;
  position_ += signed_fill;
}

}  // namespace hft
