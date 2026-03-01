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
- [ ] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S1-01] 追加 fixture を backend smoke/parity 導線へ接続し、回帰検知対象へ昇格する。
- [ ] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-CS] C# backend の継承メソッド dispatch/`super()` 対応を完了する。
- [ ] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-GO] Go backend の継承メソッド dispatch/`super()` 対応を完了する。
- [ ] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-JAVA] Java backend の継承メソッド dispatch/`super()` 対応を完了する。
- [ ] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-JS] JS backend の継承メソッド dispatch/`super()` 対応を完了する。
- [ ] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-TS] TS backend の継承メソッド dispatch/`super()` 対応を完了する。
- [ ] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-KOTLIN] Kotlin backend の継承メソッド dispatch/`super()` 対応を完了する。
- [ ] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-SWIFT] Swift backend の継承メソッド dispatch/`super()` 対応を完了する。
- [ ] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-RS] Rust backend の継承メソッド dispatch/`super()` 対応を完了する。
- [ ] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-RUBY] Ruby backend の継承メソッド dispatch/`super()` 対応を完了する。
- [ ] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-LUA] Lua backend の継承メソッド dispatch/`super()` 対応を完了する。
- [ ] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S3-01] 全 backend の parity/smoke 結果を集約し、未達 blocker を分離する。

決定ログ:
- 2026-03-01: 非C++ backend の継承メソッド動的ディスパッチ改善を P0 で計画化した。
