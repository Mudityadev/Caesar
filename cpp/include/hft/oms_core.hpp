#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>

namespace hft {

enum class Side {
  Buy,
  Sell,
};

enum class OrderStatus {
  PendingNew,
  Acked,
  PartiallyFilled,
  Filled,
  Canceled,
  Rejected,
};

struct RiskLimits {
  double max_order_qty;
  double max_order_notional;
  double max_net_position;
  double fat_finger_bps;
};

struct RiskResult {
  bool accepted;
  std::optional<std::string> reason;
};

struct Order {
  std::string order_id;
  std::string symbol;
  Side side;
  double price;
  double qty;
  OrderStatus status{OrderStatus::PendingNew};
  double filled_qty{0.0};
  std::optional<std::string> reject_reason;
};

class RiskEngine {
 public:
  explicit RiskEngine(RiskLimits limits);

  RiskResult Validate(Side side,
                      double price,
                      double qty,
                      double current_position,
                      double reference_price) const;

 private:
  RiskLimits limits_;
};

class OrderManager {
 public:
  OrderManager(RiskEngine risk_engine, double reference_price);

  Order& SubmitOrder(const std::string& symbol, Side side, double price, double qty);
  Order& ApplyEvent(const std::string& order_id, const std::string& event, double fill_qty = 0.0);

  [[nodiscard]] double position() const { return position_; }
  [[nodiscard]] const std::unordered_map<std::string, Order>& orders() const { return orders_; }

 private:
  static bool IsTerminal(OrderStatus status);
  void ApplyFill(Order& order, double fill_qty);

  RiskEngine risk_engine_;
  double reference_price_;
  double position_{0.0};
  std::uint64_t seq_{0};
  std::unordered_map<std::string, Order> orders_;
};

}  // namespace hft
