# EAST仕様（実装準拠）

この文書は `src/east.py` の現実装に合わせた EAST 仕様である。

## 1. 目的

- EAST は Python AST から、言語非依存の意味注釈付き JSON を生成する中間表現である。
- 目的は、型解決・readonly判定・cast指示・mainガード正規化を共通化すること。

## 2. 入出力

### 2.1 入力

- UTF-8 の Python ソースファイル 1 つ。
- 対象は Pytra の Python サブセット。

### 2.2 出力形式

- 成功時:

```json
{
  "ok": true,
  "east": { ... }
}
```

- 失敗時:

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

- `python src/east.py <input.py> [-o output.json] [--pretty]`
- `--pretty` 指定時は整形 JSON を出力する。

## 3. トップレベルEAST構造

`east` オブジェクトは次を持つ。

- `kind`: 常に `"Module"`
- `source_path`: 入力ファイルパス
- `source_span`: モジュールの span（現実装では `null` を含み得る）
- `body`: モジュール本体ステートメント配列
- `main_guard_body`: `if __name__ == "__main__":` の本体
- `renamed_symbols`: 識別子 rename マップ（例: `main -> __pytra_main`）

## 4. 構文正規化

- `if __name__ == "__main__":` は `main_guard_body` に分離する。
- 識別子衝突回避として次を rename 対象にする。
  - 重複定義名
  - 予約名: `main`, `py_main`, `__pytra_main`
- 生成される関数/クラスノードは `name`（rename後）と `original_name`（元名）を持つ。

## 5. ノード共通属性

式ノード（`_expr` で生成されるノード）は次を持つ。

- `kind`: 元 AST ノード名（例: `Name`, `Call`, `BinOp`）
- `source_span`
- `resolved_type`
- `borrow_kind`:
  - `value`
  - `readonly_ref`
  - `mutable_ref`
- `casts`: cast 指示配列
- `repr`: `ast.unparse` による文字列表現

関数ノードは次を持つ。

- `arg_types`: 引数名 -> 型
- `return_type`
- `arg_usage`: 引数名 -> `readonly` / `mutable`
- `renamed_symbols`: 当該関数に関わる rename 情報

## 6. 型システム（現実装）

### 6.1 正規型

- 基本型: `int`, `float`, `bool`, `str`, `bytes`, `bytearray`, `None`
- 合成型: `list[T]`, `set[T]`, `dict[K,V]`, `tuple[T1,...]`
- 拡張型: `Path`, `Exception`, クラス名
- 補助型: `unknown`（推論不能だが継続許容する箇所で利用）

### 6.2 注釈正規化

- `int8/uint8/int16/uint16/int32/uint32/int64/uint64` は `int` へ正規化。
- `float32/float64` は `float` へ正規化。
- `pathlib.Path` は `Path` へ正規化。

## 7. 型推論ルール（現実装）

- `Name` は型環境から解決する。未解決は `inference_failure`。
- `Constant` は型を直接決定。
- `List/Set/Dict`:
  - 空コンテナは曖昧として `inference_failure`。
  - 要素型の単一化が必要。
- `Tuple` は要素型列から `tuple[...]` を構成。
- `BinOp`:
  - 数値混在は `float` へ昇格。
  - `Path / str` は `Path`。
- `Subscript`:
  - `list[T][i] -> T`
  - `dict[K,V][k] -> V`
  - `str[i] -> str`
  - `list/str` のスライスはそれぞれ `list[T]` / `str`
- `Call`:
  - 組み込み (`int/float/str/bool/len/range/round/min/max/...`) を既知型で解決。
  - `Path(...)`, `pathlib.Path(...)` を `Path` 解決。
  - `math.*`（`sqrt/sin/cos/tan/exp/log/log10/fabs/floor/ceil/pow`）は `float`。
  - クラスコンストラクタ呼び出しはクラス型。
  - クラスメソッド呼び出しは戻り値注釈（継承探索あり）から解決。
  - 未解決呼び出しは `inference_failure`。
- `ListComp`:
  - 単一ジェネレータのみ対応。
  - 反復対象からターゲット型を導出して `list[T]` を構成。

## 8. cast 仕様

現実装の `casts` は明示的な数値昇格で付与される。

- 例:
  - `int / int` や `int + float` で `int -> float` を指示。
  - `ifexp` の分岐型が `int`/`float` 混在時に昇格指示。

cast 要素は以下形式:

```json
{
  "on": "left | right | body | orelse",
  "from": "int",
  "to": "float",
  "reason": "numeric_promotion | ifexp_numeric_promotion"
}
```

## 9. readonly 判定

関数ごとに `ArgUsageAnalyzer` で引数を解析し、`arg_usage` を付与する。

- `mutable` と判定される条件（少なくとも）:
  - 引数への代入/拡張代入
  - 引数への属性代入・添字代入
  - 破壊的メソッド呼び出し（`append`, `extend`, `pop`, `write_text`, `mkdir` など）
  - 純粋組み込み以外への引数渡し
- それ以外は `readonly`。
- 式ノードの `borrow_kind` は、関数引数参照時に `arg_usage` から反映される。

## 10. 対応ステートメント

現実装で EAST 化する主な文:

- `FunctionDef`, `ClassDef`, `Return`
- `Assign`, `AnnAssign`, `AugAssign`
- `Expr`, `If`, `For`, `While`, `Try`, `Raise`
- `Import`, `ImportFrom`, `Pass`, `Break`, `Continue`

補足:

- `Assign` は単一ターゲットのみ。
- 一部構文はサブセット制約により `unsupported_syntax` となる。

## 11. クラス情報の事前収集

EAST 生成前に次を収集する。

- クラス名集合
- 継承関係（単純名ベース）
- メソッド戻り値型
- フィールド型
  - クラス本体 `AnnAssign`
  - `__init__` 内 `self.field = arg`（引数注釈由来）
  - `self.field: T = ...`

これにより `self.x` 参照や `obj.method()` の戻り型推論を実施する。

## 12. エラー契約

`EastBuildError` は以下 4 項目を持つ。

- `kind`
- `message`
- `source_span`
- `hint`

`kind` は現実装では次を使用する。

- `inference_failure`
- `unsupported_syntax`
- `semantic_conflict`

`SyntaxError` も同形式へ変換して出力する。

## 13. 既知の制約（現時点）

- モジュール `source_span` は `lineno` 等が `null` になる場合がある。
- `borrow_kind` の `move` は未使用。
- 高度なデータフロー解析（エイリアス、厳密な副作用伝播）は未実装。
- すべての Python 構文を網羅するものではない。

## 14. 検証状態

- `test/py` 全32ケースについて `src/east.py` で変換可能（`ok: true`）
- 変換出力は `test/east/case*.json` に配置されている。
