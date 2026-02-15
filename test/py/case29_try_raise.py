# このファイルは `test/py/case29_try_raise.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

def maybe_fail_29(flag: bool) -> int:
    try:
        if flag:
            raise Exception("fail-29")
        return 10
    except Exception as ex:
        return 20
    finally:
        pass


if __name__ == "__main__":
    print(maybe_fail_29(True))
