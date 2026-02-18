# このファイルは `test/fixtures/py/case02_sub_mul.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。


from py_module.py_runtime import py_assert_stdout
def calc(x: int, y: int) -> int:
    return (x - y) * 2

def div_calc(x: int, y: int) -> float:
    return x / y


def _case_main() -> None:
    print(calc(9, 4))
    print(div_calc(9, 4))

if __name__ == "__main__":
    print(py_assert_stdout(['10', '2.25'], _case_main))
