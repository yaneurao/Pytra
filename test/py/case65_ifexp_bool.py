# このファイルは `test/py/case65_ifexp_bool.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

def pick_65(a: int, b: int, flag: bool) -> int:
    c: int = a if (flag and (a > b)) else b
    return c


if __name__ == "__main__":
    print(pick_65(10, 3, True))
