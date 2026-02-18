# このファイルは `test/fixtures/instance_member.py` のテスト/実装コードです。
# 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
# 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。


from pylib.py_runtime import py_assert_stdout
class Point:
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

    def total(self) -> int:
        return self.x + self.y


def _case_main() -> None:
    p: Point = Point(2, 5)
    print(p.total())

if __name__ == "__main__":
    print(py_assert_stdout(['7'], _case_main))
