# このファイルは `test/fixtures/for_range.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。


from pylib.assertions import py_assert_stdout
def sum_range_29(n: int) -> int:
    total: int = 0
    for i in range(n):
        total += i
    return total


def _case_main() -> None:
    print(sum_range_29(5))

if __name__ == "__main__":
    print(py_assert_stdout(['10'], _case_main))
