<a href="../../en/todo/rust.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — Rust backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-03-31

## 運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。
- **parity テストは「emit + compile + run + stdout 一致」を完了条件とする。**
- **[emitter 実装ガイドライン](../spec/spec-emitter-guide.md)を必ず読むこと。** parity check ツール、禁止事項、mapping.json の使い方が書いてある。

## 現状

- toolchain2 の Rust emitter は `src/toolchain2/emit/rs/` に実装済み（fixture 131/131 + sample 18/18 emit 成功）
- runtime は `src/runtime/rs/` に存在（toolchain2 向けに拡張中）
- compile + run parity は一部 fixture で PASS（class_instance, dataclass, class_tuple_assign, nested_types, str_index_char_compare 等）
- 残ブロッカー: 継承 + ref セマンティクスの EAST3 側問題（P0-EAST3-INHERIT）

## 未完了タスク

### P0-EAST3-INHERIT: 継承クラスの ref 一貫性 + super() 解決

文脈: [docs/ja/plans/plan-east3-inheritance-ref-super.md](../plans/plan-east3-inheritance-ref-super.md)

EAST3 lowering の問題。継承階層の基底クラスが `class_storage_hint: "value"` のまま、派生クラスだけ `"ref"` になるため、Rust emitter で `Rc<RefCell<T>>` と `Box<dyn Trait>` が衝突する。また `super()` が `resolved_type: "unknown"` のまま未解決。emitter のワークアラウンドではなく EAST3 側の修正が必要。

1. [x] [ID: P0-EAST3-INHERIT-S1] EAST3 lowering で、派生クラスが存在する基底クラスの `class_storage_hint` を `"ref"` に昇格する（推移的に適用）
   - 完了: `src/toolchain2/resolve/py/resolver.py` に継承階層の基底クラスを推移的に `ref` へ昇格する pass を追加。`tools/unittest/toolchain2/test_inheritance_ref_super_resolution.py` で `Animal <- Dog <- LoudDog` が EAST2/EAST3 の両方で `ref` になることを固定。
2. [x] [ID: P0-EAST3-INHERIT-S2] EAST3 lowering（または EAST2 resolve）で `super()` の型を解決する — receiver type を base class に、method call の戻り値型を base class のメソッド定義から確定
   - 完了: `resolve_east1_to_east2()` で `super()` を現在クラスの base class へ解決し、`super().method()` の receiver / return type が既存の method lookup に乗るよう修正。`tools/unittest/toolchain2/test_inheritance_ref_super_resolution.py` で `super().speak()` が `Dog -> str` に解決されることを確認。
4. [x] [ID: P0-EAST3-INHERIT-S4] Rust の `inheritance_virtual_dispatch_multilang` が compile + run parity PASS することを確認する
   - 完了: EAST3 の `class_storage_hint` 昇格 + `super()` 解決を前提に、`src/toolchain2/emit/rs/emitter.py` の継承 lowering を整理。`Rc<RefCell<T>>` と `Box<dyn ParentMethods>` の境界、trait receiver、enum alias、property/trait dispatch を修正し、`python3 tools/check/runtime_parity_check_fast.py --targets rs --case-root fixture inheritance_virtual_dispatch_multilang` で PASS、さらに `--case-root fixture` 全体でも `131/131 PASS` を確認。

### P7-RS-EMITTER: Rust emitter を toolchain2 に新規実装する

前提: Go emitter（参照実装）と CommonRenderer が安定してから着手。

1. [x] [ID: P7-RS-EMITTER-S1] `src/toolchain2/emit/rs/` に Rust emitter を新規実装する — Go emitter を参考に CommonRenderer + override 構成で作成。Rust 固有のノード（所有権・ライフタイム・borrow、match、impl ブロック等）だけ override として残す
   - 完了: `src/toolchain2/emit/rs/{emitter.py,types.py,__init__.py}` と `src/toolchain2/emit/profiles/rs.json` を作成。全 1001 件 fixture エラーなし emit 成功。pytra-cli2.py に rs target を追加。
2. [x] [ID: P7-RS-EMITTER-S2] `src/runtime/rs/mapping.json` を作成し、runtime_call の写像を定義する
   - 完了: `src/runtime/rs/mapping.json` を作成。Go mapping.json を参考に Rust 向け関数名でマッピング定義。
3. [x] [ID: P7-RS-EMITTER-S3] fixture 132 件 + sample 18 件の Rust emit 成功を確認する
   - 完了: fixture 131/131 + sample 18/18 emit 成功（合計 149 件）。isinstance_user_class / isinstance_tuple_check の module_prefix 属性エラーを修正。
4. [x] [ID: P7-RS-EMITTER-S4] Rust runtime を toolchain2 の emit 出力と整合させる（旧 toolchain1 runtime の引き継ぎ or 再実装）
   - 2026-03-31: `runtime_parity_check_fast.py --targets rs --case-root fixture` で `131/131 PASS` を確認
5. [x] [ID: P7-RS-EMITTER-S5] fixture + sample の Rust compile + run parity を通す
   - 2026-03-31: `runtime_parity_check_fast.py --targets rs --case-root sample` で `18/18 PASS` を確認

### P9-RS-SELFHOST: Rust emitter で toolchain2 を Rust に変換し cargo build を通す

前提: P7-RS-EMITTER 完了後に着手。

1. [ ] [ID: P9-RS-SELFHOST-S0] selfhost 対象コード（`src/toolchain2/` 全 .py）で戻り値型の注釈が欠けている関数に型注釈を追加する — resolve が `inference_failure` にならない状態にする（P4/P6/P20 と共通。先に完了した側の成果を共有）
2. [ ] [ID: P9-RS-SELFHOST-S1] toolchain2 全 .py を Rust に emit し、cargo build が通ることを確認する
3. [ ] [ID: P9-RS-SELFHOST-S2] cargo build 失敗ケースを emitter/runtime の修正で解消する（EAST の workaround 禁止）
4. [ ] [ID: P9-RS-SELFHOST-S3] selfhost 用 Rust golden を配置し、回帰テストとして維持する
5. [ ] [ID: P9-RS-SELFHOST-S4] `run_selfhost_parity.py --selfhost-lang rs --emit-target rs --case-root fixture` で fixture parity PASS
6. [ ] [ID: P9-RS-SELFHOST-S5] `run_selfhost_parity.py --selfhost-lang rs --emit-target rs --case-root sample` で sample parity PASS
