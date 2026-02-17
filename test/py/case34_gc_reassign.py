# このファイルは `test/py/case34_gc_reassign.py` のテスト/実装コードです。
# a = b の再代入で参照が切れたオブジェクトが破棄されることを確認します。


class Tracked:
    def __init__(self, name: str) -> None:
        self.name = name

    def __del__(self) -> None:
        print("DEL", self.name)


def run_case34_gc_reassign() -> None:
    a = Tracked("A")
    b = Tracked("B")
    print("before reassign")
    a = b
    print("after reassign")


if __name__ == "__main__":
    run_case34_gc_reassign()
