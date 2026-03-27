<a href="../../ja/plans/p7-selfhost-multimodule-transpile.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p7-selfhost-multimodule-transpile.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p7-selfhost-multimodule-transpile.md`

# P7: selfhost multi-module transpile 基盤構築

最終更新: 2026-03-19

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P7-SELFHOST-MULTIMOD-TRANSPILE-01`
- 親タスク: `ID: P7-SELFHOST-NATIVE-COMPILER-ELIM-01`（S2 の前提）

## 背景

selfhost バイナリの `backend_registry_static.cpp::emit_source_typed` は `python3 src/east2x.py` にシェルアウトして C++ コードを生成している。これを除去するには C++ emitter（`CppEmitter` + 全依存モジュール）を C++ に transpile して selfhost バイナリに組み込む必要がある。

現在の selfhost transpile は単一ファイル生成（`pytra-cli.py` → `selfhost/py2cpp.cpp`）であり、import 先モジュールの C++ コードは含まれない。P2 で実装した compile → link パイプラインを selfhost ビルド自体に適用し、emitter モジュール群を multi-module transpile → link する仕組みが必要。

## 設計

### パイプライン

```
# Step 1: 各モジュールを個別に compile
pytra compile src/pytra-cli.py -o work/selfhost/py2x_selfhost.east
pytra compile src/toolchain/emit/cpp/emitter/cpp_emitter.py -o work/selfhost/cpp_emitter.east
pytra compile src/toolchain/emit/cpp/emitter/class_def.py -o work/selfhost/class_def.east
...（emitter の全依存モジュール）

