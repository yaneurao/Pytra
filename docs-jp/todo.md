# TODO（未完了）

> `docs-jp/` が正（source of truth）です。`docs/` はその翻訳です。

<a href="../docs/todo.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-02-22

## 文脈運用ルール

- 各タスクは `ID` と文脈ファイル（`docs-jp/plans/*.md`）を必須にする。
- 優先度上書きは `docs-jp/plans/instruction-template.md` 形式でチャット指示し、`todo2.md` は使わない。
- 着手前に文脈ファイルの `背景` / `非対象` / `受け入れ基準` を確認する。
- 作業中の判断は文脈ファイルの `決定ログ` へ追記する。

## P0: Selfhost 安定化

文脈: `docs-jp/plans/p0-selfhost-stabilization.md`（`TG-P0-SH`）

1. [ ] [ID: P0-SH-04] `tools/prepare_selfhost_source.py` に残る selfhost 専用スタブ整理を継続する。

進捗メモ:
- `dump_codegen_options_text` の selfhost fallback は最小 `"options:\n"` スタブから、詳細行を出力する selfhost-safe 実装へ置換済み。
- `CodeEmitter.quote_string_literal` / `CodeEmitter.load_profile_with_includes` は本体側 `@staticmethod` 実装へ移行し、`tools/prepare_selfhost_source.py` 側の該当置換経路を削除済み。
- `tools/prepare_selfhost_source.py` から `dump_codegen_options_text` 置換と `main guard` 置換を削除し、正本実装を selfhost へそのまま展開する経路へ移行済み。
- `tools/prepare_selfhost_source.py` から `exception/help` 置換（`_patch_selfhost_exception_paths`）と補助関数 `is_help_requested` を削除し、CLI の正本分岐をそのまま selfhost へ展開する経路へ移行済み。
- `CodeEmitter` hooks no-op 置換は暫定で維持中（除去すると selfhost C++ で `object` callable 解決エラーが発生してビルド失敗）。

## P1: CodeEmitter / Hooks 移行

文脈: `docs-jp/plans/p1-codeemitter-hooks-migration.md`（`TG-P1-CEH`）

1. [ ] [ID: P1-CEH-01] profile で表現しづらいケースだけを hooks へ移し、`py2cpp.py` 側の条件分岐を残さない状態にする。

## P1: CodeEmitter 共通ディスパッチ再設計

文脈: `docs-jp/plans/p1-codeemitter-dispatch-redesign.md`（`TG-P1-CED`）

1. [ ] [ID: P1-CED-01] `render_expr` の kind ごとに hook ポイントを追加する。
2. [ ] [ID: P1-CED-02] `emit_stmt` も kind ごとの hook ポイントへ分解する。
3. [ ] [ID: P1-CED-03] `CppEmitter` を hook 優先 + fallback の二段構成に統一する。
4. [ ] [ID: P1-CED-04] `tools/check_selfhost_cpp_diff.py` で差分ゼロを維持しながら fallback を縮退する。
5. [ ] [ID: P1-CED-05] fallback が十分に減った段階で、共通ディスパッチを `CodeEmitter` 本体へ戻す。

受け入れ基準:
1. [ ] [ID: P1-CED-AC-01] Python 実行パス: `hooks` 有効時に既存ケースのコード生成結果が不変。
2. [ ] [ID: P1-CED-AC-02] selfhost 実行パス: `mismatches=0` を維持。
3. [ ] [ID: P1-CED-AC-03] `py2cpp.py` の `render_expr` / `emit_stmt` 本体分岐が段階的に短くなる。

py2cpp / py2rs 共通化候補:
1. [ ] [ID: P1-CED-A-01] 優先 A: `If` / `While` / `ForRange` / `For` の文スケルトン生成（開閉ブロック + scope push/pop）を `CodeEmitter` へ移す。
2. [ ] [ID: P1-CED-A-02] 優先 A: `Assign` / `AnnAssign` / `AugAssign` の「宣言判定 + 代入先レンダ」共通骨格を `CodeEmitter` へ移す。
3. [ ] [ID: P1-CED-A-03] 優先 A: `Compare` / `BoolOp` / `IfExp` の式組み立てを `CodeEmitter` へ移す。
4. [ ] [ID: P1-CED-A-04] 優先 A: import 束縛テーブル読み込み（`meta.import_bindings` 反映）を `CodeEmitter` へ移す。
5. [ ] [ID: P1-CED-B-01] 優先 B: 型名正規化 + 言語型への最終写像（`normalize_type_name` 後段）を共通化する。
6. [ ] [ID: P1-CED-B-02] 優先 B: `Call` 前処理（`_prepare_call_parts` 結果の共通利用）を共通化する。
7. [ ] [ID: P1-CED-B-03] 優先 B: `Tuple` 代入の一時変数 lower を共通化する。
8. [ ] [ID: P1-CED-C-01] 優先 C: 言語別ランタイム関数へのルーティング（profile + hooks）を共通化する。
9. [ ] [ID: P1-CED-C-02] 優先 C: 文字列/配列の細かい最適化（演算子簡約・括弧削減）を共通化する。

## P1: py2cpp 縮退（行数削減）

文脈: `docs-jp/plans/p1-py2cpp-reduction.md`（`TG-P1-CPP-REDUCE`）

1. [ ] [ID: P1-CPP-REDUCE-01] `src/py2cpp.py` に残る未移行ロジックを `CodeEmitter` へ段階移管し、行数を縮退する。

## P1: コンパイラ共通層への抽出（py2cpp 偏在解消）

