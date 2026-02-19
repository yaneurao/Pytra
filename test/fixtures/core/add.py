# このファイルは `test/fixtures/add.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。


from pytra.runtime.assertions import py_assert_stdout
def add(a: int, b: int) -> int:
    return a + b


def _case_main() -> None:
    print(add(3, 4))

if __name__ == "__main__":
    print(py_assert_stdout(['7'], _case_main))
