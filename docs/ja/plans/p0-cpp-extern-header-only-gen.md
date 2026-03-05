# P0: C++ `@extern` モジュールの header-only gen 移行（`math` 先行）

最終更新: 2026-03-06

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-EXTERN-HDRONLY-01`

背景:
- `pytra.std.math` は `@extern` 契約で C++ 実体を runtime 側へ委譲する方針に切り替えた。
- 現状は `runtime/cpp/gen/std/math.h` に宣言を出せる一方で、`runtime/cpp/gen/std/math.cpp` も生成されるため、`core` 実体との責務境界が曖昧になる。
- 目標は「gen は宣言のみ」「実体は core の事前配置」の分離を固定し、ABI 境界違反の再発を防ぐこと。

目的:
- `@extern` だけで構成される runtime モジュールは `gen` 側で `.h` のみを生成し、`.cpp` を生成しない運用へ移行する。
- 実体は `runtime/cpp/core/std/*.cpp` を正本に固定する。

対象:
- `src/backends/cpp/*`（runtime 生成経路、header/source 出力判定）
- `src/toolchain/compiler/backend_registry.py`（manifest/ビルド入力導線）
- `src/runtime/cpp/core/std/math.cpp`（`math` の実体）
- `src/runtime/cpp/gen/std/math.h`（宣言生成）
- 関連テスト（unit / parity）

非対象:
- `math` 以外の extern モジュールを同時に全件移行すること
- 非C++ backend の extern 契約変更
- runtime API の機能追加

受け入れ基準:
- `pytra.std.math` 変換時に `runtime/cpp/gen/std/math.h` のみ生成され、`runtime/cpp/gen/std/math.cpp` は生成されない。
- `runtime/cpp/core/std/math.cpp` のみで `pytra::std::math::*` 実体がリンクされる。
- C++ build/parity が `math` 利用ケースで非退行（少なくとも fixture + sample の代表ケース）する。
- `gen` と `core` の責務境界（宣言/実体）が docs に記録される。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 src/pytra-cli.py sample/py/01_mandelbrot.py --target cpp --emit-runtime-cpp --output-dir out/p0_cpp_extern_hdronly`
- `test -f src/runtime/cpp/gen/std/math.h`
- `test ! -f src/runtime/cpp/gen/std/math.cpp`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture --ignore-unstable-stdout`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root sample 01_mandelbrot 16_glass_sculpture_chaos --ignore-unstable-stdout`

## 分解

- [ ] [ID: P0-CPP-EXTERN-HDRONLY-01-S1-01] `@extern` 関数/変数の EAST 属性契約を整理し、C++ backend が参照する最小フラグを固定する。
- [ ] [ID: P0-CPP-EXTERN-HDRONLY-01-S1-02] C++ runtime 生成で extern-only module 判定を実装し、`gen/*.cpp` 生成を抑止する。
- [ ] [ID: P0-CPP-EXTERN-HDRONLY-01-S2-01] `math` 実体を `runtime/cpp/core/std/math.cpp` 正本へ移し、`gen/std/math.cpp` 依存を撤去する。
- [ ] [ID: P0-CPP-EXTERN-HDRONLY-01-S2-02] build manifest / backend registry を `math` core 実体参照へ更新する。
- [ ] [ID: P0-CPP-EXTERN-HDRONLY-01-S3-01] `math.h` 生成と `.cpp` 非生成を固定する unit 回帰を追加する。
- [ ] [ID: P0-CPP-EXTERN-HDRONLY-01-S3-02] C++ fixture/sample parity で非退行を確認し、決定ログへ記録する。

決定ログ:
- 2026-03-06: ユーザー指示により、`@extern` モジュールは `gen` 側 `.h` のみを生成し、実体は `core` 事前配置を正本とする方針を採用した（`math` 先行）。