文脈: `docs-jp/plans/p1-compiler-shared-extraction.md`（`TG-P1-COMP-SHARED`）

1. [ ] [ID: P1-COMP-01] import グラフ解析（`_analyze_import_graph`）を `src/pytra/compiler/` 配下の共通モジュールへ抽出する。
2. [ ] [ID: P1-COMP-02] module EAST map 構築（`build_module_east_map`）を共通 API 化し、`py2cpp.py` 以外から再利用可能にする。
3. [ ] [ID: P1-COMP-03] module symbol index / type schema 構築（`build_module_symbol_index`, `build_module_type_schema`）を共通 API 化する。
4. [ ] [ID: P1-COMP-04] deps dump（`dump_deps_text`, `dump_deps_graph_text`）を共通 API 化し、CLI 層は表示/出力だけを担当する構成にする。
5. [ ] [ID: P1-COMP-05] 共通抽出後、`py2cpp.py` は C++ 固有責務（C++ runtime/header/multi-file 出力）へ限定する。

## P1: 多言語ランタイム配置統一

文脈: `docs-jp/plans/p1-runtime-layout-unification.md`（`TG-P1-RUNTIME-LAYOUT`）

目的: ランタイム配置を言語間で統一し、責務混在と重複実装を防ぐ。

1. [ ] [ID: P1-RUNTIME-01] Rust ランタイムを `src/rs_module/` から `src/runtime/rs/pytra/` へ段階移行し、`src/runtime/cpp/pytra/` と同等の責務分割（`built_in/`, `std/`, `utils/`, `compiler/`）に揃える。
2. [ ] [ID: P1-RUNTIME-02] `py2rs.py` / Rust hooks のランタイム解決パスを `src/runtime/rs/pytra/` 基準へ更新する。
3. [ ] [ID: P1-RUNTIME-03] `src/rs_module/` の既存参照を洗い出し、互換レイヤを経由して最終的に廃止する。
5. [ ] [ID: P1-RUNTIME-05] 各言語トランスパイラ（`py2cs.py`, `py2js.py`, `py2ts.py`, `py2go.py`, `py2java.py`, `py2kotlin.py`, `py2swift.py`）と hooks のランタイム解決パスを `src/runtime/<lang>/pytra/` 基準へ統一する。

## P1: 多言語出力品質（`sample/cpp` 水準）

文脈: `docs-jp/plans/p1-multilang-output-quality.md`（`TG-P1-MULTILANG-QUALITY`）

1. [ ] [ID: P1-MQ-01] `sample/{rs,cs,js,ts,go,java,swift,kotlin}` の生成品質を計測し、`sample/cpp` 比での差分（過剰 `mut` / 括弧 / cast / clone / 未使用 import）を定量化する。
2. [ ] [ID: P1-MQ-02] 各言語 emitter/hooks/profile に段階的改善を入れ、`sample/cpp` と同等の可読性水準へ引き上げる。
3. [ ] [ID: P1-MQ-03] 多言語の出力品質回帰を防ぐ検査（品質指標 + transpile/smoke）を整備する。
4. [ ] [ID: P1-MQ-04] 非 C++ 各言語（`rs/cs/js/ts/go/java/swift/kotlin`）で、`py2<lang>.py` の selfhost 可否（自己変換した生成物で `sample/py` を再変換できるか）を検証し、言語別ステータスを記録する。
5. [ ] [ID: P1-MQ-05] 非 C++ 各言語で、生成物による再自己変換（多段 selfhost）が成立するかを検証し、失敗要因を分類する。
6. [ ] [ID: P1-MQ-06] 非 C++ 言語の selfhost / 多段 selfhost 検証を定期実行できるチェック導線（手順またはスクリプト）を整備する。
7. [ ] [ID: P1-MQ-07] `sample/` 生成物はタイムスタンプ埋め込みなしで管理し、CI で再生成差分ゼロ（常に最新）を必須化する。

## P2: Any/object 境界整理

文脈: `docs-jp/plans/p2-any-object-boundary.md`（`TG-P2-ANY-OBJ`）

1. [ ] [ID: P2-ANY-01] `CodeEmitter` の `Any/dict` 境界を selfhost でも安定する実装へ段階移行する。
2. [ ] [ID: P2-ANY-02] `cpp_type` と式描画で `object` へのフォールバックを最小化する。
3. [ ] [ID: P2-ANY-03] `Any -> object` が必要な経路と不要な経路を分離し、過剰な `make_object(...)` 挿入を削減する。
4. [ ] [ID: P2-ANY-04] `py_dict_get_default` / `dict_get_node` の既定値が `object` 必須化している箇所を整理する。
5. [ ] [ID: P2-ANY-05] `py2cpp.py` で既定値に `nullopt` を渡している箇所を洗い出し、型別既定値へ置換する。
6. [ ] [ID: P2-ANY-06] selfhost 変換で `std::any` を通る経路を記録・列挙し、段階的に除去する。
7. [ ] [ID: P2-ANY-07] 影響上位3関数単位でパッチを分けて改善し、毎回 `check_py2cpp_transpile.py` を実行する。

## P2: microgpt 変換互換性

文脈: `docs-jp/plans/p2-microgpt-compatibility.md`（`TG-P2-MICROGPT-COMPAT`）

