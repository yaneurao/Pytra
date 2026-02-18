# このファイルは `test/fixtures/comprehension.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。


from pylib.assertions import py_assert_stdout
def comp_like_24(x: int) -> int:
    values: list[int] = [i for i in [1, 2, 3, 4]]
    return x + 1


def _case_main() -> None:
    print(comp_like_24(5))

if __name__ == "__main__":
    print(py_assert_stdout(['6'], _case_main))
