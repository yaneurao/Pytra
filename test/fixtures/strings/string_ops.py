# This file contains test/implementation code for `test/fixtures/string_ops.py`.
# Reader-facing comments are added to make roles easier to understand.
# When modifying this file, always verify consistency with existing specs and test results.


from pytra.utils.assertions import py_assert_stdout
def decorate(name: str) -> str:
    prefix: str = "[USER] "
    message: str = prefix + name
    return message + "!"


def _case_main() -> None:
    print(decorate("Alice"))

if __name__ == "__main__":
    print(py_assert_stdout(['[USER] Alice!'], _case_main))
