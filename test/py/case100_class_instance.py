# このファイルは `test/py/case100_class_instance.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

import pathlib
from typing import List as TList


class Box100:
    def __init__(self, seed: int) -> None:
        self.seed = seed

    def next(self) -> int:
        self.seed += 1
        return self.seed


if __name__ == "__main__":
    b: Box100 = Box100(3)
    print(b.next())
