# This file contains test/implementation code for `test/fixtures/gc_reassign.py`.
# Verify that reassignment `a = b` destroys the object whose reference was dropped.


from pytra.utils.assertions import py_assert_stdout
class Tracked:
    def __init__(self, name: str) -> None:
        self.name = name

    def __del__(self) -> None:
        print("DEL", self.name)


def run_gc_reassign() -> None:
    a = Tracked("A")
    b = Tracked("B")
    print("before reassign")
    a = b
    print("after reassign")


def _case_main() -> None:
    run_gc_reassign()

if __name__ == "__main__":
    print(py_assert_stdout(['before reassign', 'DEL A', 'after reassign', 'DEL B'], _case_main))
