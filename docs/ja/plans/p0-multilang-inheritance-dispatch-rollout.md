# P0: 非C++ 継承メソッド動的ディスパッチ改善

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-MULTILANG-INHERIT-DISPATCH-01`

背景:
- C++ backend は virtual/override と `super()` lower を前提に、基底参照経由のメソッド呼び出しで動的ディスパッチを維持している。
- 非C++ backend では、継承表現はあっても Python 互換の動的ディスパッチが不完全な言語が残る。
- 回帰検知用に `test/fixtures/oop/inheritance_virtual_dispatch_multilang.py` を追加し、期待値を固定した。

目的:
- 非C++ backend（`cs/go/java/js/ts/kotlin/swift/rs/ruby/lua`）で、継承メソッド呼び出しと `super()` の意味を Python 互換へ揃える。

対象:
- fixture: `test/fixtures/oop/inheritance_virtual_dispatch_multilang.py`
- backend: `src/hooks/{cs,go,java,js,ts,kotlin,swift,rs,ruby,lua}/emitter/*`
- 検証: `tools/runtime_parity_check.py` / `test/unit/test_py2*_smoke.py`

非対象:
- C++ backend の再設計
- 多重継承の導入（Pytra は単一継承）

受け入れ基準:
- 追加 fixture が各 backend で transpile 可能。
- 実行可能 backend で parity が `loud-dog / loud-dog` に一致。
- backend ごとの設計差分は言語別 plan に記録され、TODO 子IDで追跡できる。

確認コマンド:
- `PYTHONPATH=src python3 test/fixtures/oop/inheritance_virtual_dispatch_multilang.py`
- `PYTHONPATH=src python3 tools/runtime_parity_check.py inheritance_virtual_dispatch_multilang --targets cpp,rs,cs,js,ts,go,java,swift,kotlin,ruby,lua`
- `python3 tools/check_todo_priority.py`

分解:
- [x] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S1-01] 追加 fixture を backend smoke/parity 導線へ接続し、回帰検知対象へ昇格する。
- [x] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-CS] C# backend の継承メソッド dispatch/`super()` 対応を完了する。
- [x] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-GO] Go backend の継承メソッド dispatch/`super()` 対応を完了する。
- [x] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-JAVA] Java backend の継承メソッド dispatch/`super()` 対応を完了する。
- [x] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-JS] JS backend の継承メソッド dispatch/`super()` 対応を完了する。
- [x] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-TS] TS backend の継承メソッド dispatch/`super()` 対応を完了する。
- [x] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-KOTLIN] Kotlin backend の継承メソッド dispatch/`super()` 対応を完了する。
- [ ] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-SWIFT] Swift backend の継承メソッド dispatch/`super()` 対応を完了する。
- [ ] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-RS] Rust backend の継承メソッド dispatch/`super()` 対応を完了する。
- [x] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-RUBY] Ruby backend の継承メソッド dispatch/`super()` 対応を完了する。
- [ ] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-LUA] Lua backend の継承メソッド dispatch/`super()` 対応を完了する。
- [ ] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S3-01] 全 backend の parity/smoke 結果を集約し、未達 blocker を分離する。

決定ログ:
- 2026-03-01: 非C++ backend の継承メソッド動的ディスパッチ改善を P0 で計画化した。
- 2026-03-01: `tools/runtime_parity_check.py` の fixture 既定ケースに `inheritance_virtual_dispatch_multilang` を追加し、回帰導線へ接続した。
- 2026-03-01: `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_runtime_parity_check_cli.py' -v` は pass（7 tests, 0 fail）。
- 2026-03-01: `python3 tools/runtime_parity_check.py inheritance_virtual_dispatch_multilang --targets cpp,rs,cs,js,ts,go,java,swift,kotlin,ruby,lua --ignore-unstable-stdout --summary-json out/inherit_dispatch_multilang_summary.json` を実行し、S2 実装前のベースラインを固定した（`run_failed=10`, `toolchain_missing=1`）。
- 2026-03-01: C#（`S2-CS`）を実施し、`virtual/override` 付与・`super` lower・assertion 関数マッピングを追加。`--targets cs` の fixture parity は pass（1/1）。
- 2026-03-01: Go（`S2-GO`）を実施し、class interface 導入 + `super` lower を追加。`--targets go` の fixture parity は pass（1/1）。
- 2026-03-01: Java（`S2-JAVA`）を実施し、`super().method(...)` を `super.method(...)` へ lower 修正。`test_py2java_smoke.py`（23 tests）と `runtime_parity_check --targets java`（1/1 pass）を確認した。
- 2026-03-01: JS（`S2-JS`）を実施し、`class ... extends ...` と `super` lower（`super().__init__` / `super().method`）を追加。`test_py2js_smoke.py`（23 tests）と `runtime_parity_check --targets js`（1/1 pass）を確認した。
- 2026-03-01: TS（`S2-TS`）は JS 委譲経路のため、JS 修正追従後に `test_py2ts_smoke.py`（15 tests）と `runtime_parity_check --targets ts`（1/1 pass）を確認して完了扱いとした。
- 2026-03-01: Kotlin（`S2-KOTLIN`）を実施し、`open/override` 解析と `super().method` の `super.method` lower を追加。`test_py2kotlin_smoke.py`（13 tests）と `runtime_parity_check --targets kotlin`（1/1 pass）を確認した。
- 2026-03-01: Ruby（`S2-RUBY`）を実施し、`super().method` を superclass method bind 呼び出しへ lower、`py_assert_*` の副作用評価を抑制。`test_py2rb_smoke.py`（20 tests）と `runtime_parity_check --targets ruby`（1/1 pass）を確認した。
