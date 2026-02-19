# このファイルは `test/fixtures/nested_call.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。


from pylib.tra.assertions import py_assert_stdout
def inc(x: int) -> int:
    return x + 1


def twice(x: int) -> int:
    return inc(inc(x))


def _case_main() -> None:
    print(twice(10))

if __name__ == "__main__":
    print(py_assert_stdout(['12'], _case_main))