1. [x] [ID: P2-MGPT-01] self_hosted parser の型注釈必須制約（`name: Type`）について、仕様維持するか、無注釈引数の受理/推論を拡張するかを決め、選択した方針を実装へ反映する。
2. [x] [ID: P2-MGPT-02] `pytra.std.random` と `src/runtime/cpp/pytra/std/random.*` に `choices` / `gauss` / `shuffle` を追加し、`py2cpp` 生成コードがコンパイル可能な状態にする。
3. [x] [ID: P2-MGPT-03] `microgpt` 相当入力（最小再現 fixture でも可）で transpile -> C++ 構文チェックまで回す検証導線を追加する。
4. [x] [ID: P2-MGPT-04] （低優先）`work/tmp/microgpt-20260222-lite.py` を `py2cpp.py` で変換し、生成 C++ のコンパイル（`g++ -std=c++20 -I src -I src/runtime/cpp`）が通る状態にする。

進捗メモ:
- `P2-MGPT-01`: 方針を「型注釈必須の仕様維持」に確定。`src/pytra/compiler/east_parts/core.py` で無注釈引数（`def f(x): ...`）の拒否を専用メッセージ（`requires type annotation`）で明示し、`test/fixtures/signature/ng_untyped_param.py` + `test/unit/test_self_hosted_signature.py::test_reject_untyped_parameter` を追加。`docs-jp/spec/spec-user.md` に運用方針を明文化した。
- `P2-MGPT-02`: `src/pytra/std/random.py` へ `choices/gauss/shuffle` を追加し、`python3 src/py2cpp.py src/pytra/std/random.py --emit-runtime-cpp` で `src/runtime/cpp/pytra/std/random.*` を更新。`test/fixtures/stdlib/random_timeit_traceback_extended.py` と `test/unit/test_py2cpp_features.py` に runtime 検証を追加し、`python3 test/unit/test_py2cpp_features.py Py2CppFeatureTest.test_random_timeit_traceback_extended_runtime` で通過を確認。
- `P2-MGPT-03`: `test/fixtures/microgpt/microgpt_compat_min.py`（型注釈付き最小 microgpt 相当ケース）を追加し、`test/unit/test_py2cpp_features.py` に `test_microgpt_compat_min_syntax_check` を追加。`python3 test/unit/test_py2cpp_features.py Py2CppFeatureTest.test_microgpt_compat_min_syntax_check` で transpile -> `g++ -fsyntax-only` の導線が通ることを確認。
- `P2-MGPT-04`: `work/tmp/microgpt-20260222-lite.py` を self_hosted parser 制約に合わせて `microgpt-lite`（dataset -> vocab -> training -> sampling）構成へ再整理し、`random.choices` / `random.gauss` / `random.shuffle` を維持したまま `python3 src/py2cpp.py work/tmp/microgpt-20260222-lite.py -o work/out/microgpt-20260222.cpp` と `g++ -std=c++20 -I src -I src/runtime/cpp -fsyntax-only work/out/microgpt-20260222.cpp` の通過を確認。

## P3: microgpt 原本保全（低優先）

文脈: `docs-jp/plans/p3-microgpt-source-preservation.md`（`TG-P3-MICROGPT-SOURCE-PRESERVATION`）

1. [x] [ID: P3-MSP-01] `materials/inbox/exec-extracted.log` で抽出した原本改変項目（型注釈追加、内包/zip 展開、I/O 置換、アルゴリズム簡略化）を、parser/emitter/runtime の責務へ再分類する。
2. [x] [ID: P3-MSP-02] `materials/microgpt/microgpt-20260222.py` を無改変で `py2cpp` に入力したときの失敗要因を再現・列挙し、改変で迂回していた箇所を実装タスクへ置き換える。
3. [ ] [ID: P3-MSP-03] `work/tmp/microgpt-20260222-lite.py` 依存を縮退し、原本 `materials/microgpt/microgpt-20260222.py` で transpile -> `g++ -fsyntax-only` が通る回帰導線を整備する。
4. [ ] [ID: P3-MSP-04] parser: 無注釈引数（`def f(x): ...`）と class 内 1 行メソッド定義（`def f(...): return ...`）の受理方針を再検討し、原本改変なしで読める範囲を拡張する。
5. [ ] [ID: P3-MSP-05] parser: top-level `for` / tuple 同時代入 / 複数 `for` 内包の受理・lower を段階対応し、原本スクリプト構造を維持して EAST 化できるようにする。
6. [ ] [ID: P3-MSP-06] EAST/emitter: 内包内 `range(...)` の lower 不整合（`unexpected raw range Call in EAST`）を解消する。
7. [ ] [ID: P3-MSP-07] EAST/emitter: `zip` / 内包経由で `object receiver` エラーへ落ちる型崩れ経路を再現し、型解決を安定化する。
8. [ ] [ID: P3-MSP-08] runtime/std: `open` 反復、`list.index`、`random.shuffle(list[str])` など原本依存 API の互換差分を整理し、どのレイヤで吸収するかを確定する。
9. [x] [ID: P3-MSP-09] 回帰導線: 原本 `materials/microgpt/microgpt-20260222.py` を固定入力として、`py2cpp` 失敗要因の再発を検知する手順またはテストを追加する。

