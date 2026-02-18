# このファイルは `test/fixtures/float.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。


from py_module.py_runtime import py_assert_stdout
def half(x: float) -> float:
    return x / 2.0


def _case_main() -> None:
    print(half(5.0))

if __name__ == "__main__":
    print(py_assert_stdout(['2.5'], _case_main))