# Step 2: link → C++ 出力（multi-file）
pytra link work/selfhost/*.east --target cpp -o selfhost/cpp/

# Step 3: compile C++ → selfhost バイナリ
g++ -std=c++20 -O2 -Isrc -Isrc/runtime/cpp selfhost/cpp/src/*.cpp <runtime_sources> -o selfhost/py2cpp.out
```

### 前提条件

1. emitter モジュール群が selfhost 対象コードの制約を満たすこと:
   - 動的 import 不使用
   - `ast` モジュール不使用
   - Python 標準モジュール直接 import 不使用（`pytra.std.*` 経由）
2. compile → link パイプラインが multi-module C++ 出力を生成できること（P2 で実装済み）
3. `pytra link` の multi-file C++ 出力が selfhost ビルドでコンパイルできること

### 主要な課題

- emitter コードが selfhost 制約を満たさない可能性（動的 dispatch、`globals()` 操作、`setattr` 等）
- emitter の依存モジュール数が多い（`CodeEmitter`, profile loader, optimizer, lower 等）
- generated C++ headers（`string_ops.h` 等）のビルド環境整備

## 対象

- `tools/build_selfhost.py` — multi-module transpile パイプラインへの拡張
- `src/pytra-cli.py` — `emit_source_typed` シェルアウトを直接 emitter 呼び出しに置換
- `src/runtime/cpp/compiler/backend_registry_static.cpp` — `emit_source_typed` シェルアウト除去
- emitter モジュール群（`src/toolchain/emit/cpp/emitter/*.py`）— selfhost 制約準拠の確認・修正

## 非対象

- 非 C++ バックエンドの selfhost 対応
- emitter の完全リファクタリング（selfhost 制約違反箇所の最小修正に限定）

## 受け入れ基準

- [ ] selfhost ビルドが emitter を含む multi-module transpile で C++ バイナリを生成できる。
- [ ] `backend_registry_static.cpp` の `emit_source_typed` がシェルアウトなしで動作する。
- [ ] selfhost diff mismatches=0。

## 子タスク

- [x] [ID: P7-SELFHOST-MULTIMOD-TRANSPILE-01-S1] emitter モジュール群の selfhost 制約準拠を監査し、違反箇所を列挙する。
- [x] [ID: P7-SELFHOST-MULTIMOD-TRANSPILE-01-S2] `tools/build_selfhost.py` を multi-module transpile パイプライン（compile → link）に拡張する。
- [ ] [ID: P7-SELFHOST-MULTIMOD-TRANSPILE-01-S3] `pytra-cli.py` から `emit_cpp_from_east` を直接呼び出し、`backend_registry_static.cpp` の `emit_source_typed` シェルアウトを除去する。
- [x] [ID: P7-SELFHOST-MULTIMOD-TRANSPILE-01-S4] リンカーの import 解決で wildcard re-export が export テーブルに反映されない問題を修正する。

## 決定ログ

- 2026-03-19: P7-S2 調査の結果、selfhost transpile が単一ファイル生成であり emitter の依存グラフが含まれないことが判明。multi-module transpile 基盤の構築が前提条件として起票。
- 2026-03-20: S1 制約違反を修正。stdlib import 3件を pytra.std 経由に移行（pathlib.Path に relative_to/with_suffix を実装、pytra.std.re に compile/Pattern を実装）。動的 dispatch 4件は CppEmitter を多重継承に変更し setattr/__dict__/globals() を除去。EAST3 mixin 展開を新規実装し transpile 対象の多重継承をサポート。
- 2026-03-20: S2 着手調査。emitter モジュールの EAST3 コンパイルを試みたが `from typing import Any` が `unsupported_syntax` で拒否される。emitter 全ファイル（13+）の `typing` import を `pytra.typing` に移行する前提作業が必要。
- 2026-03-20: S1 監査完了。結果:
  - **#1 動的 import**: 違反なし
  - **#2 ast モジュール**: 違反なし
  - **#3 直接 stdlib import**: 4件 (module.py:pathlib, profile_loader.py:pathlib, multifile_writer.py:os, cpp_optimizer.py:re)
  - **#4 動的 dispatch**: 4件 (cpp_emitter.py:145 globals(), :166-173 __dict__/setattr) — `install_py2cpp_runtime_symbols` と `_attach_cpp_emitter_helper_methods` が翻訳不可能パターン
  - **#5 continue**: ~170件 — 自動変換可能だが広範囲
  - **#6 literal set membership**: ~330件 — 自動変換可能だが広範囲
  - **ブロッカー**: #4 の動的 dispatch 4件。`_attach_cpp_emitter_helper_methods` は mixin パターンで CppEmitter にヘルパーメソッドを動的注入しており、C++ では静的多重継承またはテンプレート CRTP に置換が必要。
- 2026-03-20: S2 実装完了。パーサー修正 3 件（typing/dataclasses no-op import 許容、dict 文字列キー内 `:` 対応、複数型引数 subscript 対応）。コンパイラバグ修正 4 件（TypeExpr sync、EAST3 validator 2 件、optimizer fold）。全 150 モジュールの個別 EAST3 コンパイルに成功。依存チェーン全体（40+ ファイル）の object レシーバを dict[str, Any] 型ローカルに修正。global 文を mutable list holder に置換。typing import を pytra.typing に移行（emitter/optimizer 34 ファイル）。EAST3 mixin 展開を新規実装。
- 2026-03-20: リンク段階で `from toolchain.misc.transpile_cli import make_user_error` 等のシンボル解決に失敗。全モジュール個別コンパイルは成功しているが、リンカーの export/import マッチングが未解決。S4 として起票。
- 2026-03-20: S4 解決。根本原因: `module_export_table` が `from X import *`（wildcard re-export）を export セットに反映していなかった。`toolchain.misc.transpile_cli` は `from toolchain.frontends.transpile_cli import *` で全シンボルを再エクスポートする shim だが、wildcard がスキップされていたため consumer 側で 36 件の `missing_symbol` エラー発生。修正: (1) `module_export_table` に wildcard re-export の推移的展開ループを追加（`__all__` フィルタリング対応）。(2) wildcard バインディング時の既存明示 import との重複をエラーではなくスキップに変更。検証: 151 モジュールの link 成功（95秒）。後続の `optimize_linked_program` は 151 モジュール規模で 10 分超タイムアウト（別問題）。
- 2026-03-20: optimizer の `_build_type_id_table` で `TypedDict` が未知の基底型としてエラー。`_ROOT_BASE_NAMES` に追加して解決。151 モジュールの optimize が 413 秒で完了。
- 2026-03-21: S3 着手。`pytra-cli.py` に `--output-dir` 対応の multi-file C++ emit パスを追加。`type_bridge.py` の Any 含有 union 型を `object` に退化させる修正。151 モジュールの emit 段階で `str.startswith` の BuiltinCall lowering 未対応エラーが残存。lowering パスが multi-module selfhost 規模のコードに対して不完全。
- 2026-03-21: str メソッド BuiltinCall 未 lower 問題を解決。根本原因: linked doc の `source_path=""` で `_render_selfhost_builtin_method_call` の source_path ホワイトリストが通過しなかった。ホワイトリストに `src == ""` を追加。`str.replace` の 3 引数（count）サポートを追加（`py_replace_n`）。次のブロッカー: 一部モジュールで `object receiver attribute/method access` 制約違反。
- 2026-03-21: PowerShell emitter の object receiver 制約違反を全修正（96 行の型注釈追加）。151 モジュールの EAST3 コンパイル → link → optimize → emit パイプラインが emit 段階まで到達。次のブロッカー: C++ emitter が Slice ノードを単独で処理できない（通常は Subscript 内で処理）。
- 2026-03-21: emit 段階の修正 3 件: (1) cpp_emitter.py の list スライス代入を insert ループに置換（Slice ノード問題解消）。(2) module.py の `_module_class_signature_docs` に sentinel キャッシュ導入（クラス型解決の無限再帰を防止）。(3) multifile_writer.py の再帰制限を 10000 に引き上げ。全修正適用後、151 モジュールの emit はエラーなく動作するが性能問題あり。
- 2026-03-21: emit 性能プロファイル。9 分で 29/151 モジュール完了（平均 18 秒/モジュール）。151 モジュール完了に推定 ~45 分。ボトルネック: 各モジュールの `optimize_cpp_ir` + `CppEmitter.transpile()` が独立に実行され、大規模 emitter ファイル（cs_emitter.py 等）で特に遅い。性能改善案: (a) emit 対象を selfhost に必要なモジュールのみに限定、(b) C++ optimizer/emitter のキャッシュ改善、(c) emit 並列化。
