import pytra.typing as typing
from pytra.utils.assertions import py_assert_all, py_assert_eq


def _sum_list(xs: typing.List[int]) -> int:
    total: int = 0
    for x in xs:
        total += x
    return total


def _head_pair(pair: typing.Tuple[int, int]) -> int:
    return pair[0]


def _has_key(d: typing.Dict[str, int], keys: typing.Set[str]) -> bool:
    for k in keys:
        if k in d:
            return True
    return False


def run_typing_extended() -> bool:
    checks: list[bool] = []
    checks.append(py_assert_eq(_sum_list([1, 2, 3]), 6, "List"))
    checks.append(py_assert_eq(_head_pair((7, 8)), 7, "Tuple"))
    checks.append(py_assert_eq(_has_key({"a": 1}, {"a", "b"}), True, "Dict/Set"))
    return py_assert_all(checks, "typing_extended")


if __name__ == "__main__":
    print(run_typing_extended())
