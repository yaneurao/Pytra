# EAST仕様（実装準拠）

<a href="../../docs/spec/spec-east.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>


この文書は `src/pytra/compiler/east.py` / `src/pytra/compiler/east_parts/` の現実装に合わせた EAST 仕様の統合正本である。

統合方針:
- 現行実装準拠の EAST2 仕様と、EAST1/EAST2/EAST3 三段構成の責務仕様をこの文書へ統合する。
- 旧ドキュメント（`spec-east123.md`, `spec-east123-migration.md`, `spec-east1-build.md`）は `docs-ja/spec/archive/` に退役移管する。
- 連結段（`type_id` 決定、manifest、中間ファイル再開）の詳細は [spec-linker.md](./spec-linker.md) を参照する。

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

- `python src/pytra/compiler/east.py <input.py> [-o output.json] [--pretty] [--human-output output.cpp]`
- `--pretty`: 整形 JSON を出力。
- `--human-output`: C++風の人間可読ビューを出力。
- `python src/py2cpp.py <input.py|east.json> [-o output.cpp]`: EASTベースの C++ 生成器。

## 3. トップレベルEAST構造

`east` オブジェクトは以下を持つ。

- `kind`: 常に `Module`
- `east_stage`: 常に `2`（`EAST2`）
- `schema_version`: 整数（現行 `1`）
- `source_path`: 入力パス
- `source_span`: モジュール span
- `body`: 通常のトップレベル文
- `main_guard_body`: `if __name__ == "__main__":` の本体
- `renamed_symbols`: rename マップ
- `meta.import_bindings`: import 正本（`ImportBinding[]`）
- `meta.qualified_symbol_refs`: `from-import` の解決済み参照（`QualifiedSymbolRef[]`）
- `meta.import_modules`: `import module [as alias]` の束縛情報（`alias -> module`）
- `meta.import_symbols`: `from module import symbol [as alias]` の束縛情報（`alias -> {module,name}`）
- `meta.dispatch_mode`: `native | type_id`（コンパイル開始時に確定し、`EAST2 -> EAST3` で意味適用する）

注:
- `meta.dispatch_mode` の意味論適用点は `EAST2 -> EAST3` の 1 回のみで、backend/hook で再判断しない。
- 詳細契約は本書と `docs-ja/spec/spec-linker.md` を正本とする。

`ImportBinding` は次を持つ。

- `module_id`
- `export_name`（`import M` では空文字）
- `local_name`
- `binding_kind`（`module` / `symbol`）
- `source_file`
- `source_line`

`QualifiedSymbolRef` は次を持つ。

- `module_id`
- `symbol`
- `local_name`

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

### 5.1 `leading_trivia` による C++ パススルー記法

- EAST では、パススルーは新ノードを増やさず、既存の `leading_trivia`（`kind: "comment"`）で保持する。
- 解釈対象コメント:
  - `# Pytra::cpp <C++行>`
  - `# Pytra::cpp: <C++行>`
  - `# Pytra::pass <C++行>`
  - `# Pytra::pass: <C++行>`
  - `# Pytra::cpp begin` ... `# Pytra::cpp end`
  - `# Pytra::pass begin` ... `# Pytra::pass end`
- 出力ルール（C++ エミッタ）:
  - directive コメントは通常コメント化（`// ...`）せず、C++ 行としてそのまま出力する。
  - `begin/end` ブロック中の通常コメントは、`#` を除いた本文を C++ 行として順序どおり出力する。
  - 出力位置は `leading_trivia` が付いている文の直前で、文のインデントに合わせる。
  - `blank` trivia は従来どおり空行として維持する。
  - 同一 `leading_trivia` 内の複数 directive は記述順に連結して出力する。
