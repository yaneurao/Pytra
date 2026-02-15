# このファイルは `test/py/case94_comprehension.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

def comp_like_94(x: int) -> int:
    values: list[int] = [i for i in [1, 2, 3, 4]]
    return x + 1


if __name__ == "__main__":
    print(comp_like_94(5))
