<a href="../../en/todo/cpp.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — C++ backend

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

## 未完了タスク

### P0-CPP-IN-MEMBERSHIP: in_membership_iterable fixture の C++ parity を通す

`test/fixture/source/py/collections/in_membership_iterable.py` が C++ で FAIL。大きい tuple (20要素)、range(1000)、range with step、str の `in`/`not in` を含むケース。C++ emitter / runtime が iterable の汎用 `contains` として正しく処理できていない可能性。

1. [x] [ID: P0-CPP-IN-MEMBER-S1] 失敗原因を特定する（compile error / runtime error / output mismatch）
2. [x] [ID: P0-CPP-IN-MEMBER-S2] C++ emitter / runtime を修正し、`in_membership_iterable` が compile + run parity PASS することを確認する
   - 完了: 失敗原因は compile error で、`range(...)` を含む `in` / `not in` が `py_contains(rc_from_value(py_range(...)), needle)` に落ちる一方、C++ parity lane には `py_range` 宣言/実装の直接契約がなく `py_range` 未定義で落ちていた。
   - 完了: `emitter.py` の `Compare(In/NotIn)` に `range` call 専用 lowering を追加し、`x in range(start, stop, step)` を `start/stop/step` の算術判定式へ直接展開するよう修正した。`PYTHONPATH=src:tools python3 tools/check/runtime_parity_check_fast.py --targets cpp --case-root fixture --east3-opt-level 2 in_membership_iterable` は PASS。

### P0-CPP-CALLABLE: callable 型（高階関数）の C++ parity を通す

EAST3 の `GenericType(base="callable", args=[引数型, 戻り値型])` を `std::function<R(Args...)>` に変換する処理が C++ emitter にない。`callable_higher_order` fixture が compile + run parity PASS することを完了条件とする。

1. [x] [ID: P0-CPP-CALLABLE-S1] C++ emitter で `callable` 型を `std::function<R(Args...)>` に変換する処理を追加する
2. [x] [ID: P0-CPP-CALLABLE-S2] `callable_higher_order` fixture が C++ で compile + run parity PASS することを確認する
   - 完了: `types.py` / `header_gen.py` / `emitter.py` で `callable[[Args],Ret]` を `std::function<Ret(Args...)>` に落とし、bare `callable` も fallback で扱えるようにした。C++ 予約語衝突（`double`→`double_`）と `std::function` include 伝播も修正した。
   - 完了: `pytra.core.str` 上の string method runtime 参照を依存収集時に `pytra.built_in.string_ops` へ正規化し、`src/pytra/built_in/string_ops.py` に `py_lower` / `py_upper` を追加して runtime EAST を再生成した。`PYTHONPATH=src:tools python3 tools/check/runtime_parity_check_fast.py --targets cpp --case-root fixture --east3-opt-level 2 callable_higher_order` は PASS。

### P0-CLI2-RS-DECOUPLE: pytra-cli2.py から Rust emit 固有 import を分離

文脈: [docs/ja/plans/plan-cli2-rs-decouple.md](../plans/plan-cli2-rs-decouple.md)

`pytra-cli2.py` は C++ emit 経路を切り離した後も Rust emit の top-level import を残しており、C++ selfhost build で不要な Rust emitter / manifest loader を include graph に引き込んでいる。Rust emit も subprocess 委譲へ揃える。

1. [x] [ID: P0-CLI2-RS-DECOUPLE-S1] Rust emit 用 CLI を `toolchain2.emit.rs` 側へ追加し、manifest loader / package emit helper を移す
2. [x] [ID: P0-CLI2-RS-DECOUPLE-S2] `pytra-cli2.py` の Rust emit/build 経路を subprocess 委譲へ変更し、top-level import を削除する
3. [x] [ID: P0-CLI2-RS-DECOUPLE-S3] `pytra-cli2.py --target rs` の representative build と C++ selfhost header で非流入を確認する
   - 完了: `src/toolchain2/emit/rs/cli.py` を追加して Rust emit helper を移し、`pytra-cli2.py` は `python3 -m toolchain2.emit.rs.cli` への subprocess 委譲へ変更した。`PYTHONPATH=src python3 src/pytra-cli2.py -build sample/py/17_monte_carlo_pi.py --target rs --rs-package -o work/tmp/cli2_rs_emit` は成功し、C++ selfhost 用に生成した `work/selfhost/build/cpp/emit/pytra_cli2.h` から `toolchain2/emit/rs/emitter.h` と `shutil.h` の流入が消えていることを確認した

### P20-CPP-SELFHOST: C++ emitter で toolchain2 を C++ に変換し g++ build を通す

文脈: [docs/ja/plans/p4-cpp-selfhost.md](../plans/p4-cpp-selfhost.md)

1. [x] [ID: P20-CPP-SELFHOST-S0] selfhost 対象コード（`src/toolchain2/` 全 .py）で戻り値型の注釈が欠けている関数に型注釈を追加する — resolve が `inference_failure` にならない状態にする（他言語と共通。先に完了した側の成果を共有）
   - 完了: `ast` 走査で `src/toolchain2/` 全 `.py` の `FunctionDef` / `AsyncFunctionDef` を監査し、戻り値注釈欠落が 0 件であることを確認。回帰防止として `tools/unittest/selfhost/test_selfhost_return_annotations.py` を追加した
2. [x] [ID: P20-CPP-SELFHOST-S1] toolchain2 全 .py を C++ に emit し、g++ build が通ることを確認する
   - 完了: code_emitter.py → code_emitter.cpp 生成・リンク成功（runtime cpp + 依存 .cpp と結合）
3. [x] [ID: P20-CPP-SELFHOST-S2] g++ build 失敗ケースを emitter/runtime の修正で解消する（EAST の workaround 禁止）
   - 完了: tuple subscript 検出拡張、py_dict_set_mut 追加、object→str/container 型強制、前方宣言二段階出力、is_simple_ident ガード、py_set_add_mut fallback を py_to_string 経由に変更
4. [x] [ID: P20-CPP-SELFHOST-S3] selfhost 用 C++ golden を配置し、回帰テストとして維持する
   - 完了: `python3 tools/gen/regenerate_selfhost_golden.py --target cpp --timeout 60` で `test/selfhost/cpp/` の golden を再生成し、emit 成功する 42 モジュールを更新した。emit 失敗する 5 モジュール（`toolchain2.compile.passes`, `toolchain2.optimize.passes.{tuple_target_direct_expansion,typed_enumerate_normalization,typed_repeat_materialization}`, `toolchain2.resolve.py.resolver`）は既知 skip として整理し、`tools/unittest/selfhost/test_selfhost_cpp_golden.py` に C++ 専用の golden coverage / re-emit 一致テストを追加した
5. [ ] [ID: P20-CPP-SELFHOST-S4] emit 失敗の 5 モジュールを解消し、toolchain2 全モジュールの C++ emit を成功させる
6. [ ] [ID: P20-CPP-SELFHOST-S5] selfhost C++ バイナリを g++ でビルドし、リンクが通ることを確認する
7. [ ] [ID: P20-CPP-SELFHOST-S6] `run_selfhost_parity.py --selfhost-lang cpp --emit-target cpp --case-root fixture` で fixture parity が PASS することを確認する
8. [ ] [ID: P20-CPP-SELFHOST-S7] `run_selfhost_parity.py --selfhost-lang cpp --emit-target cpp --case-root sample` で sample parity が PASS することを確認する
