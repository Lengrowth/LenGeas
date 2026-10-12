from time import perf_counter

from packages.runtime.src.lengeas_runtime.formulas import evaluate_formula


def test_formula_fixture_meets_local_50ms_runtime_budget() -> None:
    expression = {
        "operator": "add",
        "args": [
            {
                "operator": "multiply",
                "args": [
                    {"operator": "literal", "value": "1.25"},
                    {"operator": "literal", "value": 40},
                ],
            },
            {"operator": "literal", "value": 7},
        ],
    }
    started = perf_counter()
    for _ in range(100):
        assert evaluate_formula(expression, {}) == 57
    elapsed_ms = (perf_counter() - started) * 1000
    assert elapsed_ms < 50
