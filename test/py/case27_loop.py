# このファイルは `test/py/case27_loop.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

def calc_27(values: list[int]) -> int:
    total: int = 0
    for v in values:
        if v % 2 == 0:
            total = total + v
        else:
            total = total + (v * 2)
    return total


if __name__ == "__main__":
    print(calc_27([1, 2, 3, 4]))
