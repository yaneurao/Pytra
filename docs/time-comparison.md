# 計測条件等

## サンプルコードとその変換されたコード

- [sample/py](../sample/py): Pythonで書かれたサンプル（15本）
- [sample/cpp](../sample/cpp): C++へ変換したサンプル
- [sample/cs](../sample/cs): C#へ変換したサンプル

## 計測条件について

計測条件:
- Python: `PYTHONPATH=src python3 sample/py/<file>.py`
- C++: `g++ -std=c++20 -O2 -I src ...` でビルドした実行ファイル
- C#: `mcs ...` + `mono ...`
