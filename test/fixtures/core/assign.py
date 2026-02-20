# このファイルは `test/fixtures/assign.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。


from pytra.utils.assertions import py_assert_stdout
def square_plus_one(n: int) -> int:
    result = n * n
    result += 1
    return result


def _case_main() -> None:
    print(square_plus_one(5))

if __name__ == "__main__":
    print(py_assert_stdout(['26'], _case_main))
