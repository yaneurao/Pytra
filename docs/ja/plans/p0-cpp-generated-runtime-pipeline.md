<a href="../../en/plans/p0-cpp-generated-runtime-pipeline.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: C++ generated runtime ヘッダー生成パイプライン整備

最終更新: 2026-03-19

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-GENERATED-RUNTIME-PIPELINE-01`

## 背景

`src/runtime/cpp/` 配下の native ヘッダー・ソースが `#include "runtime/cpp/generated/built_in/*.h"` や `#include "runtime/cpp/generated/std/*.h"` を参照しているが、`src/runtime/cpp/generated/` ディレクトリ自体が存在せず、これらのヘッダーを生成するパイプラインも整備されていない。

### 影響範囲

以下の 15 箇所が存在しないヘッダーを include している:

**built_in（6 ファイル）:**
- `py_runtime.h` → `runtime/cpp/generated/built_in/string_ops.h`
- `py_runtime.h` → `runtime/cpp/generated/built_in/type_id.h`
- `built_in/contains.h` → `runtime/cpp/generated/built_in/contains.h`
- `built_in/io_ops.h` → `runtime/cpp/generated/built_in/io_ops.h`
- `built_in/iter_ops.h` → `runtime/cpp/generated/built_in/iter_ops.h`
- `built_in/scalar_ops.h` → `runtime/cpp/generated/built_in/scalar_ops.h`

**std（6 ファイル）:**
- `std/glob.cpp` → `runtime/cpp/generated/std/glob.h`
- `std/math.cpp` → `runtime/cpp/generated/std/math.h`
- `std/os.cpp` → `runtime/cpp/generated/std/os.h`
- `std/os_path.cpp` → `runtime/cpp/generated/std/os_path.h`
- `std/sys.cpp` → `runtime/cpp/generated/std/sys.h`
- `std/time.cpp` → `runtime/cpp/generated/std/time.h`

**compiler（3 ファイル）:**
- `compiler/backend_registry_static.cpp` → `runtime/cpp/generated/compiler/backend_registry_static.h`
- `compiler/backend_registry_static.cpp` → `runtime/cpp/generated/compiler/transpile_cli.h`
- `compiler/transpile_cli.cpp` → `runtime/cpp/generated/compiler/transpile_cli.h`

### 生成元

`.east` ファイル（EAST3 JSON）は `src/runtime/east/` に存在する:
- `src/runtime/east/built_in/` — string_ops.east, type_id.east, contains.east 等（10 ファイル）
- `src/runtime/east/std/` — time.east, sys.east, json.east 等（13 ファイル）

### マニフェストの状態

`tools/runtime_generation_manifest.json` には C++ ターゲットが `utils/png` と `utils/gif` の 2 件しか登録されていない。`built_in/*` と `std/*` の C++ ヘッダー生成エントリが欠落している。

### 結果

selfhost ビルド（`tools/build_selfhost.py`）が g++ コンパイルで失敗する:
```
fatal error: runtime/cpp/generated/built_in/string_ops.h: No such file or directory
```

## 対象

- `tools/runtime_generation_manifest.json` — `built_in/*` と `std/*` の C++ ターゲット追加
- `tools/gen/gen_runtime_from_manifest.py` — C++ ヘッダー生成の `postprocess` 対応（`.east` → `.h`）
- `src/runtime/cpp/generated/` — 生成先ディレクトリ（`.gitignore` 管理 or git 管理）

## 非対象

- `compiler/` の generated headers（P7-SELFHOST-NATIVE-COMPILER-ELIM-01 の対象）
- 生成後の C++ コンパイル検証（selfhost ビルド全体の検証は P7 の受け入れ基準）

## 受け入れ基準

- [ ] `src/runtime/cpp/generated/built_in/*.h` が `.east` から生成される。
- [ ] `src/runtime/cpp/generated/std/*.h` が `.east` から生成される。
- [ ] selfhost ビルドの g++ コンパイルで `No such file or directory` が発生しない。

## 決定ログ

- 2026-03-19: selfhost ビルド失敗の調査で発見。`runtime/cpp/generated/` ディレクトリが存在せず、マニフェストにも C++ built_in/std ターゲットが未登録であることを確認。P0 で起票。
- 2026-03-19: 実装完了。`gen_runtime_from_manifest.py` に `cpp_program_to_header` postprocess を追加。マニフェストに 12 件の C++ ターゲットを登録。`call.py` の source_path 正規化を修正（絶対パス対応）。全 12 ヘッダー生成成功。check_py2x_transpile 148/148 pass。