- 優先順位:
  - `leading_trivia` の directive 解釈が最優先。
  - 既存の docstring コメント変換（`"""..."""` -> `/* ... */`）とは独立で、互いに上書きしない。

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
- `byte` は `uint8` に正規化（1文字/1byte用途の注釈エイリアス）。
- `float32/float64` はそのまま保持。
- `any` / `object` は `Any` と同義に扱う。
- C++ ランタイムでの具体表現（`object`, `None`, boxing/unboxing）は [ランタイム仕様](./spec-runtime.md) の `Any` / `object` 表現方針を参照。
- `bytes` / `bytearray` は `list[uint8]` に正規化。
- `pathlib.Path` は `Path` に正規化。
- C++ ランタイムの `str` / `list` / `dict` / `set` / `bytes` / `bytearray` は、STL 継承ではなく wrapper（composition）として実装する。

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
  - 注: `%` の Python/C++ 差異は EAST では吸収しない。
  - EAST は `%` を演算子として保持し、生成器側が `--mod-mode`（`native` / `python`）に応じて出力を切り替える。
- `Subscript`:
- `list[T][i] -> T`
- `dict[K,V][k] -> V`
- `str[i] -> str`
- `list/str` スライスは同型
  - EAST 自体は `Subscript`/`Slice` を保持し、`str-index-mode` / `str-slice-mode` の意味論は生成器側で適用する。
  - 現行 C++ 生成器では `byte` / `native` を実装済み、`codepoint` は未実装。
- `Call`:
- 既知: `int`, `float`, `bool`, `str`, `bytes`, `bytearray`, `len`, `range`, `min`, `max`, `round`, `print`, `write_rgb_png`, `save_gif`, `grayscale_palette`, `perf_counter`, `Path`, `Exception`, `RuntimeError`
- `float(...)`, `round(...)`, `perf_counter()`, `math.*` 主要関数は `float64`
- `bytes(...)` / `bytearray(...)` は `list[uint8]`
- クラスコンストラクタ/メソッドは事前収集した型情報で推論
- `ListComp`: 単一ジェネレータのみ対応
- `BoolOp` (`or`/`and`) は EAST 上では `kind: BoolOp` として保持する。
  - C++ 生成時に、期待型が `bool` のときは真偽演算（`&&`/`||`）として出力する。
  - 期待型が `bool` 以外のときは Python の値選択式として出力する。
    - `a or b` -> `truthy(a) ? a : b`
    - `a and b` -> `truthy(a) ? b : a`
  - 値選択の判定・出力は `src/py2cpp.py` 側で行い、EAST では追加ノードへ lower しない。

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

`dict[str, Any]` の `.get(...).items()` について:

- C++ 生成時は `dict[str, object]` を前提に、`Dict`/`List` リテラル値を `make_object(...)` で再帰変換して初期化する。
- `.get(..., {})` で辞書既定値を与える場合は `dict[str, object]` へ正規化して扱う。

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

## 9. 引数再代入判定（`arg_usage`）

`FunctionDef` ごとに `arg_usage` を付与する。

- 値は `readonly | reassigned` を使う。
- `reassigned` 条件:
  - 引数名への代入/拡張代入（`Assign` / `AnnAssign` / `AugAssign`）
  - `Swap` の左辺/右辺としての引数名
  - `for` / `for range` のターゲットとしての引数名
  - `except ... as name` の `name` が引数名と一致
- 入れ子 `FunctionDef` / `ClassDef` 内の代入は外側関数の判定対象に含めない。
- 上記以外は `readonly`。

現時点では、この情報は主に backend 側の引数 `mut` 判定に利用する。

## 10. 対応文

- `FunctionDef`, `ClassDef`, `Return`
- `Assign`, `AnnAssign`, `AugAssign`
- `Expr`, `If`, `For`, `ForRange`, `While`, `Try`, `Raise`
- `Import`, `ImportFrom`, `Pass`, `Break`, `Continue`

補足:

- `Assign` は単一ターゲット文のみ。
- タプル代入は対応（例: `x, y = ...`, `a[i], a[j] = ...`）。
- 名前ターゲットについては RHS タプル型が分かる場合に型環境を更新。
- `from module import *`（ワイルドカード import）は未対応。

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

- `test/fixtures` 32/32 を `src/pytra/compiler/east.py` で変換可能（`ok: true`）
- `sample/py` 16/16 を `src/pytra/compiler/east.py` で変換可能（`ok: true`）
- `sample/py` 16/16 を `src/py2cpp.py` で「変換→コンパイル→実行」可能（`ok`）

