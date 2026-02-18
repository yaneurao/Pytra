# このファイルは `test/fixtures/string.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。


from py_module.py_runtime import py_assert_stdout
def greet(name: str) -> str:
    return "Hello, " + name


def _case_main() -> None:
    print(greet("Codex"))

if __name__ == "__main__":
    print(py_assert_stdout(['Hello, Codex'], _case_main))
