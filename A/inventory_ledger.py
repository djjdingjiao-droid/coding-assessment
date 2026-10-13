"""单 SKU、状态确定的库存命令处理器。"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field


@dataclass
class Ledger:
    on_hand: int
    reservations: dict[str, int] = field(default_factory=dict)
    processed: set[str] = field(default_factory=set)

    @property
    def reserved(self) -> int:
        return sum(self.reservations.values())

    def apply(self, line: str) -> str:
        parts = line.split()
        if len(parts) != 4:
            return self._result("REJECTED")
        action, event_id, order_id, raw_qty = parts
        if event_id in self.processed:
            return self._result("DUPLICATE")
        # 格式错误或业务拒绝的事件同样要记录，重放时才可保持幂等。
        self.processed.add(event_id)
        try:
            qty = int(raw_qty)
        except ValueError:
            return self._result("REJECTED")
        if action not in {"RESERVE", "RELEASE", "SHIP", "RESTOCK"} or qty <= 0:
            return self._result("REJECTED")

        current = self.reservations.get(order_id, 0)
        if action == "RESERVE":
            if qty > self.on_hand - self.reserved:
                return self._result("REJECTED")
            self.reservations[order_id] = current + qty
        elif action == "RELEASE":
            if qty > current:
                return self._result("REJECTED")
            self._set_reservation(order_id, current - qty)
        elif action == "SHIP":
            if qty > current:
                return self._result("REJECTED")
            self.on_hand -= qty
            self._set_reservation(order_id, current - qty)
        else:  # RESTOCK 不影响某一个订单的预留量。
            self.on_hand += qty
        return self._result("OK")

    def _set_reservation(self, order_id: str, qty: int) -> None:
        if qty:
            self.reservations[order_id] = qty
        else:
            self.reservations.pop(order_id, None)

    def _result(self, status: str) -> str:
        return f"{status} {self.on_hand} {self.reserved}"


def process(text: str) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        raise ValueError("missing header")
    try:
        stock, count = map(int, lines[0].split())
    except ValueError as exc:
        raise ValueError("header must contain initial stock and command count") from exc
    if stock < 0 or count < 0 or len(lines) - 1 != count:
        raise ValueError("invalid header or command count")
    ledger = Ledger(stock)
    output = [ledger.apply(line) for line in lines[1:]]
    output.extend(f"OPEN {order_id} {qty}" for order_id, qty in sorted(ledger.reservations.items()))
    return output


if __name__ == "__main__":
    print("\n".join(process(sys.stdin.read())))

