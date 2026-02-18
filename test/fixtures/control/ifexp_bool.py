# このファイルは `test/fixtures/ifexp_bool.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。


from py_module.py_runtime import py_assert_stdout
def pick_25(a: int, b: int, flag: bool) -> int:
    c: int = a if (flag and (a > b)) else b
    return c


def _case_main() -> None:
    print(pick_25(10, 3, True))

if __name__ == "__main__":
    print(py_assert_stdout(['10'], _case_main))
