# TODO（未完了）

> `docs-jp/` が正（source of truth）です。`docs/` はその翻訳です。

<a href="../docs/todo.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-02-22

## P0: Selfhost 安定化

1. [ ] selfhost `.py` 経路の段階回復を完了する。
2. [ ] `selfhost/py2cpp.out` の最小実行経路を安定化する（入力/生成/実行の end-to-end を常に再現可能にする）。
3. [ ] selfhost のコンパイルエラーを段階的にゼロ化する（回帰時の即時再検出手順を含む）。
4. [ ] `tools/prepare_selfhost_source.py` に残る selfhost 専用スタブ整理を継続する。
   - [x] `dump_codegen_options_text` の selfhost fallback を最小 `"options:\n"` スタブから、詳細行を出力する selfhost-safe 実装へ置換済み。
   - [x] `CodeEmitter.quote_string_literal` / `CodeEmitter.load_profile_with_includes` を本体側 `@staticmethod` 実装へ移行し、`tools/prepare_selfhost_source.py` 側の該当置換経路を削除済み。

## P1: CodeEmitter / Hooks 移行

1. [ ] profile で表現しづらいケースだけを hooks へ移し、`py2cpp.py` 側の条件分岐を残さない状態にする。

## P1: CodeEmitter 共通ディスパッチ再設計

1. [ ] `render_expr` の kind ごとに hook ポイントを追加する。
2. [ ] `emit_stmt` も kind ごとの hook ポイントへ分解する。
3. [ ] `CppEmitter` を hook 優先 + fallback の二段構成に統一する。
4. [ ] `tools/check_selfhost_cpp_diff.py` で差分ゼロを維持しながら fallback を縮退する。
5. [ ] fallback が十分に減った段階で、共通ディスパッチを `CodeEmitter` 本体へ戻す。

### 受け入れ基準

1. [ ] Python 実行パス: `hooks` 有効時に既存ケースのコード生成結果が不変。
2. [ ] selfhost 実行パス: `mismatches=0` を維持。
3. [ ] `py2cpp.py` の `render_expr` / `emit_stmt` 本体分岐が段階的に短くなる。

### py2cpp / py2rs 共通化候補

1. [ ] 優先 A: `If` / `While` / `ForRange` / `For` の文スケルトン生成（開閉ブロック + scope push/pop）を `CodeEmitter` へ移す。
2. [ ] 優先 A: `Assign` / `AnnAssign` / `AugAssign` の「宣言判定 + 代入先レンダ」共通骨格を `CodeEmitter` へ移す。
3. [ ] 優先 A: `Compare` / `BoolOp` / `IfExp` の式組み立てを `CodeEmitter` へ移す。
4. [ ] 優先 A: import 束縛テーブル読み込み（`meta.import_bindings` 反映）を `CodeEmitter` へ移す。
5. [ ] 優先 B: 型名正規化 + 言語型への最終写像（`normalize_type_name` 後段）を共通化する。
6. [ ] 優先 B: `Call` 前処理（`_prepare_call_parts` 結果の共通利用）を共通化する。
7. [ ] 優先 B: `Tuple` 代入の一時変数 lower を共通化する。
8. [ ] 優先 C: 言語別ランタイム関数へのルーティング（profile + hooks）を共通化する。
9. [ ] 優先 C: 文字列/配列の細かい最適化（演算子簡約・括弧削減）を共通化する。

## P1: py2cpp 縮退（行数削減）

1. [ ] `src/py2cpp.py` に残る未移行ロジックを `CodeEmitter` へ段階移管し、行数を縮退する。

## P2: Any/object 境界整理

1. [ ] `CodeEmitter` の `Any/dict` 境界を selfhost でも安定する実装へ段階移行する。
2. [ ] `cpp_type` と式描画で `object` へのフォールバックを最小化する。
3. [ ] `Any -> object` が必要な経路と不要な経路を分離し、過剰な `make_object(...)` 挿入を削減する。
4. [ ] `py_dict_get_default` / `dict_get_node` の既定値が `object` 必須化している箇所を整理する。
5. [ ] `py2cpp.py` で既定値に `nullopt` を渡している箇所を洗い出し、型別既定値へ置換する。
6. [ ] selfhost 変換で `std::any` を通る経路を記録・列挙し、段階的に除去する。
7. [ ] 影響上位3関数単位でパッチを分けて改善し、毎回 `check_py2cpp_transpile.py` を実行する。

## P3: Pythonic 記法戻し（低優先）

### `src/py2cpp.py`

1. [ ] `while i < len(xs)` + 手動インデックス更新を `for x in xs` / `for i, x in enumerate(xs)` へ戻す。
2. [ ] `text[0:1] == "x"` のような1文字比較を、selfhost 要件を満たす範囲で `text.startswith("x")` へ戻す。
3. [ ] 空 dict/list 初期化後の逐次代入（`out = {}; out["k"] = v`）を、型崩れしない箇所から辞書リテラルへ戻す。
4. [ ] 三項演算子を回避している箇所（`if ...: a=x else: a=y`）を、selfhost 側対応後に式形式へ戻す。
5. [ ] import 解析の一時変数展開（`obj = ...; s = any_to_str(obj)`）を、型安全が確保できる箇所から簡潔化する。

### `src/pytra/compiler/east_parts/code_emitter.py`

1. [ ] `split_*` / `normalize_type_name` 周辺の index ループを段階的に `for` ベースへ戻す。
2. [ ] `any_*` 系ヘルパで重複する `None`/空文字判定を共通小関数へ集約する。
3. [ ] `_emit_trivia_items` の directive 処理分岐を小関数に分割する。
4. [ ] `hook_on_*` 系で同型の呼び出しパターンを汎用ヘルパ化し、重複を減らす。

### 作業ルール

1. [ ] 1パッチで戻す範囲は 1〜3 関数に保つ。
2. [ ] 各パッチで `python3 tools/check_py2cpp_transpile.py` を実行する。
3. [ ] 各パッチで `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented` を実行する。
4. [ ] 回帰が出た場合は「可読性改善より selfhost 安定」を優先する。

## Docs 翻訳同期

1. [ ] `docs-jp/todo-history/YYYYMMDD.md` を正として、`docs/todo-history/YYYYMMDD.md` への翻訳同期フローを整備する（今は未実施）。

## メモ

- このファイルは未完了タスクのみを保持します。
- 完了済みタスクは `docs-jp/todo-old.md` へ移動します。
- `docs-jp/todo-old.md` は索引のみを保持し、履歴本文は `docs-jp/todo-history/YYYYMMDD.md` に日付単位で保存します。
