# このファイルは `test/py/case25_negative_index.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

def last_item_25() -> int:
    stack: list[int] = [10, 20, 30, 40]
    return stack[-1]


if __name__ == "__main__":
    print(last_item_25())
