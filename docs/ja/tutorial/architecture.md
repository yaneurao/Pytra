# Pytra のアーキテクチャ

Pytra は Python のサブセットを複数のターゲット言語に変換するトランスパイラです。
このページではパイプラインの全体像と、各段の役割を説明します。

## パイプライン概要

```
  .py ソース
      │
      ▼
  ┌─────────┐
  │  parse   │  Python 構文解析
  └────┬─────┘
       │  .py.east1（Python 固有の中間表現）
       ▼
  ┌─────────┐
  │ resolve  │  型解決 + 構文正規化
  └────┬─────┘
       │  .east2（言語非依存の中間表現）
       ▼
  ┌─────────┐
  │ compile  │  core lowering（命令化）
  └────┬─────┘
       │  .east3（最適化前の命令化済み IR）
       ▼
  ┌──────────┐
  │ optimize │  whole-program 最適化
  └────┬─────┘
       │  .east3（最適化済み IR）
       ▼
  ┌─────────┐
  │  link    │  multi-module 結合
  └────┬─────┘
       │  manifest.json + linked east3 群
       ▼
  ┌─────────┐
  │  emit    │  target コード生成
  └────┬─────┘
       │
       ▼
  .go / .cpp / .rs / ...
```

## 各段の役割

### parse（構文解析）

```
入力: .py ファイル
出力: .py.east1（JSON）
```

Python ソースコードを読み込み、EAST1（Extended AST, Stage 1）を生成します。

- 構文解析のみ。型の解決はしません。
- 型注釈はソースに書かれたまま保持されます（`int` は `int` のまま、`int64` にはまだならない）。
- ソースの位置情報（行番号・列番号）、コメント、空行を保持します。
- モジュール単位で完全に独立しており、他のファイルを参照しません。
- 出力ファイルの拡張子が `.py.east1` であることが「Python 由来の EAST1」を示します。

### resolve（型解決 + 構文正規化）

```
入力: *.py.east1（複数モジュール）
出力: *.east2（JSON）
```

EAST1 を受け取り、型解決と Python 固有の構文正規化を行い、言語非依存の EAST2 を生成します。

- **型解決**: 全ての式に型が確定します。`math.sqrt()` の戻り値は `float64` と解決されます。
- **型注釈の正規化**: Python の型名を正規型に変換します。
  - `int` → `int64`, `float` → `float64`, `bytes` → `list[uint8]` 等
- **構文正規化**: Python 固有の構文を言語非依存の表現に変換します。
  - `for x in range(n)` → `ForRange` ノード
  - `Optional[X]` → `X | None`
- **cast 挿入**: 型の不一致がある箇所に自動変換を挿入します。
  - 例: `math.sqrt(int_var)` → 引数に `int64 → float64` の cast を挿入
- **cross-module 型解決**: import 先モジュールの関数シグネチャを参照して型を解決します。
  - `built_in.py` の `len`, `print` 等も同じ仕組みで解決します（ハードコードなし）。
- 出力の拡張子から `.py` が消え `.east2` になることが「Python の意味論が抜けた」ことを示します。

### compile（core lowering）

```
入力: *.east2
出力: *.east3（JSON）
```

EAST2 を受け取り、バックエンド非依存の命令化を行い、EAST3 を生成します。

- **boxing/unboxing の命令化**: 多態的な値の受け渡しを明示的な命令にします。
- **type_id 判定の命令化**: `isinstance` を効率的な型 ID 比較に変換します。
- **反復計画の命令化**: `for` ループを `ForCore` + `iter_plan` に変換します。
- **dispatch_mode の適用**: コンパイル方針（`native` / `type_id`）を EAST3 に反映します。
  この適用は EAST2 → EAST3 の 1 回のみで、後段で再判断しません。

### optimize（whole-program 最適化）

```
入力: *.east3
出力: *.east3（最適化済み、JSON）
```

EAST3 に対して言語非依存の最適化パスを適用します。

- 不要な cast の除去
- リテラル畳み込み
- dead code 除去
- ループ最適化
- escape 解析
- その他の局所最適化

最適化は任意であり、スキップしても正しいコードが生成されます。

### link（multi-module 結合）

```
入力: *.east3（最適化済み）
出力: manifest.json + linked east3 群
```

複数モジュールの EAST3 を結合し、emit に必要な情報をまとめます。

- **import graph 解決**: ユーザーコードが依存する全モジュールを収集します。
- **runtime module 追加**: `built_in/io_ops`, `std/time`, `utils/png` 等の runtime EAST3 を追加します。
- **manifest.json 生成**: entry module、module 一覧、出力パスを記述するマニフェストを生成します。
- **type_id テーブル生成**: クラス継承の型判定用テーブルを確定します。
- **linked_program_v1 metadata**: whole-program 情報を各 module の meta に付与します。

### emit（コード生成）

```
入力: *.east3（最適化済み）
出力: .go / .cpp / .rs / .js 等
```

EAST3 を受け取り、ターゲット言語のソースコードを生成します。

- EAST3 のノードをターゲット言語の構文に写像するだけです。意味の再解釈はしません。
- ランタイムライブラリの配置、import / include の生成も行います。
- 言語ごとに独立した emitter を持ちます（`emit/go/`, `emit/cpp/` 等）。

## EAST とは

EAST（Extended AST）は Pytra の中間表現です。JSON 形式で表現されます。

Python の標準 `ast` モジュールが提供する抽象構文木と異なり、EAST は:

- **コメントと空行を保持** — ソースコードの構造を忠実に反映します。
- **型情報を保持** — 型注釈の解決結果を全ノードに付与します。
- **言語非依存** — EAST2 以降は Python 固有の情報を含みません。
- **段階的に情報が確定** — EAST1（未解決）→ EAST2（型確定）→ EAST3（命令化済み）と進みます。

| 段 | ファイル拡張子 | 型の状態 | 言語依存性 |
|---|---|---|---|
| EAST1 | `.py.east1` | 未解決 | Python 固有 |
| EAST2 | `.east2` | 確定 | 言語非依存 |
| EAST3 | `.east3` | 確定 + 命令化 | 言語非依存 |

## CLI コマンド

通常は `./pytra` で一括実行しますが、各段を個別に実行することもできます。

```bash
# 一括実行（通常使用）
./pytra input.py --target cpp --output-dir out/

# 各段を個別に実行（デバッグ・調査用）
pytra-cli2 -parse input.py -o input.py.east1
pytra-cli2 -resolve input.py.east1 -o input.east2
pytra-cli2 -compile input.east2 -o input.east3
pytra-cli2 -optimize input.east3 -o input.east3
pytra-cli2 -link input.east3 -o out/
pytra-cli2 -emit --target=cpp out/manifest.json -o out/emit/
```

## 対応言語

Pytra は以下の言語への変換をサポートしています:

C++, Rust, C#, JavaScript, TypeScript, Go, Java, Kotlin, Swift, Ruby, Lua, Scala, PHP, Nim, Dart, Julia, Zig

## 関連ドキュメント

- [使い方](./how-to-use.md) — 実行手順、オプション
- [Python 互換性ガイド](../spec/spec-python-compat.md) — 使えない構文、Python との違い
- [EAST2 仕様](../spec/spec-east2.md) — resolve 出力の契約
- [仕様書トップ](../spec/index.md) — 全仕様の入口
