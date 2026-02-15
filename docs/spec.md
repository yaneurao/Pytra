# 概要

- PythonからC#へのトランスパイラを作ってください。

## トランスパイラの使い方

例 : `case11_fib.py` を `case11_fib.cs` に変換する場合。

```
python pycs.py test/py/case11_fib.py test/cs/case11_fib.cs
```

## 言語仕様

- Pythonのコードは、型アノテーション必須とします。
- Pythonのintは、そのままC#のintに変換されるものとします。
- Pythonのastモジュールを用いてASTを取得し、C#に1対1になるべく近い形で書き出します。
- `import` / `from ... import ...` は C# の `using` に変換します（`as` は `using` エイリアスに変換）。
- x : int = 1 のように変数の型をひとたびint型と決めたら、そのあと別の型であるstr型の値の代入はできないものとします。
- class は単一継承をサポートし、`self` は C# の `this` として変換します。
- Python の class 本体で宣言したメンバーは C# の `static` メンバーとして変換します。
- `__init__` 内で `self.xxx` に代入したメンバーは C# のインスタンスメンバー（非`static`）として変換します。
- `@dataclass` を付けた class は、型注釈付きフィールドをインスタンスメンバーとして変換し、必要なコンストラクタを自動生成します。

## フォルダ構成

- ソースコードのフォルダ : src/
- テスト用のコードフォルダ : test/
- ドキュメントフォルダ : docs/

## 単体テスト

- 単体テストとして、`test/py/` 配下のサンプルPythonコードを C# に変換し、`test/cs/` の期待コードと一致することを確認してください。
- フィボナッチは `case11_fib` としてサンプルに含めます。

### 単体テストの実行方法

- プロジェクトルート (`PyCs/`) で以下を実行します。

```bash
python -m unittest discover -s test -p "test_*.py" -v
```

- 期待する結果
  - `test_transpile_cases.py` が `ok` になり、各 `caseXX` の変換結果が期待する C# コードと一致します。

### トランスパイラの使い方（補足）

- 変換コマンド

```bash
python pycs.py <input.py> <output.cs>
```

- 例

```bash
python pycs.py test/py/case11_fib.py test/cs/case11_fib.cs
```

- エラー時は標準エラー出力に `error: ...` 形式で理由を表示し、終了コードは `1` になります。

### テスト時の注意点

- 入力Pythonコードは型アノテーション必須です（関数引数・戻り値・必要な変数宣言）。
- 未対応の構文を使うとトランスパイル時にエラーになります。
- テスト用サンプルは `test/py/caseXX_*.py` と `test/cs/caseXX_*.cs` の対応で管理します。
- 現在のサンプル数は `case01` から `case100` までの100件です。
- 変換後の `.cs` は `test/cs/` に出力します。既存ケースを更新した場合は、対応する `test/cs/` も更新してください。

### サンプルプログラム解説

- `case01_add`: 整数の加算関数と `print` の基本ケース。
- `case02_sub_mul`: 減算と乗算、かっこ付き式の変換確認。
- `case03_if_else`: `if/else` と単項マイナス演算の確認。
- `case04_assign`: 型付き変数宣言 (`AnnAssign`) と再代入 (`Assign`) の確認。
- `case05_compare`: 比較演算子 `>=` と `bool` 戻り値の確認。
- `case06_string`: 文字列連結 (`str + str`) の基本ケース。
- `case07_float`: `float -> double` 変換と除算の確認。
- `case08_nested_call`: 関数呼び出しのネスト変換確認。
- `case09_top_level`: トップレベル変数宣言と `Main` からの利用確認。
- `case10_not`: 論理否定 (`not`) の変換確認。
- `case11_fib`: 再帰関数（フィボナッチ）の変換確認ケース。
- `case12_string_ops`: 文字列プレフィックス付与と複数回の連結を行う文字列操作ケース。
- `case13_class`: クラス定義、インスタンス生成、インスタンスメソッド呼び出しを行うケース。
- `case14_inheritance`: 親クラスの継承と、子クラスメソッド内から継承メソッドを呼び出すケース。
- `case15_class_member`: class 本体のメンバー（`static` 変換）の宣言・更新・参照を行うケース。
- `case16_instance_member`: `__init__` で初期化するインスタンスメンバー（非`static`）の宣言・参照を行うケース。

## 制約

- トランスパイラ本体は、Pythonで書くこと。