進捗メモ:
- `P3-MSP-01`: `materials/inbox/exec-extracted.log`（2026-02-23 00:03〜00:13）と `materials/microgpt/microgpt-20260222.py` vs `work/tmp/microgpt-20260222-lite.py` の差分を照合し、改変 7 項目を parser / emitter / runtime の責務へ再分類した。入力側改変を再発させないため、各項目を実装側で吸収する方針を `docs-jp/plans/p3-microgpt-source-preservation.md` に明記。
- `P3-MSP-02`: `python3 src/py2cpp.py materials/microgpt/microgpt-20260222.py -o work/out/msp2-microgpt.cpp` で先頭エラー（無注釈引数）を再現し、`materials/inbox/exec-extracted.log` の追跡と合わせて失敗要因 A〜F（parser 構文、EAST lower、型崩れ、runtime 互換）を列挙。改変で迂回していた論点を `P3-MSP-04`〜`P3-MSP-09` へ分解して TODO 化。
- `P3-MSP-09`: `tools/check_microgpt_original_py2cpp_regression.py` を追加し、原本 `materials/microgpt/microgpt-20260222.py` 固定入力の transpile/syntax-check 結果を `stage=A..F|SUCCESS` で分類する回帰導線を整備した。`python3 tools/check_microgpt_original_py2cpp_regression.py --expect-stage any-known` で実行可能。

## P3: Pythonic 記法戻し（低優先）

文脈: `docs-jp/plans/p3-pythonic-restoration.md`（`TG-P3-PYTHONIC`）

### `src/py2cpp.py`

1. [ ] [ID: P3-PY-01] `while i < len(xs)` + 手動インデックス更新を `for x in xs` / `for i, x in enumerate(xs)` へ戻す。
2. [x] [ID: P3-PY-02] `text[0:1] == "x"` のような1文字比較を、selfhost 要件を満たす範囲で `text.startswith("x")` へ戻す。
3. [ ] [ID: P3-PY-03] 空 dict/list 初期化後の逐次代入（`out = {}; out["k"] = v`）を、型崩れしない箇所から辞書リテラルへ戻す。
4. [ ] [ID: P3-PY-04] 三項演算子を回避している箇所（`if ...: a=x else: a=y`）を、selfhost 側対応後に式形式へ戻す。
5. [ ] [ID: P3-PY-05] import 解析の一時変数展開（`obj = ...; s = any_to_str(obj)`）を、型安全が確保できる箇所から簡潔化する。

