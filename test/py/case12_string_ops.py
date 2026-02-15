# このファイルは `test/py/case12_string_ops.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

def decorate(name: str) -> str:
    prefix: str = "[USER] "
    message: str = prefix + name
    return message + "!"


if __name__ == "__main__":
    print(decorate("Alice"))
