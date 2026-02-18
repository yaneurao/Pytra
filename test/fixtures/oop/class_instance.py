# このファイルは `test/fixtures/class_instance.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。


from py_module.py_runtime import py_assert_stdout
class Box100:
    def __init__(self, seed: int) -> None:
        self.seed = seed

    def next(self) -> int:
        self.seed += 1
        return self.seed


def _case_main() -> None:
    b: Box100 = Box100(3)
    print(b.next())

if __name__ == "__main__":
    print(py_assert_stdout(['4'], _case_main))
