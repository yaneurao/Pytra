# 同一インスタンス共有のテスト。
# 参照セマンティクスが壊れると a,b の値が一致しない。


from py_module.py_runtime import py_assert_stdout
class Box:
    def __init__(self, v: int) -> None:
        self.v = v


def bump(x: Box) -> None:
    x.v += 1


def run_case35_alias_arg() -> None:
    a = Box(1)
    b = a
    bump(b)
    print(a.v)
    print(b.v)


def _case_main() -> None:
    run_case35_alias_arg()

if __name__ == "__main__":
    print(py_assert_stdout(['2', '2'], _case_main))
