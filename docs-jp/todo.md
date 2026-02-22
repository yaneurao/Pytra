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

## P3: Pythonic 記法戻し（低優先）

文脈: `docs-jp/plans/p3-pythonic-restoration.md`（`TG-P3-PYTHONIC`）

### `src/py2cpp.py`

1. [ ] [ID: P3-PY-01] `while i < len(xs)` + 手動インデックス更新を `for x in xs` / `for i, x in enumerate(xs)` へ戻す。
2. [ ] [ID: P3-PY-02] `text[0:1] == "x"` のような1文字比較を、selfhost 要件を満たす範囲で `text.startswith("x")` へ戻す。
3. [ ] [ID: P3-PY-03] 空 dict/list 初期化後の逐次代入（`out = {}; out["k"] = v`）を、型崩れしない箇所から辞書リテラルへ戻す。
4. [ ] [ID: P3-PY-04] 三項演算子を回避している箇所（`if ...: a=x else: a=y`）を、selfhost 側対応後に式形式へ戻す。
5. [ ] [ID: P3-PY-05] import 解析の一時変数展開（`obj = ...; s = any_to_str(obj)`）を、型安全が確保できる箇所から簡潔化する。

進捗メモ:
- `P3-PY-01` の一部として `src/py2cpp.py::_sanitize_module_label` の手動インデックス `while` を `for ch in s` へ置換した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）と `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）を確認。
- `P3-PY-02` の一部として `src/py2cpp.py` の `_render_set_literal_repr` で `[:1]` / `[-1:]` 比較を `startswith` / `endswith` へ戻し、同等挙動を維持した。
- `P3-PY-02` の継続として `src/py2cpp.py::_emit_target_unpack` の `list[` / `set[` / `tuple[` / `dict[` 判定をスライス比較から `startswith` / `endswith` へ置換した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）と `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）を確認。
- `P3-PY-02` 周辺の整理として `src/py2cpp.py` のクラス名推定2箇所（`_cpp_type_text`, `_header_cpp_type_from_east`）で `leaf[:1]` 判定を空文字チェック + `leaf[0]` 参照へ統一し、可読性を維持したままスライス依存を削減した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）と `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）を確認。

### `src/pytra/compiler/east_parts/code_emitter.py`

1. [ ] [ID: P3-CE-01] `split_*` / `normalize_type_name` 周辺の index ループを段階的に `for` ベースへ戻す。
2. [ ] [ID: P3-CE-02] `any_*` 系ヘルパで重複する `None`/空文字判定を共通小関数へ集約する。
3. [ ] [ID: P3-CE-03] `_emit_trivia_items` の directive 処理分岐を小関数に分割する。
4. [ ] [ID: P3-CE-04] `hook_on_*` 系で同型の呼び出しパターンを汎用ヘルパ化し、重複を減らす。

### 作業ルール

1. [ ] [ID: P3-RULE-01] 1パッチで戻す範囲は 1〜3 関数に保つ。
2. [ ] [ID: P3-RULE-02] 各パッチで `python3 tools/check_py2cpp_transpile.py` を実行する。
3. [ ] [ID: P3-RULE-03] 各パッチで `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented` を実行する。
4. [ ] [ID: P3-RULE-04] 回帰が出た場合は「可読性改善より selfhost 安定」を優先する。

## メモ

- このファイルは未完了タスクのみを保持します。
- 完了済みタスクは `docs-jp/todo-history/index.md` 経由で履歴へ移動します。
- `docs-jp/todo-history/index.md` は索引のみを保持し、履歴本文は `docs-jp/todo-history/YYYYMMDD.md` に日付単位で保存します。
