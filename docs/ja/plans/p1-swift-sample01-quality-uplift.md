# P1: sample/swift/01 品質改善（C++品質との差分縮小）

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-SWIFT-SAMPLE01-QUALITY-01`

背景:
- `sample/swift/01_mandelbrot.swift` は `sample/cpp/01_mandelbrot.cpp` と比較して品質差が大きい。
- 主な差分は以下。
  - 画像出力が `__pytra_noop(...)` に退化し、実行機能が欠落。
  - 数値演算で `__pytra_float` / `__pytra_int` の同型ラッパーが多重挿入される。
  - 単純ループが `__step_*` 付き `while` lower へ退化する。
  - `[Any]` 退化が多く、typed container 最適化が効いていない。

目的:
- Swift backend の `sample/01` 出力を native 品質へ引き上げ、C++ 出力との差分を縮小する。

対象:
- `src/hooks/swift/emitter/*`
- `src/runtime/swift/pytra/*`（必要に応じて）
- `test/unit/test_py2swift_*`
- `sample/swift/01_mandelbrot.swift` の再生成

非対象:
- Swift backend 全ケースの一括最適化
- EAST3 仕様の大規模変更
- Go/Kotlin backend 側の同時改修

受け入れ基準:
- `sample/swift/01_mandelbrot.swift` で PNG 出力が no-op ではなく runtime の実関数呼び出しになる。
- 数値ホットパスの同型 `__pytra_float/__pytra_int` 連鎖が有意に減る。
- 単純 `range` ループは canonical loop へ lower される。
- `pixels` 等ホットパスで `[Any]` 退化を最小化し typed container を優先する。
- unit/transpile/parity が通る。

確認コマンド:
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2swift*.py' -v`
- `python3 tools/check_py2swift_transpile.py`
- `python3 tools/regenerate_samples.py --langs swift --force`
- `python3 tools/runtime_parity_check.py --case-root sample --targets swift 01_mandelbrot`

分解:
- [ ] [ID: P1-SWIFT-SAMPLE01-QUALITY-01-S1-01] `sample/swift/01` の品質差分（冗長 cast / loop / no-op / any退化）を棚卸しし、改善優先順を固定する。
- [ ] [ID: P1-SWIFT-SAMPLE01-QUALITY-01-S2-01] Swift emitter の数値演算出力で同型変換連鎖を削減し、typed 経路を優先する。
- [ ] [ID: P1-SWIFT-SAMPLE01-QUALITY-01-S2-02] 単純 `range` ループを canonical loop へ lower する fastpath を追加する。
- [ ] [ID: P1-SWIFT-SAMPLE01-QUALITY-01-S2-03] `write_rgb_png` 経路を no-op から native runtime 呼び出しへ接続し、未解決時は fail-closed にする。
- [ ] [ID: P1-SWIFT-SAMPLE01-QUALITY-01-S2-04] `sample/01` の `pixels` 経路で typed container fastpath を追加し、`[Any]` 退化を抑制する。
- [ ] [ID: P1-SWIFT-SAMPLE01-QUALITY-01-S3-01] 回帰テスト（コード断片 + parity）を追加し、`sample/swift/01` 再生成差分を固定する。

決定ログ:
- 2026-03-01: ユーザー指示により、`sample/swift/01` 品質改善を P1 として計画化し、TODO へ積む方針を確定した。
