# このファイルは `test/py/case15_class_member.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

class Counter:
    value: int = 0

    def inc(self) -> int:
        Counter.value += 1
        return Counter.value


if __name__ == "__main__":
    c: Counter = Counter()
    c.inc()
    c = Counter()
    print(c.inc())
