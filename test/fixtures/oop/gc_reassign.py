# このファイルは `test/fixtures/gc_reassign.py` のテスト/実装コードです。
# a = b の再代入で参照が切れたオブジェクトが破棄されることを確認します。


from pylib.py_runtime import py_assert_stdout
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
