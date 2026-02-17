# このファイルは `test/py/case33_fstring.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

def make_msg_22(name: str, count: int) -> str:
    return f"{name}:22:{count}"


if __name__ == "__main__":
    print(make_msg_22("user", 7))
