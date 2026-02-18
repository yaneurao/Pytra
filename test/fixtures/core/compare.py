# このファイルは `test/fixtures/compare.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。


from pylib.assertions import py_assert_stdout
def is_large(n: int) -> bool:
    if n >= 10:
        return True
    else:
        return False


def _case_main() -> None:
    print(is_large(11))

if __name__ == "__main__":
    print(py_assert_stdout(['True'], _case_main))
