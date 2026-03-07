# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-03-07

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

### P0: C++ core runtime の `.ext` suffix 退役（plain naming 化）

文脈: [docs/ja/plans/p0-cpp-core-ext-suffix-retire.md](../plans/p0-cpp-core-ext-suffix-retire.md)

1. [ ] [ID: P0-CPP-CORE-EXT-SUFFIX-RETIRE-01] C++ core runtime から `.ext` suffix を退役し、`core` surface / `native/core` 正本 / `generated/core` lane を plain file name 契約へ揃える。
2. [x] [ID: P0-CPP-CORE-EXT-SUFFIX-RETIRE-01-S1-01] `core/*.ext.h` と `native/core/*.ext.{h,cpp}` の rename inventory を作り、plain name 対応表を決定ログへ固定する。
3. [ ] [ID: P0-CPP-CORE-EXT-SUFFIX-RETIRE-01-S1-02] `core` は shim、`native/core` は ownership 正本、`generated/core` は plain naming future lane とする命名契約を plan/spec に固定する。
4. [ ] [ID: P0-CPP-CORE-EXT-SUFFIX-RETIRE-01-S2-01] `runtime_symbol_index` / `cpp_runtime_deps.py` / layout guard を rename 耐性ありの導線へ拡張し、移行中でも source/header 解決が通るようにする。
5. [ ] [ID: P0-CPP-CORE-EXT-SUFFIX-RETIRE-01-S2-02] synthetic test を追加し、`core/*.h` + `native/core/*.{h,cpp}` の plain naming で compile/source 解決できることを固定する。
6. [ ] [ID: P0-CPP-CORE-EXT-SUFFIX-RETIRE-01-S3-01] `src/runtime/cpp/core/*.ext.h` を `*.h` へ rename し、forwarder surface を plain name へ切り替える。
7. [ ] [ID: P0-CPP-CORE-EXT-SUFFIX-RETIRE-01-S3-02] backend / generated runtime / native companion / tests の include を `runtime/cpp/core/*.h` へ更新し、`runtime/cpp/core/*.ext.h` 依存を除去する。
8. [ ] [ID: P0-CPP-CORE-EXT-SUFFIX-RETIRE-01-S4-01] `src/runtime/cpp/native/core/*.ext.h` / `*.ext.cpp` を plain name へ rename し、public forwarder と compile source の参照先を同期する。
9. [ ] [ID: P0-CPP-CORE-EXT-SUFFIX-RETIRE-01-S4-02] runtime symbol index / parity tool / representative tests を plain `native/core/*.{h,cpp}` 前提へ更新し、旧 `.ext` path を返さないことを固定する。
10. [ ] [ID: P0-CPP-CORE-EXT-SUFFIX-RETIRE-01-S5-01] `generated/core` の plain naming rule を README/spec/guard に固定し、future artifact が `.ext` を再導入しないようにする。
11. [ ] [ID: P0-CPP-CORE-EXT-SUFFIX-RETIRE-01-S5-02] fallback / docs / archive / guard を更新し、core runtime の `.ext` naming を完了扱いで閉じる。

### P0: C++ mutable list の ref-first 完全化（`rc<list<T>>` 正本化）

文脈: [docs/ja/plans/p0-cpp-list-ref-first-completion.md](../plans/p0-cpp-list-ref-first-completion.md)

1. [ ] [ID: P0-CPP-LIST-REFFIRST-01] C++ mutable list を全面 ref-first (`rc<list<T>>`) 正本へ切り替え、value list を optimizer 結果だけへ閉じ込める。
2. [x] [ID: P0-CPP-LIST-REFFIRST-01-S1-01] 現行 emitter/runtime に残る value-first 分岐を棚卸しし、「禁止」「ABI adapter 限定」「optimizer 限定」に分類する。
3. [x] [ID: P0-CPP-LIST-REFFIRST-01-S1-02] `spec-cpp-list-reference-semantics.md` を今回の最終方針（dual model ではなく ref-first 正本）に更新する。
4. [x] [ID: P0-CPP-LIST-REFFIRST-01-S1-03] representative codegen test を追加し、「typed list だから value へ寄せる」退行を fail-fast 化する。
5. [x] [ID: P0-CPP-LIST-REFFIRST-01-S2-01] runtime helper の list 主経路を `rc<list<T>>` 基準へ整理し、mutable operation の正本 overload を固定する。
6. [x] [ID: P0-CPP-LIST-REFFIRST-01-S2-02] `iter_ops` / `contains` / `sequence` / `py_to_*` / `make_object` の list 経路を `rc<list<T>>` 正本へ揃える。
7. [x] [ID: P0-CPP-LIST-REFFIRST-01-S2-03] `list<T>` runtime overload のうち ABI adapter 以外のものを縮退・撤去し、残す理由を決定ログへ固定する。
8. [x] [ID: P0-CPP-LIST-REFFIRST-01-S3-01] emitter の list 型描画を ref-first に切り替え、`_is_pyobj_forced_typed_list_type` 依存を撤去する。
9. [ ] [ID: P0-CPP-LIST-REFFIRST-01-S3-02] list literal / empty init / assign / annassign / tuple unpack / comprehension を `rc<list<T>>` 正本へ切り替える。
10. [ ] [ID: P0-CPP-LIST-REFFIRST-01-S3-03] callsite / return / method dispatch / subscript / for/enumerate/reversed の描画を `rc<list<T>>` 正本へ切り替える。
11. [ ] [ID: P0-CPP-LIST-REFFIRST-01-S4-01] `@extern` / `Any` / `object` 境界でだけ `list<T>` value adapter を挿入する規則を実装し、他経路から分離する。
12. [ ] [ID: P0-CPP-LIST-REFFIRST-01-S4-02] ABI adapter 用 helper を整理し、`list<T>` を backend 内部正本として扱う経路をなくす。
13. [ ] [ID: P0-CPP-LIST-REFFIRST-01-S5-01] optimizer 側で「証明できた list だけ value 化する」責務境界を実装し、correctness と optimization を分離する。
14. [ ] [ID: P0-CPP-LIST-REFFIRST-01-S5-02] optimizer off / fail-closed 条件でも unit/parity が通ることを確認する。
15. [ ] [ID: P0-CPP-LIST-REFFIRST-01-S6-01] C++ unit 全体を再実行し、list ref-first 化後の非退行を確認する。
16. [ ] [ID: P0-CPP-LIST-REFFIRST-01-S6-02] fixture/sample parity を再実行し、artifact を含めて非退行を確認する。
17. [ ] [ID: P0-CPP-LIST-REFFIRST-01-S6-03] TODO/archive/docs を更新し、この ref-first 契約を完了扱いで固定する。
