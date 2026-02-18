# このファイルは `test/fixtures/class_member.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。


from py_module.py_runtime import py_assert_stdout
class Counter:
    value: int = 0

    def inc(self) -> int:
        Counter.value += 1
        return Counter.value


def _case_main() -> None:
    c: Counter = Counter()
    c.inc()
    c = Counter()
    print(c.inc())

if __name__ == "__main__":
    print(py_assert_stdout(['2'], _case_main))
