# This file contains test/implementation code for `test/fixtures/string.py`.
# Reader-facing comments are added to make roles easier to understand.
# When modifying this file, always verify consistency with existing specs and test results.


from pytra.utils.assertions import py_assert_stdout
def greet(name: str) -> str:
    return "Hello, " + name


def _case_main() -> None:
    print(greet("Codex"))

if __name__ == "__main__":
    print(py_assert_stdout(['Hello, Codex'], _case_main))
