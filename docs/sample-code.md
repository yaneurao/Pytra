# サンプルコードについて

## サンプルコードとその変換されたコード

Pythonで書かれた実用サンプルと、それを各言語に本トランスパイラで変換したものです。

- [sample/py](../sample/py): Pythonで書かれたサンプル(変換元)
- [sample/cpp](../sample/cpp): C++へ変換したサンプル
- [sample/rs](../sample/rs): Rustへ変換したサンプル
- [sample/cs](../sample/cs): C#へ変換したサンプル
- [sample/js](../sample/js): JavaScriptへ変換したサンプル
- [sample/ts](../sample/ts): TypeScriptへ変換したサンプル
- [sample/go](../sample/go): Goへ変換したサンプル
- [sample/java](../sample/java): Javaへ変換したサンプル
- [sample/swift](../sample/swift): Swiftへ変換したサンプル
- [sample/kotlin](../sample/kotlin): Kotlinへ変換したサンプル

## 計測条件について

計測条件:
- Python: `PYTHONPATH=src python3 sample/py/<file>.py`
- C++: `g++ -std=c++20 -O3 -ffast-math -flto -I src ...` でビルドした実行ファイル
- C#: `mcs ...` + `mono ...`


## テストコード

Pythonで書かれた小規模テストケースと、それを各言語に本トランスパイラで変換したものです。

注: トランスパイラが正しく実装されているかの検証に利用します。

- [test/py](../test/py)   : Pythonで書かれたテストコード
- [test/cpp](../test/cpp) : C++へ変換したテストコード
- [test/rs](../test/rs): Rustへ変換したテストコード
- [test/cs](../test/cs): C#へ変換したテストコード
- [test/js](../test/js): JavaScriptへ変換したテストコード
- [test/ts](../test/ts): TypeScriptへ変換したテストコード
- [test/go](../test/go): Goへ変換したテストコード
- [test/java](../test/java): Javaへ変換したテストコード
- [test/swift](../test/swift): Swiftへ変換したテストコード
- [test/kotlin](../test/kotlin): Kotlinへ変換したテストコード
