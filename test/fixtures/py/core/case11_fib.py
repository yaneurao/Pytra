# このファイルは `test/fixtures/py/case11_fib.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。


from py_module.py_runtime import py_assert_stdout
def fib(n: int) -> int:
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)


def _case_main() -> None:
    print(fib(10))

if __name__ == "__main__":
    print(py_assert_stdout(['55'], _case_main))
