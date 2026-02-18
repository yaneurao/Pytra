# このファイルは `test/fixtures/top_level.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。


from pylib.runtime import py_assert_stdout
def mul3(n: int) -> int:
    return n * 3


value: int = 7


def _case_main() -> None:
    print(mul3(value))

if __name__ == "__main__":
    print(py_assert_stdout(['21'], _case_main))
