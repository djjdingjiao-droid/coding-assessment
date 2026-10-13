from inventory_ledger import process


def test_example_and_replay():
    text = """10 6
RESERVE e1 o100 4
RESERVE e2 o200 7
SHIP e3 o100 2
RELEASE e4 o100 2
RESERVE e5 o999 1
RESERVE e2 o999 1
"""
    assert process(text) == [
        "OK 10 4", "REJECTED 10 4", "OK 8 2", "OK 8 0",
        "OK 11 1", "DUPLICATE 11 1", "OPEN o999 1",
    ]


def test_rejected_event_is_idempotent():
    assert process("1 2\nRESERVE e1 a 2\nRESERVE e1 a 1\n") == [
        "REJECTED 1 0", "DUPLICATE 1 0"
    ]