進捗メモ:
- `P3-PY-05` の継続として `src/py2cpp.py::_module_id_from_east_for_graph`、`_module_id_from_east`、`build_module_symbol_index` の `meta` 抽出を `_dict_any_get_dict(...)` へ統一し、`obj -> isinstance -> 代入` 展開を削減した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.53.0 -> 0.54.0`）を確認した。
- `P3-PY-05` の継続として `src/py2cpp.py::_meta_import_bindings`、`_meta_qualified_symbol_refs`、`build_module_east_map` の `meta` 抽出で `obj -> isinstance -> 代入` 展開を `_dict_any_get_dict(...)` へ統一した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.52.0 -> 0.53.0`）を確認した。
- `P3-PY-05` の継続として `src/py2cpp.py` に `_dict_any_get_dict(...)` を追加し、`_write_multi_file_cpp` の `meta/import_modules/import_symbols/functions/arg_types` 読取で `obj -> isinstance -> 代入` の一時展開を削減した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.51.0 -> 0.52.0`）を確認した。
- `P3-PY-01` の継続として `src/py2cpp.py::_graph_cycle_dfs` の `stack` 走査（`nodes` 構築）を index `while` から `for range` へ置換した（外側の `nxts` 走査は回帰履歴のため維持）。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.50.0 -> 0.51.0`）を確認した。
- `P3-PY-05` の継続として `src/py2cpp.py::_analyze_import_graph` の `resolved["path"]` 抽出を `_dict_any_get_str(...)` に統一し、`obj -> isinstance -> 代入` 展開を削減した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.49.0 -> 0.50.0`）を確認した。
- `P3-PY-05` の継続として `src/py2cpp.py::_write_multi_file_cpp` の import symbol 解析で `sym["module"]` / `sig["return_type"]` / `arg_types[an]` 読取を `_dict_any_get_str(...)` に統一し、`obj -> isinstance -> 代入` 展開を簡潔化した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.48.0 -> 0.49.0`）を確認した。
- `P3-PY-05` の継続として `src/py2cpp.py::_module_id_from_east_for_graph` と `_module_id_from_east` の `meta.module_id` 抽出を `_dict_any_get_str(...)` に統一し、`obj -> isinstance -> 代入` 展開を削減した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.47.0 -> 0.48.0`）を確認した。
- `P3-PY-05` の継続として `src/py2cpp.py::build_module_east_map` と `build_module_type_schema` で `module_id/name/return_type` 抽出を `_dict_any_get_str(...)` へ統一し、`obj -> isinstance -> 代入` の一時変数展開を削減した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.46.0 -> 0.47.0`）を確認した。
- `P3-PY-05` の継続として `src/py2cpp.py::_collect_import_modules` と `_validate_from_import_symbols_or_raise` の module/name 抽出で `obj -> isinstance -> 代入` の展開を `_dict_any_get_str(...)` 呼び出しへ統一し、一時変数を削減した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.45.0 -> 0.46.0`）を確認した。
- `P3-PY-05` の継続として `src/py2cpp.py::_meta_import_bindings` / `_meta_qualified_symbol_refs` の `module_id/export_name/local_name/binding_kind/symbol` 抽出で、`*_obj` + 手動 `isinstance` 展開を `_dict_any_get_str(...)` へ統一し一時変数を簡潔化した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.44.0 -> 0.45.0`）を確認した。
- `P3-PY-05` の継続として `src/py2cpp.py::dump_deps_text`（Import/ImportFrom の module/symbol/alias 読取）で `*_obj` からの手動 `isinstance` 展開を `_dict_any_get_str(...)` 呼び出しへ置換し、一時変数を簡潔化した。最初に三項演算子での簡略化を試したが selfhost C++ で `object` と文字列リテラルの型不一致回帰が出たため取り下げ、selfhost-safe 版へ差し替えた。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.43.0 -> 0.44.0`）を確認した。
- `P3-PY-05` の継続として `src/py2cpp.py::build_module_symbol_index`（`import_bindings` 未使用時の fallback）で `import_modules_obj2` / `import_symbols_obj2` の一時変数を削減し、`import_modules` / `import_symbols` への条件式代入へ簡潔化した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.42.0 -> 0.43.0`）を確認した。
- `P3-PY-01` の継続として `src/py2cpp.py::_graph_cycle_dfs` の `nodes` 走査（`disp_nodes` 構築）を index `while` から `for range` へ置換した（index 参照は維持）。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.41.0 -> 0.42.0`）を確認した。
- `P3-PY-01` の継続として `src/py2cpp.py::CppEmitter._fallback_tuple_target_names_from_repr` の `repr_txt` 文字走査を index `while` から `for range` へ置換した（文字取得は `repr_txt[i:i+1]` を維持）。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.40.0 -> 0.41.0`）を確認した。
- `P3-PY-01` の継続として `src/py2cpp.py::_extract_function_signatures_from_python_source` の `lines` 走査（外側）と複数行 `def` 連結（内側）を index `while` から `for range` へ置換し、行スキップ制御は `skip_until` で維持した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.39.0 -> 0.40.0`）を確認した。
- `P3-PY-01` の継続として `src/py2cpp.py::CppEmitter._render_repr_expr`（比較連鎖の `pair_parts` 組み立て）の index `while` を `for range` へ置換した（index 参照は維持）。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.38.0 -> 0.39.0`）を確認した。
- `P3-PY-01` の継続として `src/py2cpp.py::CppEmitter._collect_assigned_name_types`（Tuple 要素走査）、`CppEmitter._emit_noop_stmt`（Import/ImportFrom の `raw_names` 走査）、`CppEmitter.emit_assign`（`fallback_names` 走査）の index `while` を `for range` へ置換した（index 参照は維持）。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.37.0 -> 0.38.0`）を確認した。
- `P3-PY-01` の継続として `src/py2cpp.py::CppEmitter.transpile`（`arg_order` 走査）と `CppEmitter.render_minmax`（`arg_nodes_safe` 走査）の index `while` を `for range` へ置換した（index 参照は維持）。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.36.0 -> 0.37.0`）を確認した。
- `P3-PY-01` の継続として `src/py2cpp.py::CppEmitter._mark_mutated_param_from_target` と `CppEmitter._render_param_default_expr` の `Tuple elements` 走査を index `while` から `for range` へ置換した（index 参照は維持）。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.35.0 -> 0.36.0`）を確認した。
- `P3-PY-01` の継続として `src/py2cpp.py::CppEmitter._collect_import_cpp_includes` と `CppEmitter._seed_import_maps_from_meta` の `bindings/refs` 走査を index `while` から `for range` へ置換した（index 参照は維持）。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.34.0 -> 0.35.0`）を確認した。
- `P3-PY-01` の継続として `src/py2cpp.py::_header_guard_from_path` の `src` 走査と `_header_allows_none_default` の `parts` 走査を index `while` から `for range` へ置換した（index 参照は維持）。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.33.0 -> 0.34.0`）を確認した。
- `P3-PY-01` の継続として `src/py2cpp.py::_sort_str_list_in_place` の `items/out` 走査と `_header_render_default_expr`（Tuple 分岐）の `elements` 走査を index `while` から `for range` へ置換した（index 参照は維持）。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.32.0 -> 0.33.0`）を確認した。
- `P3-PY-01` の継続として `src/py2cpp.py::build_module_symbol_index` の `body_obj` 走査を index `while` から `for range` へ置換した（index 参照は維持）。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.31.0 -> 0.32.0`）を確認した。
- `P3-PY-01` の継続として `src/py2cpp.py::_resolve_user_module_path_for_graph` の `candidates` 走査と `_analyze_import_graph` の `mods` 走査を index `while` から `for range` へ置換した（index 参照は維持）。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.30.0 -> 0.31.0`）を確認した。
- `P3-PY-01` の継続として `src/py2cpp.py::dump_deps_text` の `body_obj` / `import_bindings` / `body` / `Import.names` 走査を index `while` から `for range` へ置換した（index 参照は維持）。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.29.0 -> 0.30.0`）を確認した。
- `P3-PY-01` の継続として `src/py2cpp.py::build_cpp_header_from_east` の `body_obj` / `body` / `arg_order` / `includes` / `class_lines` / `var_lines` / `fn_lines` 走査と、`_resolve_user_module_path` の `candidates` 走査を index `while` から `for range` へ置換した（index 参照は維持）。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.28.0 -> 0.29.0`）を確認した。
- `P3-PY-01` の継続として `src/py2cpp.py::_write_multi_file_cpp` の `files`（2箇所）と `arg_order` 走査を index `while` から `for range` へ置換した（index 参照は維持）。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.27.0 -> 0.28.0`）を確認した。
- `P3-PY-01` の継続として `src/py2cpp.py::build_module_east_map` と `build_module_type_schema` の `files` / `body_obj` / `body` 走査を index `while` から `for range` へ置換した（index 参照は維持）。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.26.0 -> 0.27.0`）を確認した。
- `P3-PY-01` の継続として `src/py2cpp.py::_module_export_table` と `_validate_from_import_symbols_or_raise` の `body` / `targets` / `names` 走査を index `while` から `for range` へ置換した（index 参照は維持）。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.25.0 -> 0.26.0`）を確認した。
- `P3-PY-01` の継続として `src/py2cpp.py::_validate_import_graph_or_raise` の `reserved` / `relative` / `missing` / `cycles` 走査を index `while` から `for range` へ置換した（index 参照は維持）。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.24.0 -> 0.25.0`）を確認した。
- `P3-PY-01` の一部として `src/py2cpp.py::_sanitize_module_label` の手動インデックス `while` を `for ch in s` へ置換した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）と `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）を確認。
- `P3-PY-01` の継続として `src/py2cpp.py::_path_parent_text`（区切り探索）と `_make_user_error`（details 結合）の `while` ループを `for` ベースへ置換した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）と `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）を確認。
- `P3-PY-01` の継続として `src/py2cpp.py::_module_tail_to_cpp_header_path`、`_parse_user_error`、`_header_guard_from_path` の手動インデックス走査を `for` ベースへ置換した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）と `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）を確認。
- `P3-PY-01` の継続として `src/py2cpp.py::_split_infix_once` の手動インデックス探索を `str.find` + スライスへ置換し、同一 API（`(left, right, found)`）を維持した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）と `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）を確認。
- `P3-PY-01` の継続として `src/py2cpp.py::_split_ws_tokens` と `_first_import_detail_line` の手動 index 走査を `for` ベースへ置換した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）と `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）を確認。
- `P3-PY-01` の継続として `src/py2cpp.py::_split_top_level_csv`、`_extract_function_signatures_from_python_source`（params 展開部）、`_extract_function_arg_types_from_python_source` の index `while` を `for` ベースへ置換した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）と `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）を確認。
- `P3-PY-01` の継続として `src/py2cpp.py::cpp_string_lit`、`_split_type_args`、`_split_top_level_union` の index `while` を `for` ベースへ置換した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）と `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）を確認。
- `P3-PY-01` の継続として `src/py2cpp.py::_sort_str_list_in_place`、`CppEmitter.build`（`self.lines` 結合）、`_render_append_like` の index `while` を `for` ベースへ置換した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）と `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）を確認。
- `P3-PY-01` の継続として `src/py2cpp.py::_coerce_args_for_module_function` と `_coerce_py_assert_args` の `args` 走査を `while` + 手動インデックスから `for enumerate` へ置換した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）と `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）を確認。
- `P3-PY-01` の継続として `src/py2cpp.py::_collect_mutated_params`（引数名収集）と `_allows_none_default`（union 走査）の `while` を `for` ベースへ置換した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.13.0 -> 0.14.0`）を確認した。
- `P3-PY-01` の継続として `src/py2cpp.py::_meta_import_bindings`、`_meta_qualified_symbol_refs`、`build_module_symbol_index` の index `while` を段階的に `for` へ置換した（`build_module_symbol_index` の `body_obj` 事前正規化のみ selfhost C++ の `begin/end` 解決回帰回避のため `while` 維持）。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.15.0 -> 0.16.0`）を確認した。
- `P3-PY-01` の継続として `src/py2cpp.py::_runtime_output_rel_tail`（`module_tail` 走査）と `_header_cpp_type_from_east`（union/tuple 走査）の index `while` を `for` ベースへ置換した。`_header_allows_none_default` も同様に試行したが selfhost C++ で `list[str]` 走査が `object` 推論される回帰を確認したため当該箇所は `while` に戻した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.17.0 -> 0.18.0`）を確認した。
- `P3-PY-01` の継続として `src/py2cpp.py::emit_function`（`arg_names` 走査）と `_merge_args_with_kw_by_name`（`args`/`arg_names` 走査）の index `while` を `for` / `enumerate` ベースへ置換した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.18.0 -> 0.19.0`）を確認した。
- `P3-PY-01` の継続として `src/py2cpp.py::_class_method_sig` と `_class_method_name_sig` の `candidates` 走査を `while` から `for i in range(len(candidates))` へ置換した（要素型推論回帰を避けるため index ベースを維持）。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.19.0 -> 0.20.0`）を確認した。
- `P3-PY-01` の継続として `src/py2cpp.py::_fallback_tuple_target_names_from_repr` の `parts`/`nm` 走査を index `while` から `for range` ベースへ置換した（`repr_txt` の文字走査は selfhost 安定のため `while` を維持）。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.20.0 -> 0.21.0`）を確認した。
- `P3-PY-01` の継続として `src/py2cpp.py::_first_import_detail_line`、`_extract_function_signatures_from_python_source`（閉じ括弧探索）、`_extract_function_arg_types_from_python_source` の index `while` を `for range` ベースへ置換した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.21.0 -> 0.22.0`）を確認した。
- `P3-PY-01` の継続として `src/py2cpp.py::dump_deps_text`（`names/modules/symbols` 走査）と `_collect_import_modules`（`body_obj/names_obj` 走査）の index `while` を `for range` ベースへ置換した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.22.0 -> 0.23.0`）を確認した。
- `P3-PY-01` の継続として `src/py2cpp.py::_analyze_import_graph`（`graph_keys/keys/visited_order` 走査）、`_format_graph_list_section`（`items` 走査）、`_format_import_graph_report`（`edges` 走査）の index `while` を `for range` ベースへ置換した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.23.0 -> 0.24.0`）を確認した。
- `P3-PY-05` の一部として `src/py2cpp.py::_meta_import_bindings`、`_meta_qualified_symbol_refs`、`build_module_symbol_index` の import メタ読取で `meta` / `binds` / `refs` / `import_*_obj2` の一時変数展開を条件式代入へ簡潔化した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.14.0 -> 0.15.0`）を確認した。
- `P3-PY-05` の継続として `src/py2cpp.py::_render_isinstance_name_call` の `rhs` 一時変数初期化（`if len(arg_nodes) > 1`）を条件式代入へ簡潔化した。合わせて `_analyze_import_graph` / `build_module_east_map` の同系簡略化も試行したが selfhost C++ で型回帰（`east_cur` 未宣言・`meta["module_id"]` 代入型不一致）が出たため当該2箇所は元の実装へ戻した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.16.0 -> 0.17.0`）を確認した。
- `P3-PY-03` の一部として `src/py2cpp.py::_parse_user_error`、`CppEmitter._prepare_call_parts`、`_resolve_module_name_for_graph` の段階的 dict 構築を辞書リテラル返却へ置換した。selfhost 互換維持のため `_first_import_detail_line` / `_extract_function_arg_types_from_python_source` / `_header_guard_from_path` は `for` を `while` ベースへ戻し、`_sort_str_list_in_place` はソート済みコピー返却 + 呼び出し側再代入へ調整した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.1.0 -> 0.2.0`）を確認した。
- `P3-PY-03` の継続として `src/py2cpp.py::load_cpp_hooks`、`_analyze_import_graph`（戻り値整形部）、`resolve_module_name` の dict 段階構築を辞書リテラル返却へ置換した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.2.0 -> 0.3.0`）を確認した。
- `P3-PY-03` の継続として `src/py2cpp.py::build_module_symbol_index` の `import_symbols` 要素生成（`module/name`）と module index 返却組み立て（`functions/classes/variables/import_*`）を辞書リテラル化した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.3.0 -> 0.4.0`）を確認した。
- `P3-PY-03` の継続として `src/py2cpp.py::CppEmitter._seed_import_maps_from_meta` の symbol import エントリ生成（`module/name`）4箇所を辞書リテラル化した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.4.0 -> 0.5.0`）を確認した。
- `P3-PY-03` の継続として `src/py2cpp.py::_extract_function_signatures_from_python_source`、`_meta_import_bindings`、`_meta_qualified_symbol_refs` の固定キー辞書組み立てを辞書リテラル化した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.5.0 -> 0.6.0`）を確認した。
- `P3-PY-03` の継続として `src/py2cpp.py::CppEmitter._emit_noop_stmt`（`ImportFrom` 分岐）の import symbol エントリ生成2箇所（`module/name`）を辞書リテラル化した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.6.0 -> 0.7.0`）を確認した。
- `P3-PY-03` の継続として `src/py2cpp.py::build_module_type_schema` の `ClassDef` 側 schema 組み立て（`field_types`）と module schema 返却組み立て（`functions/classes`）を辞書リテラル化した（`FunctionDef` 側は selfhost 安定を優先して段階代入のまま維持）。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.7.0 -> 0.8.0`）を確認した。
- `P3-PY-03` の継続として `src/py2cpp.py::_write_multi_file_cpp` の manifest module エントリ組み立て（`module/label/header/source/is_entry`）を辞書リテラル化した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.8.0 -> 0.9.0`）を確認した。
- `P3-PY-03` の継続として `src/py2cpp.py::_write_multi_file_cpp` の manifest 初期組み立て（`entry/include_dir/src_dir`）を辞書リテラル化した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.9.0 -> 0.10.0`）を確認した。
- `P3-PY-03` の継続として `src/py2cpp.py::_write_multi_file_cpp` の manifest 終端組み立て（`modules` 追加と戻り値 `manifest` パス付与）を辞書リテラル化し、`manifest[...]` の段階代入を削減した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.10.0 -> 0.11.0`）を確認した。
- `P3-PY-03` の継続として `src/py2cpp.py::emit_for_each` の `RangeExpr` 分岐で擬似 `ForRange` ノード（`target/target_type/start/stop/step/range_mode/body/orelse`）の段階代入を辞書リテラル化した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.11.0 -> 0.12.0`）を確認した。
- `P3-PY-03` の継続として `src/py2cpp.py::emit_assign`（`pseudo_target`/`rec`）、`render_expr`（`Dict` 分岐の `entries`）、`build_module_type_schema`（`fn_ent`）の固定キー辞書の段階代入を辞書リテラル化した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_transpiler_version_gate.py`（`cpp 0.12.0 -> 0.13.0`）を確認した。
- `P3-PY-02` の一部として `src/py2cpp.py` の `_render_set_literal_repr` で `[:1]` / `[-1:]` 比較を `startswith` / `endswith` へ戻し、同等挙動を維持した。
- `P3-PY-02` の継続として `src/py2cpp.py::_emit_target_unpack` の `list[` / `set[` / `tuple[` / `dict[` 判定をスライス比較から `startswith` / `endswith` へ置換した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）と `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）を確認。
- `P3-PY-02` 周辺の整理として `src/py2cpp.py` のクラス名推定2箇所（`_cpp_type_text`, `_header_cpp_type_from_east`）で `leaf[:1]` 判定を空文字チェック + `leaf[0]` 参照へ統一し、可読性を維持したままスライス依存を削減した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）と `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）を確認。
- `src/py2cpp.py` で `[:1]` / `[-1:]` / `[0:1]` などの1文字スライス比較パターンが検出ゼロになったため、`P3-PY-02` を完了扱いに更新した。

