# このファイルは `test/py/case20_finally.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

def finally_effect_20(flag: bool) -> int:
    value: int = 0
    try:
        if flag:
            raise Exception("fail-20")
        value = 10
    except Exception as ex:
        value = 20
    finally:
        value += 3
    return value


if __name__ == "__main__":
    print(finally_effect_20(True))
