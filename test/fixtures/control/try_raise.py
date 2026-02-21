# This file contains test/implementation code for `test/fixtures/try_raise.py`.
# Reader-facing comments are added to make roles easier to understand.
# When modifying this file, always verify consistency with existing specs and test results.


from pytra.utils.assertions import py_assert_stdout
def maybe_fail_19(flag: bool) -> int:
    try:
        if flag:
            raise Exception("fail-19")
        return 10
    except Exception as ex:
        return 20
    finally:
        pass


def _case_main() -> None:
    print(maybe_fail_19(True))

if __name__ == "__main__":
    print(py_assert_stdout(['20'], _case_main))
