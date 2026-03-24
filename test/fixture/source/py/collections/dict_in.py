# This file contains test/implementation code for `test/fixtures/dict_in.py`.
# Reader-facing comments are added to make roles easier to understand.
# When modifying this file, always verify consistency with existing specs and test results.


from pytra.utils.assertions import py_assert_stdout
def has_key_23(k: str) -> bool:
    d: dict[str, int] = {"a": 1, "b": 2}
    if k in d:
        return True
    else:
        return False


def _case_main() -> None:
    print(has_key_23("a"))

if __name__ == "__main__":
    print(py_assert_stdout(['True'], _case_main))
