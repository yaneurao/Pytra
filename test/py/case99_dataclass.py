# このファイルは `test/py/case99_dataclass.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

from dataclasses import dataclass


@dataclass
class Point99:
    x: int
    y: int = 10

    def total(self) -> int:
        return self.x + self.y


if __name__ == "__main__":
    p: Point99 = Point99(3)
    print(p.total())
