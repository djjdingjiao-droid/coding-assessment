"""
大规模场景可以将内层有界数量转移替换成单调队列优化。
"""
from __future__ import annotations

import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class Warehouse:
    warehouse_id: str
    stock: int
    fixed_cost: int
    unit_cost: int


def optimise(warehouses: list[Warehouse], required: int):
    if required < 0 or sum(w.stock for w in warehouses) < required:
        return None
    warehouses = sorted(warehouses, key=lambda item: item.warehouse_id)
    # (使用仓库数, 分配数量) -> (成本, 按仓库 ID 排序的分配方案)
    dp: dict[tuple[int, int], tuple[int, tuple[tuple[str, int], ...]]] = {(0, 0): (0, ())}
    for warehouse in warehouses:
        nxt = dict(dp)  # 当前仓库不分配库存时，保留既有状态。
        for (used, already), (cost, allocation) in dp.items():
            maximum = min(warehouse.stock, required - already)
            for qty in range(1, maximum + 1):
                key = (used + 1, already + qty)
                candidate = (cost + warehouse.fixed_cost + qty * warehouse.unit_cost,
                             allocation + ((warehouse.warehouse_id, qty),))
                old = nxt.get(key)
                if old is None or candidate < old:
                    nxt[key] = candidate
        dp = nxt
    candidates = [(used, cost, allocation) for (used, qty), (cost, allocation) in dp.items() if qty == required]
    if not candidates:
        return None
    used, cost, allocation = min(candidates)
    return used, cost, allocation


def main(text: str) -> str:
    lines = [line.split() for line in text.splitlines() if line.strip()]
    if not lines:
        raise ValueError("missing input")
    count, required = map(int, lines[0])
    if len(lines) != count + 1:
        raise ValueError("warehouse count mismatch")
    warehouses = [Warehouse(row[0], int(row[1]), int(row[2]), int(row[3])) for row in lines[1:]]
    result = optimise(warehouses, required)
    if result is None:
        return "-1"
    used, cost, allocation = result
    return "\n".join([f"{used} {cost}"] + [f"{name} {qty}" for name, qty in allocation])


if __name__ == "__main__":
    print(main(sys.stdin.read()))

