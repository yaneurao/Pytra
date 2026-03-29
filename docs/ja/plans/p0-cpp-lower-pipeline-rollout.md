<a href="../../en/plans/p0-cpp-lower-pipeline-rollout.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: C++ 3段構成移行（案1: `CppLower` / `CppIrOptimizer` / `CppEmitter`）

最終更新: 2026-03-02

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-LOWER-PIPELINE-01`

背景:
- 現在の C++ backend は、`EAST3 -> (EAST3最適化) -> CppEmitter` が中心で、C++ 向けの構造決定が emitter 側へ残っている。
- 既存 `CppOptimizer` は EAST3 ノードを直接扱う pass であり、C++ backend 固有の IR 境界（lower 後の責務）が明示されていない。
- ユーザー合意により、まず C++ だけを対象に案1（`cpp_lower.py` / `cpp_ir_optimizer.py` / `cpp_emitter.py`）で段階移行する。

目的:
- C++ backend の責務を `EAST3 -> CppLower -> CppIrOptimizer -> CppEmitter` に分離し、意味決定・正規化・表記出力の境界を固定する。
- `CppEmitter` を「C++ IR の決定的レンダラ」に縮退し、EAST3 直接解釈ロジックを段階的に削減する。

対象:
- `src/toolchain/emit/cpp/lower/cpp_lower.py`（新設）
- `src/toolchain/emit/cpp/optimizer/cpp_ir_optimizer.py`（新設、既存 optimizer との橋渡し）
- `src/toolchain/emit/cpp/emitter/cpp_emitter.py`（責務縮退）
- `src/py2cpp.py`（新パイプライン配線）
- C++ backend 回帰テスト（unit / transpile / sample）

非対象:
- Rust/Scala/Go など他 backend への同時展開
- EAST2/EAST1 の仕様変更
- C++ runtime API の意味変更

受け入れ基準:
- `py2cpp` 実行時に `CppLower -> CppIrOptimizer -> CppEmitter` の順で必ず処理される。
- `CppEmitter` の migrated 範囲で EAST3 `kind` 分岐依存がなくなり、C++ IR ノード描画に一本化される。
- 既存の C++ transpile 回帰（`tools/check/check_py2cpp_transpile.py`）が非退行で通る。
- `sample/01,08,18` の C++ 再生成でコンパイル可能性と parity を維持する。

確認コマンド（予定）:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_cpp_*lower*.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_*.py' -v`
- `python3 tools/check/check_py2cpp_transpile.py`
- `python3 tools/gen/regenerate_samples.py --langs cpp --stems 01_mandelbrot,08_langtons_ant,18_mini_language_interpreter --force`
- `python3 tools/check/runtime_parity_check.py --case-root sample --targets cpp --all-samples --ignore-unstable-stdout`

## 分解

- [x] [ID: P0-CPP-LOWER-PIPELINE-01-S1-01] C++ IR の最小ノード集合（Stmt/Expr/Type/Decl）と fail-closed 契約を定義する。
- [x] [ID: P0-CPP-LOWER-PIPELINE-01-S1-02] 案1のファイル責務（`cpp_lower.py` / `cpp_ir_optimizer.py` / `cpp_emitter.py`）と公開 API を固定する。
- [x] [ID: P0-CPP-LOWER-PIPELINE-01-S2-01] `cpp_lower.py` を新設し、EAST3 Module から C++ IR Module へ lower する骨格を実装する。
- [x] [ID: P0-CPP-LOWER-PIPELINE-01-S2-02] `cpp_ir_optimizer.py` を新設し、既存 optimizer pass の移設/再配線方針を実装する。
- [x] [ID: P0-CPP-LOWER-PIPELINE-01-S2-03] `py2cpp` から新パイプラインを呼び出す配線と dump/trace 入口を追加する。
- [x] [ID: P0-CPP-LOWER-PIPELINE-01-S3-01] 文単位の構造決定（loop/if/tuple unpack など）を emitter から lower/optimizer 側へ移設する。
- [x] [ID: P0-CPP-LOWER-PIPELINE-01-S3-02] 式単位の正規化（cast/compare/binop の冗長除去）を emitter から lower/optimizer 側へ移設する。
- [x] [ID: P0-CPP-LOWER-PIPELINE-01-S3-03] `CppEmitter` の EAST3 直接分岐を削減し、C++ IR レンダラ責務へ縮退する。
- [x] [ID: P0-CPP-LOWER-PIPELINE-01-S4-01] lower/optimizer/emitter 境界を検証する unit テストを追加し、回帰を固定する。
- [x] [ID: P0-CPP-LOWER-PIPELINE-01-S4-02] C++ transpile/sample/parity を実施し、非退行を確認する。

