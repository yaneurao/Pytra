# このファイルは `test/fixtures/py/case33_dict_in.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。


from py_module.py_runtime import py_assert_stdout
def has_key_23(k: str) -> bool:
    d: dict[str, int] = {"a": 1, "b": 2}
    if k in d:
        return True
    else:
        return False


def _case_main() -> None:
    print(has_key_23("a"))

if __name__ == "__main__":
    print(py_assert_stdout(['True'], _case_main))
