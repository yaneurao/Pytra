# このファイルは `test/fixtures/string_ops.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。


from pytra.runtime.assertions import py_assert_stdout
def decorate(name: str) -> str:
    prefix: str = "[USER] "
    message: str = prefix + name
    return message + "!"


def _case_main() -> None:
    print(decorate("Alice"))

if __name__ == "__main__":
    print(py_assert_stdout(['[USER] Alice!'], _case_main))
