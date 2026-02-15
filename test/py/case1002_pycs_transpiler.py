# このファイルは `test/py/case1002_pycs_transpiler.py` のテストコードです。
# pycs_transpiler.py を C++ へ変換できることを確認します。

from pathlib import Path
import sys


if __name__ == "__main__":
    root: Path = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root))

    from src.pycpp_transpiler import transpile

    src_file: Path = root / "src" / "pycs_transpiler.py"
    out_file: Path = root / "test" / "cpp" / "case1002_pycs_transpiler.cpp"

    out_file.parent.mkdir(parents=True, exist_ok=True)
    transpile(str(src_file), str(out_file))
    print("ok")
