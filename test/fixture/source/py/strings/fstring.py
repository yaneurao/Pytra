# This file contains test/implementation code for `test/fixtures/fstring.py`.
# Reader-facing comments are added to make roles easier to understand.
# When modifying this file, always verify consistency with existing specs and test results.


from pytra.utils.assertions import py_assert_stdout
def make_msg_22(name: str, count: int) -> str:
    return f"{name}:22:{count}" + f"{count*2}" + f"{name}-{name}"


def _case_main() -> None:
    print(make_msg_22("user", 7))

if __name__ == "__main__":
    print(py_assert_stdout(['user:22:714user-user'], _case_main))
