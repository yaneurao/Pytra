# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-03-18（S7-03 完了・P5-ANY-ELIM-OBJECT-FREE-01 全完了）

## 文脈運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度上書きは `docs/ja/plans/instruction-template.md` 形式でチャット指示し、`todo2.md` は使わない。
- 着手対象は「未完了の最上位優先度ID（最小 `P<number>`、同一優先度では上から先頭）」に固定し、明示上書き指示がない限り低優先度へ進まない。
- `P0` が 1 件でも未完了なら `P1` 以下には着手しない。
- 着手前に文脈ファイルの `背景` / `非対象` / `受け入れ基準` を確認する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める（例: ``[ID: P0-XXX-01] ...``）。
- `docs/ja/todo/index.md` の進捗メモは 1 行要約に留め、詳細（判断・検証ログ）は文脈ファイル（`docs/ja/plans/*.md`）の `決定ログ` に記録する。
- 1 つの `ID` が大きい場合は、文脈ファイル側で `-S1` / `-S2` 形式の子タスクへ分割して進めてよい（親 `ID` 完了までは親チェックを維持）。
- 割り込み等で未コミット変更が残っている場合は、同一 `ID` を完了させるか差分を戻すまで別 `ID` に着手しない。
- `docs/ja/todo/index.md` / `docs/ja/plans/*.md` 更新時は `python3 tools/check_todo_priority.py` を実行し、差分に追加した進捗 `ID` が最上位未完了 `ID`（またはその子 `ID`）と一致することを確認する。
- 作業中の判断は文脈ファイルの `決定ログ` へ追記する。
- 一時出力は既存 `out/`（または必要時のみ `/tmp`）を使い、リポジトリ直下に新規一時フォルダを増やさない。

## メモ

- このファイルは未完了タスクのみを保持します。
- 完了済みタスクは `docs/ja/todo/archive/index.md` 経由で履歴へ移動します。
- `docs/ja/todo/archive/index.md` は索引のみを保持し、履歴本文は `docs/ja/todo/archive/YYYYMMDD.md` に日付単位で保存します。

## 未完了タスク

### P5

