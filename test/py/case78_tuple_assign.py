# このファイルは `test/py/case78_tuple_assign.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

def swap_sum_78(a: int, b: int) -> int:
    x: int = a
    y: int = b
    x, y = y, x
    return x + y


if __name__ == "__main__":
    print(swap_sum_78(10, 20))