<a id="east-stages"></a>
## 16. 現行の段階構成（2026-02-24）

- EAST は `EAST1 -> EAST2 -> EAST3` の三段で扱う。
- 現行実装では `py2*.py` の既定経路を `EAST3` とする。
- `py2cpp.py` は `--east-stage 3` のみ受理し、`--east-stage 2` はエラーで停止する。
- 非 C++ 8変換器（`py2rs.py`, `py2cs.py`, `py2js.py`, `py2ts.py`, `py2go.py`, `py2java.py`, `py2kotlin.py`, `py2swift.py`）は `--east-stage 2` を移行互換モード（警告付き）として維持する。
- `meta.dispatch_mode` は全段で保持し、意味論適用は `EAST2 -> EAST3` の 1 回のみとする。

### 16.1 段階ごとの責務

- `EAST1`（Parsed）:
  - parser 直後 IR。
  - source span / trivia を保持し、backend 固有ノードは混入させない。
- `EAST2`（Normalized）:
  - 構文正規化 IR。
  - `ForRange` / `RangeExpr`、import 正規化、型解決結果を安定化する。
- `EAST3`（Core）:
  - backend 非依存の意味論確定 IR。
  - boxing/unboxing、`Obj*` 命令、`type_id` 判定、反復計画を明示命令化する。

### 16.1.1 段階境界表（入力/出力/禁止事項/担当ファイル）

| 段 | 入力 | 出力 | 禁止事項 | 担当ファイル |
| --- | --- | --- | --- | --- |
| `EAST1` | `Source`（`.py` / parser backend 指定） | `east_stage=1` の `Module` 文書 | `EAST2/EAST3` 変換、dispatch 意味適用、target 依存ノード生成 | `src/pytra/compiler/east_parts/core.py`, `src/pytra/compiler/east_parts/east1.py` |
| `EAST2` | `EAST1` 文書 | `east_stage=2` の正規化 `Module` 文書 | dispatch 意味適用、boxing/type_id 命令化、backend 構文判断 | `src/pytra/compiler/east_parts/east2.py` |
| `EAST3` | `EAST2` 文書 + `meta.dispatch_mode` | `east_stage=3` の core 命令化 `Module` 文書 | target 言語構文への写像、hook による意味論再判断 | `src/pytra/compiler/east_parts/east3_lowering.py`, `src/pytra/compiler/east_parts/east3.py` |

### 16.2 不変条件

1. `east_stage` とノード形状を一致させる。  
2. `dispatch_mode` の意味適用は `EAST2 -> EAST3` の 1 回だけで行う。  
3. backend / hook は `EAST3` の意味論を再判断しない。  

<a id="east-pipeline"></a>
## 17. パイプライン仕様（統合）

1. `Source -> EAST1`  
2. `EAST1 -> EAST2`（Normalize pass）  
3. `EAST2 -> EAST3`（Core Lowering pass）  
4. `EAST3 -> TargetEmitter`（言語写像）  

補足:
- `--object-dispatch-mode {type_id,native}` はコンパイル開始時に確定し、`EAST2 -> EAST3` で `iter_plan` / `Obj*` 系命令へ反映する。
- backend/hook 側でモード再判定して命令を差し替えてはならない。

<a id="east-file-mapping"></a>
## 18. 現行/移行後の責務対応表（2026-02-24）

| 段 | 責務 | 現行実装（着手時点） | 移行後の正本 |
| --- | --- | --- | --- |
| EAST1 | parser 直後 IR 生成 | `src/pytra/compiler/east_parts/core.py` | `src/pytra/compiler/east_parts/core.py` |
| EAST1 | EAST1 入口 API | `src/pytra/compiler/east_parts/east1.py`（互換ラッパ経由） | `src/pytra/compiler/east_parts/east1.py` |
| EAST2 | EAST1 -> EAST2 正規化 API | `src/pytra/compiler/east_parts/east2.py`（互換ラッパ + selfhost fallback） | `src/pytra/compiler/east_parts/east2.py` |
| EAST3 | EAST2 -> EAST3 lower 本体 | `src/pytra/compiler/east_parts/east3_lowering.py` | `src/pytra/compiler/east_parts/east3_lowering.py` |
| EAST3 | EAST3 入口 API | `src/pytra/compiler/east_parts/east3.py`（互換ラッパ経由） | `src/pytra/compiler/east_parts/east3.py` |
| Bridge | backend 入口（C++） | `src/py2cpp.py`（`--east-stage 3` 専用） | `src/py2cpp.py`（`EAST3` 専用） |
| CLI 互換 | 旧 API 公開 | `src/pytra/compiler/transpile_cli.py` | `src/pytra/compiler/transpile_cli.py`（互換ラッパ専任） |

