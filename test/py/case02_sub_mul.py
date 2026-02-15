# このファイルは `test/py/case02_sub_mul.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

def calc(x: int, y: int) -> int:
    return (x - y) * 2


if __name__ == "__main__":
    print(calc(9, 4))
