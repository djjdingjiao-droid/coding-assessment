from fulfilment_optimizer import Warehouse, optimise


def test_example():
    result = optimise([Warehouse("AU", 5, 8, 2), Warehouse("CN", 20, 7, 1), Warehouse("US", 4, 3, 4)], 7)
    assert result == (1, 14, (("CN", 7),))


def test_prefers_count_before_cost():
    result = optimise([Warehouse("A", 5, 100, 1), Warehouse("B", 3, 0, 1), Warehouse("C", 2, 0, 1)], 5)
    assert result == (1, 105, (("A", 5),))

