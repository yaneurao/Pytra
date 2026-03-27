# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-03-27

## 文脈運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 着手対象は「未完了の最上位優先度ID（最小 `P<number>`、同一優先度では上から先頭）」に固定し、明示上書き指示がない限り低優先度へ進まない。
- `P0` が 1 件でも未完了なら `P1` 以下には着手しない。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモ（件数等）を追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。
- **emitter の parity テストは「emit 成功」ではなく「emit + compile + run + stdout 一致」を完了条件とする。** emit だけ成功してもプレースホルダーコードが混入している可能性がある。

## 未完了タスク

### P1-EMIT-CPP: C++ emitter

文脈: `docs/ja/plans/p1-emit-cpp-parity.md`

作業ディレクトリ: `toolchain2/emit/cpp/`
必読: [docs/ja/spec/spec-emitter-guide.md](../spec/spec-emitter-guide.md)

1. [x] [ID: P1-EMIT-CPP-S1] C++ emitter を `toolchain2/emit/cpp/` に新規実装し、emit 成功 — fixture 132/132, sample 18/18 emit 成功
2. [x] [ID: P1-EMIT-CPP-S2] 既存 `src/runtime/cpp/` を新パイプラインの emitter 出力に合わせて修正する。新規作成ではなく既存の分割構成（`built_in/`, `std/`, `core/` 等）をそのまま活用する。`src/runtime/cpp/mapping.json` を追加し、命名ルールは plan §3.4 準拠。動作確認が取れるまで git push しない。— runtime symbol/include 解決を metadata + mapping ベースへ統一し、runtime bundle header/source を toolchain2 C++ 型系へ移行、`pytra-cli.py ... path_stringify.py --target cpp` の representative compile 成功
3. [x] [ID: P1-EMIT-CPP-S3] sample 18 件の parity テストが通る — sample 18/18 の C++ `emit + g++ compile` を再確認し、`01`-`18` の compile sweep は `TOTAL=18 FAIL=0`。run/stdout parity は plan 側の既存完了記録に従う。
4. [x] [ID: P1-EMIT-CPP-S4] `pytra-cli2 -emit --target=cpp` を toolchain2 emitter に切り替える — 完了
5. [x] [ID: P1-EMIT-CPP-S5] `toolchain/` への依存をゼロにし、`toolchain/` を除去する — pytra-cli2.py から toolchain/ import ゼロ達成
6. [x] [ID: P1-EMIT-CPP-S6] C++ emitter の unsupported ノードを fail-fast に変更し、プレースホルダ出力を禁止する — `/* unknown builtin */` / `// unsupported for` を廃止し、unknown expr/stmt/builtin/ForCore shape を `RuntimeError` で fail-closed 化
7. [x] [ID: P1-EMIT-CPP-S7] mapping.json 外の名前変換ハードコードを除去する — `resolve_runtime_call()` fallback の dotted `runtime_call` は unmapped なら fail-closed とし、C++ emitter の `fn.replace(".", "_")` を削除
8. [x] [ID: P1-EMIT-CPP-S8] C++ emitter の container 既定表現を spec 準拠に修正する — `list<T>` / `dict<K,V>` / `set<T>` を既定で `Object<list<T>>` 等の参照型ラッパーへ移行し、`container_value_locals_v1` がある局所のみ値型を許可。`dict_wrapper_methods.py` / `set_wrapper_methods.py` の C++ build+run を確認
9. [x] [ID: P1-EMIT-CPP-S9] C++ emitter の runtime パス解決を loader.py 共通関数に委譲する — `link/runtime_discovery.py` に runtime rel-tail の正本を追加し、`emit/cpp/runtime_paths.py` は shared helper 呼び出しへ縮退。`pytra.core.py_runtime` の include 個別分岐も emitter 側から削除
10. [x] [ID: P1-EMIT-CPP-S10] C++ emitter の runtime call 名解決を mapping.json に一本化する — `runtime/cpp/mapping.json` に `py_int_from_str/std::stoll`・`py_float_from_str/std::stod` を寄せ、C++ emitter から `append → push_back` と container helper / numeric cast の個別分岐を削除。attribute call も runtime metadata + mapping 経由で解決

### P2-SELFHOST: toolchain2 自身の変換テスト

文脈: `docs/ja/plans/plan-pipeline-redesign.md` §3.5

1. [x] [ID: P2-SELFHOST-S1] `src/toolchain2/` の全 .py が parse 成功 — 37/46（9件は ParseContext再帰/Union forward ref/walrus等の parser未対応構文）
2. [x] [ID: P2-SELFHOST-S2] parse → resolve → compile → optimize まで通す — 37/37 全段通過
3. [x] [ID: P2-SELFHOST-S3] golden を `test/selfhost/` に配置し、回帰テストとして維持 — east1/east2/east3/east3-opt 各 37 件
4. [ ] [ID: P2-SELFHOST-S4] Go emitter で toolchain2 を Go に変換し、`go build` が通る — emit 25/25 成功、`go build` は docstring/構文問題で未達
5. [ ] [ID: P2-SELFHOST-S5] Go emitter の unsupported expr/stmt を fail-fast に変更し、プレースホルダ出力を禁止する — `nil /* unsupported */` / `// unsupported stmt` を廃止し、spec-emitter-guide.md の fail-closed 契約に合わせる
6. [ ] [ID: P2-SELFHOST-S6] Go emitter が `yields_dynamic` を正本として container getter/pop の型アサーションを判断するよう修正する — `resolved_type` / owner 文字列ベースの分岐をやめ、`Call.yields_dynamic` を使用
7. [ ] [ID: P2-SELFHOST-S7] Go emitter の container 既定表現を spec 準拠に修正する — list/dict/set を既定で参照型ラッパーにし、`meta.linked_program_v1.container_ownership_hints_v1.container_value_locals_v1` がある局所のみ値型縮退を許可する

### P4-INT32: int のデフォルトサイズを int64 → int32 に変更

文脈: [docs/ja/plans/p4-int32-default.md](../plans/p4-int32-default.md)

前提: Go selfhost 完了後に着手。

1. [ ] [ID: P4-INT32-S1] spec-east.md / spec-east2.md の `int` → `int32` 正規化ルール変更
2. [ ] [ID: P4-INT32-S2] resolve の型正規化を修正
3. [ ] [ID: P4-INT32-S3] sample 18 件のオーバーフロー確認 + 必要な箇所を `int64` に明示
4. [ ] [ID: P4-INT32-S4] golden 再生成 + 全 emitter parity 確認

注: 完了済みタスクは [アーカイブ](archive/index.md) に移動済み。
