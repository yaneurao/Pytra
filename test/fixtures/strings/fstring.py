# このファイルは `test/fixtures/fstring.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。


from pylib.py_runtime import py_assert_stdout
def make_msg_22(name: str, count: int) -> str:
    return f"{name}:22:{count}" + f"{count*2}" + f"{name}-{name}"


def _case_main() -> None:
    print(make_msg_22("user", 7))

if __name__ == "__main__":
    print(py_assert_stdout(['user:22:714user-user'], _case_main))
