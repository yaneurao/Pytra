# P1: C++ `py_to` テンプレ統合計画

最終更新: 2026-02-25

関連 TODO:
- `docs-ja/todo/index.md` の `ID: P1-CPP-PYTO-01`

背景:
- 現在は `py_to_int64()`/`py_to_float64()`/`py_to_bool()` が別 API で散在し、`object`/`std::any`/基本型の変換ルートが重複しやすい。
- `Any/object` 経路の変換品質を上げつつ、呼び出し側の整合性を取りやすくするには型パラメータ化 API を段階導入したい。

目的:
- C++ 変換ヘルパを `py_to<T>()` へ統一する方向を固め、既存の `py_to_int64` などは互換ラッパとして保ったまま置換を進める。

対象:
- 主要実装: `src/runtime/cpp/pytra-core/built_in/py_runtime.h` の `py_to_int64/py_to_float64/py_to_bool` 系（既存実装と `src/runtime/cpp/pytra/built_in/py_runtime.h` の自動生成/利用形との互換を保つ）。
- `src/hooks/cpp/emitter/cpp_emitter.py` と関連 emitter 側の呼び出し。
- `src/hooks/cpp/emitter/expr.py` の型キャスト経路。

非対象:
- `py_to_string` 全体の文字列化方針の刷新（別タスクで検討）。
- 他言語の runtime 変換 API そのものの全面入れ替え。

受け入れ基準:
- 同等・同一の実行時意味を維持したまま、変換呼び出しの主要経路で `py_to<T>` が利用される。
- 既存の `py_to_int64` / `py_to_float64` / `py_to_bool` 互換ラッパが残り、既存コードへの破壊的変更を回避できる。
- selfhost / C++ 変換回帰テストが通過する。

確認コマンド:
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/check_todo_priority.py`（更新時）
- `python3 test/unit/test_unit_runtime.py`（または該当する runtime テスト群）

進め方:
1) `py_to<T>` の骨子設計（`enable_if` / SFINAE / `object` `std::any` 専用オーバーロード）を runtime ヘッダで定義。
2) emitter 側の呼び出しを段階置換し、既存 `py_to_*` 呼び出しはラッパとして残す。
3) `src/runtime/cpp/pytra-core` と `src/runtime/cpp/pytra` の実体差を避けるため、移行時の include 依存と生成差分も併せて確認し、docs-ja/plans に決定ログを記録。

関連文書:
- `docs-ja/spec/spec-type_id.md`
- `docs-ja/plans/p2-any-object-boundary.md`

補足:
- 仕様上は `pytra-core` 側 API を起点に設計し、`pytra/built_in` 側は現行の参照経路を壊さない範囲で追従する前提で進める。

`P1-CPP-PYTO-01-S1` 確定内容（2026-02-25）:
- `src/runtime/cpp/pytra-core/built_in/py_runtime.h` に `py_to<T>` テンプレート（`object`/`std::any`/値型）を追加し、`int64`/`float64`/`bool`/`str`/`object` の主要変換先を一元化した。
- 既存 API（`py_to_int64`/`py_to_float64`/`py_to_bool`）は互換ラッパとして残し、算術型・`object` 経路の呼び出しは `py_to<T>` を通す形へ寄せた。
- 検証:
  - `python3 tools/check_py2cpp_transpile.py`（`checked=131 ok=131 fail=0 skipped=6`）
  - `python3 tools/runtime_parity_check.py --case-root sample --targets cpp 01_mandelbrot --ignore-unstable-stdout`（`SUMMARY cases=1 pass=1 fail=0 targets=cpp`）

`P1-CPP-PYTO-01-S2` 確定内容（2026-02-25）:
- `src/hooks/cpp/emitter/expr.py` の cast lower を `py_to<float64>` / `py_to<int64>` / `py_to<bool>` 形式へ移行した。
- `src/hooks/cpp/emitter/cpp_emitter.py` の `py_to_int64/py_to_float64/py_to_bool` 直呼び（dict default 取得、添字、truthy 判定、range/enumerate 引数など）を `py_to<...>` 形式へ段階置換した。
- 検証:
  - `python3 test/unit/test_py2cpp_smoke.py`（3件 pass）
  - `python3 tools/check_py2cpp_transpile.py`（`checked=131 ok=131 fail=0 skipped=6`）
  - `python3 tools/runtime_parity_check.py --case-root sample --targets cpp 01_mandelbrot --ignore-unstable-stdout`（`SUMMARY cases=1 pass=1 fail=0 targets=cpp`）

決定ログ:
- [2026-02-25] [ID: P1-CPP-PYTO-01]
  - 追加: `py_to<T>` 方向への段階統合タスクを TODO 化し、互換ラッパ維持前提で進める方針を決定。
- 2026-02-25: `P1-CPP-PYTO-01-S1` として `py_runtime.h` に `py_to<T>` テンプレートを導入し、`py_to_int64`/`py_to_float64`/`py_to_bool` の主要経路を後方互換ラッパ化した。
- 2026-02-25: `P1-CPP-PYTO-01-S2` として `cpp_emitter.py` / `expr.py` の `py_to_*` 直呼びを `py_to<...>` へ段階移行し、C++ transpile/smoke/parity（1ケース）で挙動差分がないことを確認した。
