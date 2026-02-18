# EAST仕様（実装準拠）

この文書は `east/east.py` の現実装に合わせた EAST 仕様である。

## 1. 目的

- EAST(Extended AST) は Python AST から、言語非依存の意味注釈付き JSON を生成する中間表現である。
- 型解決、cast情報、引数 readonly/mutable、mainガード分離を前段で確定させる。
- Pythonにはastという抽象構文木を扱うモジュールがあるが、これだと元のソースコードのコメントなどを残してトランスパイルできないのでEASTという表現を考え、そしてこのためのparserをPythonで実装する。


## 2. 入出力

### 2.1 入力

- UTF-8 の Python ソースファイル 1 つ。

### 2.2 出力形式

- 成功時

```json
{
  "ok": true,
  "east": { "...": "..." }
}
```

- 失敗時

```json
{
  "ok": false,
  "error": {
    "kind": "inference_failure | unsupported_syntax | semantic_conflict",
    "message": "...",
    "source_span": {
      "lineno": 1,
      "col": 0,
      "end_lineno": 1,
      "end_col": 5
    },
    "hint": "..."
  }
}
```

### 2.3 CLI

- `python east/east.py <input.py> [-o output.json] [--pretty] [--human-output output.cpp]`
- `--pretty`: 整形 JSON を出力。
- `--human-output`: C++風の人間可読ビューを出力。
- `python east/py2cpp.py <input.py|east.json> [-o output.cpp]`: EASTベースの C++ 生成器。

## 3. トップレベルEAST構造

`east` オブジェクトは以下を持つ。

- `kind`: 常に `Module`
- `source_path`: 入力パス
- `source_span`: モジュール span
- `body`: 通常のトップレベル文
- `main_guard_body`: `if __name__ == "__main__":` の本体
- `renamed_symbols`: rename マップ

## 4. 構文正規化

- `if __name__ == "__main__":` は `main_guard_body` に分離。
- 次は rename 対象。
- 重複定義名
- 予約名 `main`, `py_main`, `__pytra_main`
- `FunctionDef`/`ClassDef` は `name`（rename後）と `original_name` を持つ。
- `for ... in range(...)` は `ForRange` に正規化され、`start/stop/step/range_mode` を保持。
- `range(...)` は EAST 構築段階で専用表現へ lower し、後段（`py2cpp.py` など）へ生の `Call(Name("range"), ...)` を渡さない。
  - つまり、後段エミッタは Python 組み込み `range` の意味解釈を持たず、EAST の正規化済みノードのみを処理する。
- `for` 以外の式位置 `range(...)` は `RangeExpr` へ lower する（`ListComp` 含む）。

## 5. ノード共通属性

式ノード（`_expr`）は以下を持つ。

- `kind`, `source_span`, `resolved_type`, `borrow_kind`, `casts`, `repr`
- `resolved_type` は推論済み型文字列。
- `borrow_kind` は `value | readonly_ref | mutable_ref`（`move` は未使用）。
- 主要式は構造化子ノードを持つ（`left/right`, `args`, `elements`, `entries` など）。

関数ノードは以下を持つ。

- `arg_types`, `return_type`, `arg_usage`, `renamed_symbols`

## 6. 型システム

### 6.1 正規型

- 整数型: `int8`, `uint8`, `int16`, `uint16`, `int32`, `uint32`, `int64`, `uint64`
- 浮動小数型: `float32`, `float64`
- 基本型: `bool`, `str`, `None`
- 合成型: `list[T]`, `set[T]`, `dict[K,V]`, `tuple[T1,...]`
- 拡張型: `Path`, `Exception`, クラス名
- 補助型: `unknown`, `module`, `callable[float64]`

### 6.2 注釈正規化

- `int` は `int64` に正規化。
- `float` は `float64` に正規化。
- `float32/float64` はそのまま保持。
- `bytes` / `bytearray` は `list[uint8]` に正規化。
- `pathlib.Path` は `Path` に正規化。

## 7. 型推論ルール

- `Name`: 型環境から解決。未解決は `inference_failure`。
- `Constant`:
- 整数リテラルは `int64`
- 実数リテラルは `float64`, 真偽 `bool`, 文字列 `str`, `None`
- `List/Set/Dict`:
- 非空は要素型単一化で推論
- 空は通常 `inference_failure`
- ただし `AnnAssign` で注釈付き空コンテナは注釈型を採用
- `Tuple`: `tuple[...]` を構成。
- `BinOp`:
- 数値演算 `+ - * % // /` を推論
- 混在数値は `float32/float64` を含む型昇格を行い `casts` を付与
- `Path / str` は `Path`
- `str * int`, `list[T] * int` をサポート
- ビット演算 `& | ^ << >>` は整数型として推論
  - 注: `%` の負数オペランド時の Python/C++ 差異は EAST では吸収しない。
  - C++ 生成では `%` をそのまま出力し、負数オペランドは言語仕様上の対象外とする。
