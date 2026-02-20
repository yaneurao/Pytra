# このファイルは `test/fixtures/if_else.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。


from pytra.utils.assertions import py_assert_stdout
def abs_like(n: int) -> int:
    if n < 0:
        return -n
    else:
        return n


def _case_main() -> None:
    print(abs_like(-12))

if __name__ == "__main__":
    print(py_assert_stdout(['12'], _case_main))
