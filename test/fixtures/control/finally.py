# This file contains test/implementation code for `test/fixtures/finally.py`.
# Reader-facing comments are added to make roles easier to understand.
# When modifying this file, always verify consistency with existing specs and test results.


from pytra.utils.assertions import py_assert_stdout
def finally_effect_20(flag: bool) -> int:
    value: int = 0
    try:
        if flag:
            raise Exception("fail-20")
        value = 10
    except Exception as ex:
        value = 20
    finally:
        value += 3
    return value


def _case_main() -> None:
    print(finally_effect_20(True))

if __name__ == "__main__":
    print(py_assert_stdout(['23'], _case_main))
