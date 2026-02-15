# このファイルは `test/py/case10_not.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

def invert(flag: bool) -> bool:
    if not flag:
        return True
    else:
        return False


if __name__ == "__main__":
    print(invert(False))
