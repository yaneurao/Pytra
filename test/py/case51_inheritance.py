# このファイルは `test/py/case51_inheritance.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

class Base51:
    def value(self) -> int:
        return 51


class Child51(Base51):
    def value2(self) -> int:
        return self.value() + 1


if __name__ == "__main__":
    c: Child51 = Child51()
    print(c.value2())