### `src/pytra/compiler/east_parts/code_emitter.py`

1. [x] [ID: P3-CE-01] `split_*` / `normalize_type_name` 周辺の index ループを段階的に `for` ベースへ戻す。
2. [x] [ID: P3-CE-02] `any_*` 系ヘルパで重複する `None`/空文字判定を共通小関数へ集約する。
3. [x] [ID: P3-CE-03] `_emit_trivia_items` の directive 処理分岐を小関数に分割する。
4. [x] [ID: P3-CE-04] `hook_on_*` 系で同型の呼び出しパターンを汎用ヘルパ化し、重複を減らす。

進捗メモ:
- `P3-CE-01` の一部として `src/pytra/compiler/east_parts/code_emitter.py` の `escape_string_for_literal`、`render_compare_chain_common`、`load_import_bindings_from_meta` を `for` ベースへ置換した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）と `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）を確認。
- `P3-CE-01` の継続として `CodeEmitter.load_profile_with_includes` の include 収集/展開ループ（`j/i`）を `for` ベースへ置換した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）と `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）を確認。
- `P3-CE-02` の一部として `src/pytra/compiler/east_parts/code_emitter.py` に `_is_empty_dynamic_text` を追加し、`any_dict_get_str` / `any_to_str` / `get_expr_type` / `_node_kind_from_dict` の重複した空値判定を共通化した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）と `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）を確認。
- `P3-CE-03` の一部として `src/pytra/compiler/east_parts/code_emitter.py` の `_emit_trivia_items` から directive/blank 処理を `_handle_comment_trivia_directive`、`_emit_passthrough_directive_line`、`_emit_blank_trivia_item` へ分離した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）と `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）を確認。
- `P3-CE-04` の一部として `src/pytra/compiler/east_parts/code_emitter.py` に `_lookup_hook` を追加し、`hook_on_emit_stmt` / `hook_on_emit_stmt_kind` / `hook_on_render_expr_kind` / `hook_on_render_expr_leaf` の hook 取得ロジック重複を削減した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）と `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）を確認。
- `P3-CE-04` の継続として `hook_on_stmt_omit_braces` / `hook_on_for_range_mode` / `hook_on_render_call` も `_lookup_hook` 経由へ統一した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）と `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）を確認。
- `src/pytra/compiler/east_parts/code_emitter.py` で `hook_on_*` の `if \"on_*\" in self.hooks` パターンが検出ゼロになったため、`P3-CE-04` を完了扱いに更新した。`P3-CE-03` も `_emit_trivia_items` の directive 分岐分割が完了したため完了扱いに更新した。
- `P3-CE-02` の継続として `render_name_ref` / `attr_name` に残っていた空値判定を `_is_empty_dynamic_text` へ統一し、`code_emitter.py` 内の `{\"\", \"None\", \"{}\", \"[]\"}` 直接判定を helper 定義箇所のみに集約したため、`P3-CE-02` を完了扱いに更新した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）と `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）を確認。
- `P3-CE-01` の継続として `render_constant_common`（bytes repr 引用符探索）の index `while` を `for enumerate` へ置換し、`code_emitter.py` から index 走査の `while i/j/k < len(...)` パターンが検出ゼロになったため、`P3-CE-01` を完了扱いに更新した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）と `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）を確認。

