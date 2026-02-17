# 同一インスタンス共有のテスト。
# 参照セマンティクスが壊れると a,b の値が一致しない。


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


if __name__ == "__main__":
    run_case35_alias_arg()
