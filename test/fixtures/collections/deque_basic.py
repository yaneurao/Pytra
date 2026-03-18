from pytra.std.collections import deque
from pytra.utils.assertions import py_assert_all, py_assert_eq


def run_deque_basic() -> bool:
    checks: list[bool] = []

    d: deque = deque()
    d.append(1)
    d.append(2)
    d.append(3)
    checks.append(py_assert_eq(len(d), 3, "len_after_append"))

    checks.append(py_assert_eq(d.popleft(), 1, "popleft_first"))
    checks.append(py_assert_eq(d.popleft(), 2, "popleft_second"))
    checks.append(py_assert_eq(len(d), 1, "len_after_popleft"))

    checks.append(py_assert_eq(d.pop(), 3, "pop_last"))
    checks.append(py_assert_eq(len(d), 0, "len_after_pop"))

    d.appendleft(10)
    d.appendleft(20)
    d.append(30)
    checks.append(py_assert_eq(d.popleft(), 20, "appendleft_order"))
    checks.append(py_assert_eq(d.popleft(), 10, "appendleft_order_2"))
    checks.append(py_assert_eq(d.popleft(), 30, "append_after_appendleft"))

    d.append(1)
    d.append(2)
    d.clear()
    checks.append(py_assert_eq(len(d), 0, "clear"))

    return py_assert_all(checks, "deque_basic")


if __name__ == "__main__":
    print(run_deque_basic())
