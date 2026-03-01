# P0: Swift 継承メソッド動的ディスパッチ改善

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-SWIFT`

背景:
- Swift emitter は `final class` 既定と `super` no-op が継承動作の阻害要因になっている。

目的:
- 継承可能な class 宣言と `override`/`super` 経路を導入する。

対象:
- `src/hooks/swift/emitter/swift_native_emitter.py`

非対象:
- Swift backend の型最適化全般

受け入れ基準:
- 継承対象 class から `final` を外し、必要箇所に `override` を付与する。
- `super.init` / `super.method` lower が有効化される。
- fixture parity が一致。

確認コマンド:
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2swift_smoke.py' -v`
- `PYTHONPATH=src python3 tools/runtime_parity_check.py inheritance_virtual_dispatch_multilang --targets swift`

分解:
- [x] class/fn 宣言の継承対応（final/override）を設計する。
- [x] `super` lower を実装する。
- [x] fixture 回帰を追加する。

決定ログ:
- 2026-03-01: Swift は `final` 既定を見直す前提で plan 化した。
- 2026-03-01: `final class` 既定を廃止し、継承時に `override` を自動付与するよう emitter を更新した。
- 2026-03-01: `super().__init__` / `super().method` をそれぞれ `super.init` / `super.method` へ lower する経路を追加した。
- 2026-03-01: `test_py2swift_smoke.py` に継承 dispatch 回帰を追加し、11 tests pass を確認した。
- 2026-03-01: `runtime_parity_check --targets swift` は環境の `toolchain_missing` で実行スキップ（実装は反映済み、実行検証は継続 blocker）。