- `Subscript`:
- `list[T][i] -> T`
- `dict[K,V][k] -> V`
- `str[i] -> str`
- `list/str` スライスは同型
- `Call`:
- 既知: `int`, `float`, `bool`, `str`, `bytes`, `bytearray`, `len`, `range`, `min`, `max`, `round`, `print`, `write_rgb_png`, `save_gif`, `grayscale_palette`, `perf_counter`, `Path`, `Exception`, `RuntimeError`
- `float(...)`, `round(...)`, `perf_counter()`, `math.*` 主要関数は `float64`
- `bytes(...)` / `bytearray(...)` は `list[uint8]`
- クラスコンストラクタ/メソッドは事前収集した型情報で推論
- `ListComp`: 単一ジェネレータのみ対応

`range` について:

- 入力AST上で `Call(Name("range"), ...)` が現れても、最終EASTでは専用ノード（例: `ForRange` / `RangeExpr` 等）へ変換し、直接の `Call` として残さない。
- `range` のまま残るケースは EAST 構築不備として扱い、後段で暗黙救済しない。

`lowered_kind: BuiltinCall` について:

- EAST は `runtime_call` を付与して後段実装の分岐を削減する。
- 実装済みの主要 runtime_call 例:
  - `py_print`, `py_len`, `py_to_string`, `static_cast`
  - `py_min`, `py_max`, `perf_counter`
  - `list.append`, `list.extend`, `list.pop`, `list.clear`, `list.reverse`, `list.sort`
  - `set.add`, `set.discard`, `set.remove`, `set.clear`
  - `write_rgb_png`, `save_gif`, `grayscale_palette`
  - `py_isdigit`, `py_isalpha`

## 8. cast仕様

数値昇格時に `casts` を出力する。

```json
{
  "on": "left | right | body | orelse",
  "from": "int64",
  "to": "float32 | float64",
  "reason": "numeric_promotion | ifexp_numeric_promotion"
}
```

## 9. 引数 readonly/mutable 判定

`ArgUsageAnalyzer` により `arg_usage` を付与する。

- `mutable` 条件
- 引数自体への代入/拡張代入
- 引数属性・添字への書き込み
- 破壊的メソッド呼び出し（`append`, `extend`, `pop`, `write_text`, `mkdir` など）
- 純粋組み込み以外への引数渡し
- それ以外は `readonly`

`borrow_kind` はこの判定を反映する。

## 10. 対応文

- `FunctionDef`, `ClassDef`, `Return`
- `Assign`, `AnnAssign`, `AugAssign`
- `Expr`, `If`, `For`, `ForRange`, `While`, `Try`, `Raise`
- `Import`, `ImportFrom`, `Pass`, `Break`, `Continue`

補足:

- `Assign` は単一ターゲット文のみ。
- タプル代入は対応（例: `x, y = ...`, `a[i], a[j] = ...`）。
- 名前ターゲットについては RHS タプル型が分かる場合に型環境を更新。

## 11. クラス情報の事前収集

生成前に以下を収集する。

- クラス名
- 単純継承関係
- メソッド戻り値型
- フィールド型（クラス本体 `AnnAssign` / `__init__` 代入解析）

## 12. エラー契約

`EastBuildError` は `kind`, `message`, `source_span`, `hint` を持つ。

- `inference_failure`
- `unsupported_syntax`
- `semantic_conflict`

`SyntaxError` も同形式に変換する。

## 13. 人間可読ビュー

- `--human-output` で C++風擬似ソースを出力する。
- 目的はレビュー容易化であり、C++としての厳密コンパイル性は保証しない。
- EASTの `source_span`, `resolved_type`, `ForRange`, `renamed_symbols` 等を保持して可視化する。

## 14. 既知の制約

- Python全構文網羅ではない（Pytra対象サブセット）。
- 高度なデータフロー解析（厳密エイリアス/副作用伝播）は未実装。
- `borrow_kind=move` は未使用。

## 15. 検証状態

- `test/fixtures` 32/32 を `east/east.py` で変換可能（`ok: true`）
- `sample/py` 16/16 を `east/east.py` で変換可能（`ok: true`）
- `sample/py` 16/16 を `east/py2cpp.py` で「変換→コンパイル→実行」可能（`ok`）
  - 実行時間一覧: `east/sample/benchmark_east_py2cpp.md`
