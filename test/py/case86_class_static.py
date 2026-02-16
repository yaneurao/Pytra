# このファイルは `test/py/case86_class_static.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

class Counter86:
    total: int = 0

    def add(self, x: int) -> int:
        self.total += x
        return self.total


if __name__ == "__main__":
    c: Counter86 = Counter86()
    print(c.add(5))