決定ログ:
- 2026-03-02: ユーザー指示により、他言語展開は後回しにして C++ 先行で案1（`cpp_lower.py` / `cpp_ir_optimizer.py` / `cpp_emitter.py`）を P0 起票。
- 2026-03-02: `CppLower` を `pass_through_v0`（EAST3形状維持）で導入。fail-closed 契約として root `dict` + `kind=Module` を必須化。
- 2026-03-02: `CppIrOptimizer` を既存 `optimize_cpp_ir` への薄い委譲層として導入し、`emit_cpp_from_east` を `lower -> optimizer -> emitter` 配線へ変更。
- 2026-03-02: `dump_cpp_opt_trace` は `cpp_lower_trace` と既存 `cpp_optimizer_trace` を同一ファイルへ連結出力する方式にした（CLI互換維持）。
- 2026-03-02: `CppBraceOmitHintPass` を追加し、`If/ForCore` 等の brace 省略判定を optimizer 側で `cpp_omit_braces_v1` ヒント化。emitter は hint 優先で描画する形へ更新（S3-01 部分着手）。
- 2026-03-02: `CppForIterModeHintPass` を追加し、legacy `For` の `iter_mode` 決定を optimizer 側 `cpp_iter_mode_v1` ヒントへ移設。`pyobj` list model は現状 emitter 側判定を維持。
- 2026-03-02: `CppCastCallNormalizePass` を追加し、`py_to_*` 入れ子と `static_cast` + `py_to_*` の重複キャストを optimizer 側で縮約（S3-02 部分着手）。
- 2026-03-02: `CppCompareNormalizePass` を追加し、`bool_expr == True/False` / `!= True/False` を `bool_expr` / `!bool_expr` へ正規化して compare 冗長性を optimizer 側で縮約（S3-02 部分着手）。
- 2026-03-02: `CppBinOpNormalizePass` を追加し、数値 `+0/-0/*1` の冗長 binop を optimizer 側で縮約。S3-02（cast/compare/binop）を完了扱いへ更新。
- 2026-03-02: `CppForcoreDirectUnpackHintPass` を追加し、`ForCore` tuple target の `direct_unpack` 判定を optimizer 側ヒント化。`CppBraceOmitHintPass` / `CppForIterModeHintPass` と合わせて S3-01（loop/if/tuple unpack）を完了扱いへ更新。
- 2026-03-02: `CppLower` が文ノードへ `cpp_stmt_kind_v1` を付与し、`CppEmitter.emit_stmt` は hint 優先で dispatch する構成へ更新。S3-03 の「EAST3 生 kind 直参照削減」を開始（未完）。
- 2026-03-02: `CppLower` が式ノードにも `cpp_expr_kind_v1` を付与し、`CppEmitter.render_expr` も hint 優先 dispatch へ移行。`_emit_stmt_kind_fallback` をテーブル駆動化し、S3-03 を完了扱いへ更新。
- 2026-03-02: 境界テストとして `test_cpp_optimizer.py` に `CppLower` / `CppIrOptimizer` / `emit_cpp_from_east` の接続検証を追加し、unit 回帰を固定（S4-01）。
- 2026-03-02: `tools/check/check_py2cpp_transpile.py`（136/136 pass, skip6）、`tools/gen/regenerate_samples.py --langs cpp --stems 01_mandelbrot,08_langtons_ant,18_mini_language_interpreter --force`、`tools/check/runtime_parity_check.py --case-root sample --targets cpp 01_mandelbrot 08_langtons_ant 18_mini_language_interpreter --ignore-unstable-stdout`（3/3 pass）で非退行を確認（S4-02）。

## C++ IR v0 契約（S1-01）

- root は `dict` で `kind == "Module"` を必須とする。
- body は従来 EAST3 互換の statement node 群（`Stmt/Expr/Decl/Type` を含む）を許可し、phase-1 では形状を変更しない。
- lower/optimizer の入力が契約違反の場合は `RuntimeError` で fail-closed とする。
- `CppEmitter` には C++ IR root（`Module`）のみを渡す。

## API 境界（S1-02）

- `toolchain.emit.cpp.lower.cpp_lower.CppLower.lower(east_module, debug_flags=...) -> (cpp_ir, report)`
- `toolchain.emit.cpp.lower.cpp_lower.lower_cpp_from_east3(...)` は上記 convenience wrapper。
- `toolchain.emit.cpp.optimizer.cpp_ir_optimizer.CppIrOptimizer.optimize(cpp_ir, ...) -> (cpp_ir, report)`
- `toolchain.emit.cpp.optimizer.cpp_ir_optimizer.optimize_cpp_ir_module(...)` は上記 convenience wrapper。
- `toolchain.emit.cpp.emitter.cpp_emitter.emit_cpp_from_east(...)` は公開 bridge として `lower -> optimizer -> CppEmitter.transpile()` を実行する。
