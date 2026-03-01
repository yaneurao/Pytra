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
- [ ] class/fn 宣言の継承対応（final/override）を設計する。
- [ ] `super` lower を実装する。
- [ ] fixture 回帰を追加する。

決定ログ:
- 2026-03-01: Swift は `final` 既定を見直す前提で plan 化した。
