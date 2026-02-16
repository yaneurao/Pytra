# このファイルは `test/py/case47_loop.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

def calc_47(values: list[int]) -> int:
    total: int = 0
    for v in values:
        if v % 2 == 0:
            total += v
        else:
            total += (v * 2)
    return total


if __name__ == "__main__":
    print(calc_47([1, 2, 3, 4]))
