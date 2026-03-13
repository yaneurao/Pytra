# P1: モジュール定数を使う imported class の C++ header 順序と参照 lane を揃える

最終更新: 2026-03-13

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-NES3-APU-CONST-PKG-CPP-01`

背景:
- Pytra-NES3 repro [`materials/refs/from-Pytra-NES3/apu_const_pkg/`](../../../materials/refs/from-Pytra-NES3/apu_const_pkg) は `.apu` モジュール内の class method が module constant を参照し、その class を別モジュールから import して使う。
- 2026-03-13 時点の generated `apu.h` は inline method 本文を先に出し、`LENGTH_TABLE` / `CPU_CLOCK_HZ` / `PULSE_GAIN` などの module constant 宣言が後ろに回るため、header 側で未宣言エラーになる。
- この fixture は imported class と module constant の両方が同じ header contract に乗るときの宣言順序 residual を露出している。

目的:
- module constant を参照する imported class が C++ multi-file header で compile できる宣言順序へ揃える。
- `apu_const_pkg` を representative compile smoke にして、header contract の再発を防ぐ。

対象:
- module constant declaration order と imported class header emission
- `materials/refs/from-Pytra-NES3/apu_const_pkg/` の multi-file compile smoke
- header-order residual の regression / docs / TODO 同期

非対象:
- module global 全般の redesign
- non-C++ backend への横展開
- APU 実装ロジック自体の最適化

受け入れ基準:
- `apu_const_pkg` の generated C++ が compile できる。
- `apu.h` が module constant を参照する前に必要な宣言を持つ。
- imported class + module constant の representative header contract が regression と plan に記録される。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `bash ./pytra materials/refs/from-Pytra-NES3/apu_const_pkg/user.py --target cpp --output-dir /tmp/pytra_nes3_apu_const_pkg`
- `for f in /tmp/pytra_nes3_apu_const_pkg/src/*.cpp; do g++ -std=c++20 -O0 -c "$f" -I /tmp/pytra_nes3_apu_const_pkg/include -I /workspace/Pytra/src -I /workspace/Pytra/src/runtime/cpp; done`
- `git diff --check`

## 分解

- [ ] [ID: P1-NES3-APU-CONST-PKG-CPP-01-S1-01] header 側の current compile failure と declaration-order residual を focused regression / plan / TODO に固定する。
- [ ] [ID: P1-NES3-APU-CONST-PKG-CPP-01-S2-01] imported class が参照する module constant の宣言順序を C++ header contract に合わせて修正する。
- [ ] [ID: P1-NES3-APU-CONST-PKG-CPP-01-S3-01] multi-file compile smoke と docs wording を current contract に同期する。

決定ログ:
- 2026-03-13: Pytra-NES3 repro は imported class と module constant の header 順序 residual を狙い撃ちにしているため、cross-module bundle から独立して起票する。
