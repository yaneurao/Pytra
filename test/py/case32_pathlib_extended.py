# このファイルは `test/py/case32_pathlib_extended.py` のテスト/実装コードです。
# pathlib 相当機能（Path 生成、結合、exists など）の回帰確認に使います。
# テスト対象ファイルはリポジトリ配下の既知パスを利用します。

from pathlib import Path


def main() -> None:
    # Path の生成と / 演算子による連結を確認する。
    base: Path = Path("test")
    nested: Path = base / "py" / "case01_add.py"

    # 既存ファイル・非既存ファイルの exists 判定を確認する。
    exists_target: Path = nested
    missing_target: Path = Path("test") / "py" / "__definitely_missing_case__.py"

    # 文字列化結果と exists 判定結果を出力する。
    print(str(nested))
    print(exists_target.exists())
    print(missing_target.exists())


if __name__ == "__main__":
    main()
