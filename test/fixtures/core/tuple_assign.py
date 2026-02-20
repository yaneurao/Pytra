# このファイルは `test/fixtures/tuple_assign.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。


from pytra.utils.assertions import py_assert_stdout
def swap_sum_18(a: int, b: int) -> int:
    x: int = a
    y: int = b
    x, y = y, x
    return x + y


def _case_main() -> None:
    print(swap_sum_18(10, 20))

if __name__ == "__main__":
    print(py_assert_stdout(['30'], _case_main))