1. [ ] [ID: P5-ANY-ELIM-OBJECT-FREE-01] `Any` アノテーションを禁止し、C++ ランタイムから `object`/`PyObj` 階層を除去する。`extern` 未知型は C++ テンプレート透過、クラス多態性は `rc<Base>` へ、stdlib 内部 `object` は closed 型へ置き換え。
文脈: [docs/ja/plans/p5-any-elimination-object-free.md](../plans/p5-any-elimination-object-free.md)
  - [ID: P5-ANY-ELIM-OBJECT-FREE-01-S1-01] 完了: `Any`/`object` 全量調査。std: `json.py`(S3)、`enum.py`/`argparse.py`(S2)、`sys.py`(S5)、`assertions.py`(S2)。emitter: `is_any_like_type`×80+、`make_object`×22、`"public PyObj"` 自動挿入(S4)。決定ログに分類・フェーズ割当記録済み。
  - [ID: P5-ANY-ELIM-OBJECT-FREE-01-S1-02] 完了: extern 未知型設計仕様固定。`extern_var_v1` schema v2 拡張、`extern auto {name};` emit 方針、メタデータ収集拡張（`Any`以外のアノテーション対応）を決定ログに記録。
  - [ID: P5-ANY-ELIM-OBJECT-FREE-01-S1-03] 完了: クラス多態性 rc<Base> 設計仕様固定。`public PyObj` → `public RcObject` 変更方針、type_id 比較での `isinstance` 実装、`list<rc<Base>>` への直接 emit 方針を決定ログに記録。
  - [ID: P5-ANY-ELIM-OBJECT-FREE-01-S1-04] 完了: JSON/stdlib 置き換え設計仕様固定。`JsonValue` 再帰 union 型方針、`assertions.py`/`json_adapters.py` 対応フェーズを決定ログに記録。
  - [ID: P5-ANY-ELIM-OBJECT-FREE-01-S2-01] 完了: `AnyAnnotationProhibitionPass` 新規実装。`FunctionDef.arg_types`/`return_type` と `AnnAssign.annotation` を検査し `Any` 検出時に `RuntimeError` raise。デフォルト無効（stdlib 移行後に有効化）。ユニットテスト 20 件 pass。
  - [ID: P5-ANY-ELIM-OBJECT-FREE-01-S2-02] 完了: stdlib の `Any` 移行。`enum.py`（`object`/具体型に変換）、`argparse.py`（`str | bool | None` に変換）、`json.py`（`dumps(obj: object)`）。`AnyAnnotationProhibitionPass` による検証 PASS。
  - [ID: P5-ANY-ELIM-OBJECT-FREE-01-S2-03] 完了: `Any` 禁止ドキュメント整備。`docs/ja/spec/spec-any-prohibition.md` 新規作成。移行手順・エラーガイド・パス有効化方法を記載。
  - [ID: P5-ANY-ELIM-OBJECT-FREE-01-S3-01] 完了: `json.py` 内部表現を `_JsonVal` closed 型へ移行。`JsonObj.raw: dict[str,_JsonVal]`、`_jv_to_object`/`_object_to_jv` を `json_adapters.py` に追加。decode boundary ガード 8 ファイル対応済み。
  - [ID: P5-ANY-ELIM-OBJECT-FREE-01-S3-02] 完了: `assertions.py` の `object` 除去。`_eq_any` / `py_assert_eq` 引数型を `str | int | float | bool | None` へ変更。`py_assert_stdout fn: object`（callable stub）・`enum.py`（S4）・`sys.py`（S5-01）は後続フェーズで対応。
  - [ID: P5-ANY-ELIM-OBJECT-FREE-01-S4-01] 完了: ユーザー定義 ref クラス基底を `PyObj` → `RcObject` に変更。emitter・`gc.h`（py_type_id() 仮想追加）・`py_runtime.h`（rc<T> isinstance 特殊化）を更新。
  - [ID: P5-ANY-ELIM-OBJECT-FREE-01-S4-02] 完了: `obj_to_rc<T>` の `static_assert` を `PyObj` → `RcObject` に緩和。`list[Base]` → `list<rc<Base>>` emit はすでに正しく動作していた。
  - [ID: P5-ANY-ELIM-OBJECT-FREE-01-S4-03] 完了: S4-01 で実装済み（`py_runtime_value_isinstance` の `rc<T>` 特殊化で `py_type_id()` 仮想比較を使用、type_id 比較方式に固定）。
  - [ID: P5-ANY-ELIM-OBJECT-FREE-01-S5-01] 完了: `sys.py` の `stderr`/`stdout` から `object` アノテーションを除去。`sys.h` の `extern object stderr;` が消去された。`core_extern_semantics.py` に `object`/`""` アノテーションサポートを追加。
  - [ID: P5-ANY-ELIM-OBJECT-FREE-01-S6-01] 完了: `py_runtime.h` から `PyObj` 継承階層（`PyIntObj` 等 7 クラス + イテレータ）を除去。`gc.h` の `class PyObj` も削除。`gc.cpp` に `RcObject` 仮想メソッド実装を追加。
  - [ID: P5-ANY-ELIM-OBJECT-FREE-01-S6-02] 完了: `object` を `rc<RcObject>` に再定義。`make_object`/`obj_to_*`/`py_to<T>(const object&)` を除去。`json.py` dumps 系を `_JsonVal` ベースに変更。`py_any`/`py_all` を typed template に変更。
  - [ID: P5-ANY-ELIM-OBJECT-FREE-01-S6-03] 完了: `cpp_list_model=pyobj` テスト削除、boxing テスト削除。`list.h`/`dict.h`/`set.h` の `object` 変換演算子を除去。319件実行、pre-existing 以外の非退行なし。
  - [ID: P5-ANY-ELIM-OBJECT-FREE-01-S7-01] 完了: S6 起因 regression を修正。`py_assert_*` を template 化、`contains`/`iter_ops` の dead object 関数を除去。fixture 3/3・sample 18/18 pass。
  - [ID: P5-ANY-ELIM-OBJECT-FREE-01-S7-02] 完了: selfhost diff / direct compile 非退行確認 (mismatches=0, failures=0)。
  - [ID: P5-ANY-ELIM-OBJECT-FREE-01-S7-03] 完了: `docs/en/todo/index.md` に S3-01〜S7-02 進捗を追加。`spec-any-prohibition.md`（ja/en）更新。`spec-boxing.md`（ja/en）に廃止済みノート追加。
