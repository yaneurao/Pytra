# 値型最適化候補のテスト（インスタンス状態なし）。


from py_module.py_runtime import py_assert_stdout
class Tag:
    def id(self) -> int:
        return 7


def run_stateless_value() -> None:
    t = Tag()
    u = t
    print(t.id())
    print(u.id())


def _case_main() -> None:
    run_stateless_value()

if __name__ == "__main__":
    print(py_assert_stdout(['7', '7'], _case_main))
