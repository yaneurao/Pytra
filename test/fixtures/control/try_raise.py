# このファイルは `test/fixtures/try_raise.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。


from pylib.tra.assertions import py_assert_stdout
def maybe_fail_19(flag: bool) -> int:
    try:
        if flag:
            raise Exception("fail-19")
        return 10
    except Exception as ex:
        return 20
    finally:
        pass


def _case_main() -> None:
    print(maybe_fail_19(True))

if __name__ == "__main__":
    print(py_assert_stdout(['20'], _case_main))
