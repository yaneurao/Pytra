# このファイルは `test/py/case13_class.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

class Multiplier:
    def mul(self, x: int, y: int) -> int:
        return x * y


if __name__ == "__main__":
    m: Multiplier = Multiplier()
    print(m.mul(6, 7))
