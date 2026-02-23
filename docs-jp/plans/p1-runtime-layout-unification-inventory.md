# P0-RUNTIME-SEP-01-S1: C++ runtime 棚卸し結果

最終更新: 2026-02-23

対象:
- `src/runtime/cpp/pytra/` 配下の全ファイル（57件）

分類ルール:
1. ファイル内に `AUTO-GENERATED FILE. DO NOT EDIT.` があるものは `generated`。
2. `generated` ヘッダと同名ペアの `.cpp` は `generated`。
3. `std/*-impl.{h,cpp}` と `built_in/*` は `handwritten`。
4. 公開 include 入口（薄いフォワーダー）は `entry_forwarder` とする（現状 0 件）。

集計:
- `generated`: 38
- `handwritten`: 19
- `entry_forwarder`: 0

一覧:

| path | class | reason |
| --- | --- | --- |
| `src/runtime/cpp/pytra/built_in/bytes_util.cpp` | `handwritten` | runtime core/built_in hand-maintained |
| `src/runtime/cpp/pytra/built_in/bytes_util.h` | `handwritten` | runtime core/built_in hand-maintained |
| `src/runtime/cpp/pytra/built_in/container_common.h` | `handwritten` | runtime core/built_in hand-maintained |
| `src/runtime/cpp/pytra/built_in/dict.h` | `handwritten` | runtime core/built_in hand-maintained |
| `src/runtime/cpp/pytra/built_in/exceptions.h` | `handwritten` | runtime core/built_in hand-maintained |
| `src/runtime/cpp/pytra/built_in/gc.cpp` | `handwritten` | runtime core/built_in hand-maintained |
| `src/runtime/cpp/pytra/built_in/gc.h` | `handwritten` | runtime core/built_in hand-maintained |
| `src/runtime/cpp/pytra/built_in/io.cpp` | `handwritten` | runtime core/built_in hand-maintained |
| `src/runtime/cpp/pytra/built_in/io.h` | `handwritten` | runtime core/built_in hand-maintained |
| `src/runtime/cpp/pytra/built_in/list.h` | `handwritten` | runtime core/built_in hand-maintained |
| `src/runtime/cpp/pytra/built_in/path.h` | `handwritten` | runtime core/built_in hand-maintained |
| `src/runtime/cpp/pytra/built_in/py_runtime.h` | `handwritten` | runtime core/built_in hand-maintained |
| `src/runtime/cpp/pytra/built_in/set.h` | `handwritten` | runtime core/built_in hand-maintained |
| `src/runtime/cpp/pytra/built_in/str.h` | `handwritten` | runtime core/built_in hand-maintained |
| `src/runtime/cpp/pytra/compiler/east_parts/core.cpp` | `generated` | paired with AUTO-GENERATED header |
| `src/runtime/cpp/pytra/compiler/east_parts/core.h` | `generated` | AUTO-GENERATED marker |
| `src/runtime/cpp/pytra/std/dataclasses-impl.h` | `handwritten` | manual impl layer (-impl) |
| `src/runtime/cpp/pytra/std/dataclasses.cpp` | `generated` | paired with AUTO-GENERATED header |
| `src/runtime/cpp/pytra/std/dataclasses.h` | `generated` | AUTO-GENERATED marker |
| `src/runtime/cpp/pytra/std/glob.cpp` | `generated` | paired with AUTO-GENERATED header |
| `src/runtime/cpp/pytra/std/glob.h` | `generated` | AUTO-GENERATED marker |
| `src/runtime/cpp/pytra/std/json.cpp` | `generated` | paired with AUTO-GENERATED header |
| `src/runtime/cpp/pytra/std/json.h` | `generated` | AUTO-GENERATED marker |
| `src/runtime/cpp/pytra/std/math-impl.cpp` | `handwritten` | manual impl layer (-impl) |
| `src/runtime/cpp/pytra/std/math-impl.h` | `handwritten` | manual impl layer (-impl) |
| `src/runtime/cpp/pytra/std/math.cpp` | `generated` | paired with AUTO-GENERATED header |
| `src/runtime/cpp/pytra/std/math.h` | `generated` | AUTO-GENERATED marker |
| `src/runtime/cpp/pytra/std/os.cpp` | `generated` | paired with AUTO-GENERATED header |
| `src/runtime/cpp/pytra/std/os.h` | `generated` | AUTO-GENERATED marker |
| `src/runtime/cpp/pytra/std/pathlib.cpp` | `generated` | paired with AUTO-GENERATED header |
| `src/runtime/cpp/pytra/std/pathlib.h` | `generated` | AUTO-GENERATED marker |
| `src/runtime/cpp/pytra/std/random.cpp` | `generated` | paired with AUTO-GENERATED header |
| `src/runtime/cpp/pytra/std/random.h` | `generated` | AUTO-GENERATED marker |
| `src/runtime/cpp/pytra/std/re.cpp` | `generated` | paired with AUTO-GENERATED header |
| `src/runtime/cpp/pytra/std/re.h` | `generated` | AUTO-GENERATED marker |
| `src/runtime/cpp/pytra/std/sys.cpp` | `generated` | paired with AUTO-GENERATED header |
| `src/runtime/cpp/pytra/std/sys.h` | `generated` | AUTO-GENERATED marker |
| `src/runtime/cpp/pytra/std/time-impl.cpp` | `handwritten` | manual impl layer (-impl) |
| `src/runtime/cpp/pytra/std/time-impl.h` | `handwritten` | manual impl layer (-impl) |
| `src/runtime/cpp/pytra/std/time.cpp` | `generated` | paired with AUTO-GENERATED header |
| `src/runtime/cpp/pytra/std/time.h` | `generated` | AUTO-GENERATED marker |
| `src/runtime/cpp/pytra/std/timeit.cpp` | `generated` | paired with AUTO-GENERATED header |
| `src/runtime/cpp/pytra/std/timeit.h` | `generated` | AUTO-GENERATED marker |
| `src/runtime/cpp/pytra/std/traceback.cpp` | `generated` | paired with AUTO-GENERATED header |
| `src/runtime/cpp/pytra/std/traceback.h` | `generated` | AUTO-GENERATED marker |
| `src/runtime/cpp/pytra/std/typing.cpp` | `generated` | paired with AUTO-GENERATED header |
| `src/runtime/cpp/pytra/std/typing.h` | `generated` | AUTO-GENERATED marker |
| `src/runtime/cpp/pytra/utils/assertions.cpp` | `generated` | paired with AUTO-GENERATED header |
| `src/runtime/cpp/pytra/utils/assertions.h` | `generated` | AUTO-GENERATED marker |
| `src/runtime/cpp/pytra/utils/browser.cpp` | `generated` | paired with AUTO-GENERATED header |
| `src/runtime/cpp/pytra/utils/browser.h` | `generated` | AUTO-GENERATED marker |
| `src/runtime/cpp/pytra/utils/browser/widgets/dialog.cpp` | `generated` | paired with AUTO-GENERATED header |
| `src/runtime/cpp/pytra/utils/browser/widgets/dialog.h` | `generated` | AUTO-GENERATED marker |
| `src/runtime/cpp/pytra/utils/gif.cpp` | `generated` | paired with AUTO-GENERATED header |
| `src/runtime/cpp/pytra/utils/gif.h` | `generated` | AUTO-GENERATED marker |
| `src/runtime/cpp/pytra/utils/png.cpp` | `generated` | paired with AUTO-GENERATED header |
| `src/runtime/cpp/pytra/utils/png.h` | `generated` | AUTO-GENERATED marker |
