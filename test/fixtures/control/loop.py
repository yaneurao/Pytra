# このファイルは `test/fixtures/loop.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。


from pylib.assertions import py_assert_stdout
def calc_17(values: list[int]) -> int:
    total: int = 0
    for v in values:
        if v % 2 == 0:
            total += v
        else:
            total += v * 2
    return total


def _case_main() -> None:
    print(calc_17([1, 2, 3, 4]))

if __name__ == "__main__":
    print(py_assert_stdout(['14'], _case_main))