<a id="east1-build-boundary"></a>
## 19. `EAST1` build 入口の責務境界

目的:
- `.py/.json -> EAST1` build の入口責務を分離し、`transpile_cli.py` の責務を縮退する。

構成:
- `core.py`: self-hosted parser 実装（低レイヤ）
- `east1_build.py`: build 入口（追加対象）
- `east1.py`: stage 契約 helper（薄い API）
- `py2cpp.py`: `_analyze_import_graph` / `build_module_east_map` は `East1BuildHelpers` への委譲のみを担当
- `transpile_cli.py`: `ImportGraphHelpers.analyze_import_graph` / `build_module_east_map` は `east1_build` への thin wrapper（互換公開のみ）

受け入れ条件:
1. `EAST1` build は `east_stage=1` 付与までに限定し、`EAST1 -> EAST2` を行わない。  
2. `load_east_document_compat` のエラー契約（`input_invalid` 系）を維持する。  
3. `transpile_cli.py` は build 本体ロジックを持たず、委譲中心とする。  
4. `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented` を回帰導線に含め、差分発生時は `todo` へ切り出して追跡する。  
5. `test/unit/test_east1_build.py` と `test/unit/test_py2cpp_east1_build_bridge.py` で、`EAST1` 入口契約と `py2cpp` 委譲経路を固定する。  

<a id="east-migration-phases"></a>
## 20. 移行フェーズ（EAST3 主経路化）

1. Phase 0: 契約テスト固定（`EAST3` ルート必須項目、`ForCore`/`iter_plan` 必須性、dispatch 反映点）
2. Phase 1: API 分離（`east1.py` / `east2.py` / `east3.py` へ責務移管）
3. Phase 2: `EAST3` 主経路化（`py2cpp.py` の再判断ロジック棚卸し）
4. Phase 3: hook 分離（移行期間限定で stage 混在を解消）
5. Phase 4: `EAST2` 経路縮退（互換モード化 -> 段階撤去）

補足:
- 各フェーズの進行管理は `docs-ja/todo/index.md` と `docs-ja/plans/plan-east123-migration.md` で行う。
- `Phase 4` の現行運用: 全 `py2*.py` の既定は `--east-stage 3`。`py2cpp.py` は `--east-stage 2` を受理せずエラー停止、非 C++ 8変換器は `warning: --east-stage 2 is compatibility mode; default is 3.` を伴う互換経路を維持する。

## 21. EAST導入の受け入れ基準

- 既存 `test/fixtures` が EAST 経由で変換可能であること。
- 推論失敗時に、`kind` / `source_span` / `hint` を含むエラーを返すこと。
- 仕様差分は文書化し、後段エミッタで暗黙救済しないこと。
- `--object-dispatch-mode` が `EAST2 -> EAST3` のみで適用されること。
- hooks に言語非依存意味論を新規実装しないこと。

## 22. 最低確認コマンド

```bash
python3 tools/check_py2cpp_transpile.py
python3 tools/check_noncpp_east3_contract.py
python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented
```

## 23. 将来拡張（方針）

- `borrow_kind` は現状 `value | readonly_ref | mutable_ref` を使用し、`move` は未使用。
- 将来的には Rust 向けの参照注釈（`&` / `&mut` 相当）へ接続可能な表現を維持する。
  - ただし、Rust 固有の最終判断（所有権・ライフタイム詳細）はバックエンド責務とする。
