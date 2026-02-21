# This file contains test/implementation code for `test/fixtures/class_member.py`.
# Reader-facing comments are added to make roles easier to understand.
# When modifying this file, always verify consistency with existing specs and test results.


from pytra.utils.assertions import py_assert_stdout
class Counter:
    value: int = 0

    def inc(self) -> int:
        Counter.value += 1
        return Counter.value


def _case_main() -> None:
    c: Counter = Counter()
    c.inc()
    c = Counter()
    print(c.inc())

if __name__ == "__main__":
    print(py_assert_stdout(['2'], _case_main))
