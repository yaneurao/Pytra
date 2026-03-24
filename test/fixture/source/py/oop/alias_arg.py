# Test for sharing the same instance.
# If reference semantics break, values in a and b diverge.


from pytra.utils.assertions import py_assert_stdout
class Box:
    def __init__(self, v: int) -> None:
        self.v = v


def bump(x: Box) -> None:
    x.v += 1


def run_alias_arg() -> None:
    a = Box(1)
    b = a
    bump(b)
    print(a.v)
    print(b.v)


def _case_main() -> None:
    run_alias_arg()

if __name__ == "__main__":
    print(py_assert_stdout(['2', '2'], _case_main))