### 作業ルール

1. [ ] [ID: P3-RULE-01] 1パッチで戻す範囲は 1〜3 関数に保つ。
2. [ ] [ID: P3-RULE-02] 各パッチで `python3 tools/check_py2cpp_transpile.py` を実行する。
3. [ ] [ID: P3-RULE-03] 各パッチで `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented` を実行する。
4. [ ] [ID: P3-RULE-04] 回帰が出た場合は「可読性改善より selfhost 安定」を優先する。

## P3: spec 草案整理（低優先）

文脈: `docs-jp/plans/p3-spec-drafts.md`（`TG-P3-SPEC-DRAFTS`）

1. [x] [ID: P3-SD-01] `docs-jp/spec/spec-make.md` の仕様案を実装現状と照合し、採用する項目を既存仕様へ段階移管する。
2. [x] [ID: P3-SD-02] `docs-jp/spec/spec-template.md` の仕様案を実装現状と照合し、採用/保留/非採用の区分を明確化する。

進捗メモ:
- `P3-SD-01`: `spec-make.md` と実装実体（`src/pytra/compiler/transpile_cli.py`, `src/py2cpp.py`, `tools/build_multi_cpp.py`）を照合し、採用済みの multi-file `manifest.json` 契約と build 導線を `docs-jp/spec/spec-dev.md` / `docs-jp/spec/spec-tools.md` へ移管した。未実装の `./pytra --build` / `src/pytra/cli.py` / `tools/gen_makefile_from_manifest.py` は草案維持として `docs-jp/spec/spec-make.md` と `docs-jp/plans/p3-spec-drafts.md` に明記した。
- `P3-SD-02`: `spec-template.md` と実装実体（`src/pytra/std/typing.py`, `src/pytra/compiler/east_parts/core.py`, `src/pytra/compiler/east_parts/code_emitter.py`）を照合し、採用/保留/非採用を区分した。採用項目は `TypeVar` 最小 shim のみとして `docs-jp/spec/spec-pylib-modules.md` へ移管し、`spec-template.md` の「採用」断定表現は「候補」へ修正した。

## メモ

- このファイルは未完了タスクのみを保持します。
- 完了済みタスクは `docs-jp/todo-history/index.md` 経由で履歴へ移動します。
- `docs-jp/todo-history/index.md` は索引のみを保持し、履歴本文は `docs-jp/todo-history/YYYYMMDD.md` に日付単位で保存します。
