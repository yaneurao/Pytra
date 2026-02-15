# このファイルは `test/py/case08_nested_call.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

def inc(x: int) -> int:
    return x + 1


def twice(x: int) -> int:
    return inc(inc(x))


if __name__ == "__main__":
    print(twice(10))
