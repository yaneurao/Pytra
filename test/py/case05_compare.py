# このファイルは `test/py/case05_compare.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

def is_large(n: int) -> bool:
    if n >= 10:
        return True
    else:
        return False


if __name__ == "__main__":
    print(is_large(11))
