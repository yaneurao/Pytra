# このファイルは `test/py/case09_top_level.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

def mul3(n: int) -> int:
    return n * 3


value: int = 7

if __name__ == "__main__":
    print(mul3(value))
