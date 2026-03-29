<a href="../../../en/plans/archive/20260308-p0-runtime-abi-mode-simplify-value-value-mut.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: `@abi` mode を `value` / `value_mut` に整理する

最終更新: 2026-03-08

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-RUNTIME-ABI-MODE-SIMPLIFY-01`

背景:
- 現行の `@abi` は引数 mode として `default`, `value`, `value_readonly` を持つ。
- しかし運用上、mutable container 引数に対して欲しい通常ケースは「read-only value ABI」であり、`py_join` のような helper に毎回 `value_readonly` を書くのは冗長である。
- 実際、`py_join` の `parts` が read-only であることは call graph 解析を待たず関数本体の局所検査だけで分かる。
- 一方で、将来 writable な value ABI が必要な helper は残り得るため、単純に `readonly` 概念を消すのではなく、rare case を別 mode へ追い出す方が surface として自然である。

目的:
- `@abi` の public mode 名を `default`, `value`, `value_mut` に整理する。
- 引数側の `value` は「read-only value ABI」を意味する canonical mode にする。
- writable value ABI が必要なケースだけ `value_mut` を明示させる。
- parser / metadata / validator / docs / tests / representative runtime helper を新 naming に揃える。

対象:
- `docs/ja/spec/spec-abi.md`
- `docs/ja/spec/spec-east.md`
- `src/toolchain/ir/core.py`
- `src/toolchain/frontends/runtime_abi.py`
- `src/pytra/std/abi.py` 相当の surface と decorator metadata
- `src/pytra/built_in/string_ops.py` など既存 `@abi` 利用箇所
- `tools/unittest/ir`, `tools/unittest/tooling`, `tools/unittest/common`, `tools/unittest/emit/cpp` の関連回帰

非対象:
- `@abi` 自体を不要にする設計変更
- runtime helper を linked-program に統合して `@abi` 依存を縮める長期計画
- `value_mut` を必要とする新 helper の追加
- C++ runtime helper の意味論変更

受け入れ基準:
- public docs の canonical mode 名が `default`, `value`, `value_mut` に統一される。
- 引数側 `value` は read-only value ABI として定義される。
- `value_mut` は writable value ABI として定義される。
- `value_readonly` は少なくとも canonical surface から外れる。
- 既存 `@abi(args={"parts": "value_readonly"}, ret="value")` などは `value` へ移行される。
- validator / parser / diagnostics / metadata test が新 naming を基準に通る。
- representative C++ runtime helper / codegen 回帰が壊れない。

基本方針:
1. まず仕様上の意味を固定し、`value` を引数側 read-only value ABI へ再定義する。
2. parser / metadata は新 mode 名を source of truth とする。
3. `value_readonly` を完全廃止するか、移行期 alias として一時受理して canonical metadata では `value` へ正規化するかを明示する。
4. writable case は `value_mut` だけで表し、rare case を明示化する。

確認コマンド（予定）:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/ir -p 'test_east_core.py' -k abi`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/link -p 'test_global_optimizer.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/common -p 'test_pytra_built_in_string_ops.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_py2cpp_codegen_issues.py' -k abi`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_ir2lang_cli.py'`

## 分解

- [x] [ID: P0-RUNTIME-ABI-MODE-SIMPLIFY-01-S1-01] 現行 `default/value/value_readonly` 契約を棚卸しし、`value=value_readonly`, `value_mut=旧 mutable value ABI` の移行方針を固定する。
- [x] [ID: P0-RUNTIME-ABI-MODE-SIMPLIFY-01-S1-02] spec/plan に canonical naming と移行ルールを書き、`value_readonly` の扱いを決める。
- [x] [ID: P0-RUNTIME-ABI-MODE-SIMPLIFY-01-S2-01] parser / decorator metadata / validator が `value` / `value_mut` を受理し、新 canonical metadata を出すよう更新する。
- [x] [ID: P0-RUNTIME-ABI-MODE-SIMPLIFY-01-S2-02] diagnostics / error message / target support check を新 naming に合わせる。
- [x] [ID: P0-RUNTIME-ABI-MODE-SIMPLIFY-01-S3-01] 既存 helper（`py_join`, `py_split`, `py_range` など）の注釈と generated/runtime 側期待を新 naming に移行する。
- [x] [ID: P0-RUNTIME-ABI-MODE-SIMPLIFY-01-S3-02] representative regression を更新し、C++ helper/codegen で非退行を確認する。
- [x] [ID: P0-RUNTIME-ABI-MODE-SIMPLIFY-01-S4-01] docs と how-to-use を新 naming に同期し、移行注意点を記録する。
- [x] [ID: P0-RUNTIME-ABI-MODE-SIMPLIFY-01-S4-02] 完了結果を記録し、計画を archive へ移して閉じる。

## フェーズ詳細

### Phase 1: 契約固定

やること:
- `value` / `value_readonly` / `value_mut` の意味を整理する。
- 引数側 `value` を read-only value ABI に寄せることを正式決定する。
- `value_readonly` を非推奨 alias にするか即廃止するか決める。

成果物:
- naming 決定
- 移行ルール

### Phase 2: surface / metadata 更新

やること:
- parser と decorator 解析を更新する。
- canonical `runtime_abi_v1` metadata を新 naming にする。
- diagnostics も新 naming に揃える。

成果物:
- 新 mode 名を受理する frontend
- 整理された error message

### Phase 3: helper / regression 移行

やること:
- 既存 `@abi` 利用箇所を新 naming に移行する。
- C++ helper / codegen representative test を更新する。

成果物:
- migrated helper annotations
- green regression

### Phase 4: 運用固定

やること:
- docs 更新
- archive

成果物:
- docs
- archive 済み plan

## 棚卸し結果（S1-01）

- surface / parser の受理 mode は現状 `default`, `value`, `value_readonly` の 3 つだけである。
  - self-host parser: [src/toolchain/ir/core.py](../../../src/toolchain/ir/core.py) の `_SH_RUNTIME_ABI_MODES`
  - validator: [src/toolchain/frontends/runtime_abi.py](../../../src/toolchain/frontends/runtime_abi.py) の `_RUNTIME_ABI_MODES`
- read-only 検査は現状 `value_readonly` にだけ結び付いており、`collect_mutated_params(...)` を使った局所 mutation 検出で fail-closed している。
- checked-in runtime helper の `@abi` use-site は現状 4 箇所だけである。
  - 引数付き override は [string_ops.py](../../../src/pytra/built_in/string_ops.py) の `py_join(parts)` だけで、`value_readonly` を使っている。
  - 戻り値 `ret="value"` は `py_join`, `py_split`, `py_splitlines`, [sequence.py](../../../src/pytra/built_in/sequence.py) の `py_range` で使っている。
- checked-in source / test / spec を見る限り、「writable な value ABI 引数」を要求する実例はまだ無い。
  - `value_mutating` は [spec-abi.md](../spec/spec-abi.md) に future extension として 1 回出てくるだけで、実装・fixture・runtime helper の use-site は存在しない。
- したがって今回の rename は「既存の実例を新 mode へ移す」というより、
  - 引数側 `value` を旧 `value_readonly` の意味へ寄せる
  - rare case の writable value ABI を `value_mut` として先に予約する
 という contract simplification と見るのが正しい。

## S1-01 時点の移行方針

1. canonical public naming は `default`, `value`, `value_mut` とする。
2. 引数側 `value` は旧 `value_readonly` の意味を引き継ぎ、局所 mutation 検査の対象にする。
3. `ret="value"` は現行のまま維持し、戻り値側の意味変更は行わない。
4. `value_mut` は「旧 spec 上の writable value ABI / `value_mutating` 概念」の短縮名として導入する。
   - ただし checked-in use-site はまだ無いので、初回実装では予約された writable mode として扱う。
5. `value_readonly` は移行期 alias として一時受理してよいが、canonical metadata と docs では `value` に正規化する方針を採る。
   - alias の存廃と diagnostics wording は `S1-02` / `S2-02` で正式化する。

## 決定ログ

- 2026-03-08: ユーザー指示により、`value_readonly` を簡約し、`@abi` mode 名を `value` / `value_mut` へ整理する P0 を起票する。
- 2026-03-08: 本計画では `value` を引数側 read-only value ABI として扱う。rare case の mutable value ABI は `value_mut` へ退避する。
- 2026-03-08: 本計画の主眼は naming と contract の整理であり、`@abi` 自体の必要性や runtime SoT linked-program 統合の是非は別計画で扱う。
- 2026-03-08: `S1-01` 棚卸しの結果、checked-in helper の引数 override は `py_join(parts)` の 1 例だけであり、writable value ABI の現用例は存在しないことを確認した。
- 2026-03-08: `S1-01` の移行方針として、引数側 `value` を旧 `value_readonly` へ寄せ、`value_mut` は future writable case の予約 mode として導入し、`value_readonly` は移行期 alias として扱う方針を固定した。
- 2026-03-08: `S1-02` で `spec-abi` / `spec-east` を更新し、canonical mode を `default/value/value_mut` へ統一した。
- 2026-03-08: `S1-02` で `value_readonly` は canonical metadata から外し、移行期 alias として source parser が受理しても `runtime_abi_v1` では `value` へ正規化する方針を正式化した。
- 2026-03-08: `S2-01` で self-host parser と `validate_runtime_abi_module(...)` を更新し、`value_readonly` を source alias として受理しつつ canonical metadata では `value` へ正規化するようにした。
- 2026-03-08: `S2-01` で `value_mut` を引数 mode として受理し、`ret="value_mut"` は parser/validator で reject する方針を実装へ反映した。
- 2026-03-08: `S2-02` で parser hint・mutation violation diagnostics・representative tests を新 naming に合わせ、public-facing error wording を `value parameter mutated` へ更新した。
- 2026-03-08: `S3-01` で checked-in runtime helper source の `py_join` を `@abi(args={"parts": "value"}, ret="value")` へ移し、canonical surface へ揃えた。
- 2026-03-08: `S3-02` で `test_pytra_built_in_string_ops.py`, `test_py2cpp_codegen_issues.py -k abi`, `test_global_optimizer.py` を通し、helper semantics と representative C++ ABI route の非退行を確認した。
- 2026-03-08: `S4-01` で `docs/ja/how-to-use.md` に canonical `@abi` naming (`args: default/value/value_mut`, `ret: default/value`) と legacy `value_readonly -> value` 正規化の運用メモを追加した。
- 2026-03-08: `S4-02` で本計画を archive へ移し、active TODO は次順位の `P0-PYTRACLI-CPP-MAXOPT-LINKED-01` へ戻す。
