<a href="../../../en/plans/archive/20260314-p1-nes3-bus-port-pkg-cpp-support.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1: import した bus 型の header/symbol qualification と受け渡し lane を C++ multi-file contract に揃える

最終更新: 2026-03-14

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-NES3-BUS-PORT-PKG-CPP-01`
- 依存: `ID: P1-NES3-NOT-IMPLEMENTED-ERROR-CPP-01`（shared `NotImplementedError` residual）

背景:
- Pytra-NES3 repro [`materials/refs/from-Pytra-NES3/bus_port_pkg/`](../../../materials/refs/from-Pytra-NES3/bus_port_pkg) は別モジュールから import した bus interface/type を header と実装の両方で使う。
- 2026-03-13 時点の generated `cpu.h` は `pytra_mod_bus_port::BusPort` を使うのに必要な宣言を持たず、`bus.cpp` では `rc<RAMBus>` を `BusPort&` に渡して compile failure になる。
- fixture には shared `NotImplementedError` residual も含まれるが、この task の本丸は cross-module user type の header visibility と param passing contract である。

目的:
- imported bus type が C++ multi-file lane で header / implementation の両方から正しく見えるようにする。
- base/derived bus passing lane を representative ownership contract に揃え、`bus_port_pkg` の compile blocker を外す。

対象:
- imported user type の header include / forward declaration / symbol qualification
- base/derived bus 型の parameter passing / call site lowering
- `materials/refs/from-Pytra-NES3/bus_port_pkg/` の multi-file compile smoke
- bus-port residual の regression / docs / TODO 同期

非対象:
- 例外 lowering 自体の実装詳細
- ownership model 全体の redesign
- non-C++ backend への横展開

受け入れ基準:
- `bus_port_pkg` の generated C++ が compile できる。
- `cpu.h` など imported bus type を使う header が必要な宣言または include を use site より前に持つ。
- `RAMBus` から `BusPort` への受け渡し lane が representative C++ ownership contract に合う。

確認コマンド（予定）:
- `python3 tools/check/check_todo_priority.py`
- `bash ./pytra materials/refs/from-Pytra-NES3/bus_port_pkg/bus.py --target cpp --output-dir /tmp/pytra_nes3_bus_port_pkg`
- `for f in /tmp/pytra_nes3_bus_port_pkg/src/*.cpp; do g++ -std=c++20 -O0 -c "$f" -I /tmp/pytra_nes3_bus_port_pkg/include -I /workspace/Pytra/src -I /workspace/Pytra/src/runtime/cpp; done`
- `git diff --check`

## 分解

- [x] [ID: P1-NES3-BUS-PORT-PKG-CPP-01-S1-01] current compile failure と cross-module bus type residual を focused regression / plan / TODO に固定した。
- [x] [ID: P1-NES3-BUS-PORT-PKG-CPP-01-S2-01] imported bus type の header visibility / symbol qualification を C++ multi-file contract に合わせて修正した。
- [x] [ID: P1-NES3-BUS-PORT-PKG-CPP-01-S2-02] base/derived bus passing lane を representative ownership contract に合わせて修正した。
- [x] [ID: P1-NES3-BUS-PORT-PKG-CPP-01-S3-01] compile smoke と docs wording を shared residual dependency 付きの current contract に同期した。

決定ログ:
- 2026-03-13: Pytra-NES3 bundle の中でも shared exception residual と cross-module bus type residual を分離して追えるよう、`NotImplementedError` task 依存付きの個別 P1 にした。
- 2026-03-14: header builder が class block を持つ header で `py_runtime.h` を引くようにし、`PYTRA_DECLARE_CLASS_TYPE` / `PYTRA_TID_OBJECT` を使う imported interface header も self-contained compile を通るようにした。
- 2026-03-14: imported user class の doc 解決、base qualification、ref-class parameter を `const rc<Base>&` へ正規化する判定、handle pass の call-site lowering、virtual/non-const propagation を揃え、`cpu.h` / `bus.h` / `bus_port.h` の header compile と `bus_port.cpp` / `cpu.cpp` / `bus.cpp` の compile を focused regression で固定した。
