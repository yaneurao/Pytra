# 値型最適化候補のテスト（インスタンス状態なし）。


class Tag:
    def id(self) -> int:
        return 7


def run_case36_stateless_value() -> None:
    t = Tag()
    u = t
    print(t.id())
    print(u.id())


if __name__ == "__main__":
    run_case36_stateless_value()
