# このファイルは `test/fixtures/class.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。


from pylib.tra.assertions import py_assert_stdout
class Multiplier:
    def mul(self, x: int, y: int) -> int:
        return x * y


def _case_main() -> None:
    m: Multiplier = Multiplier()
    print(m.mul(6, 7))

if __name__ == "__main__":
    print(py_assert_stdout(['42'], _case_main))
