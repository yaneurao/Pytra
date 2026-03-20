# P0: out/cpp/ 自己完結ビルドディレクトリ

最終更新: 2026-03-19

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-SELF-CONTAINED-CPP-OUTPUT-01`

## 背景

現在の C++ ビルドは `-Isrc -Isrc/runtime/cpp` でソースツリーを直接参照している。これにより:

1. ビルド生成物（ユーザーコードの `.cpp`）と手書き runtime ヘッダー（`py_runtime.h` 等）が別ディレクトリに散在し、Makefile が複雑。
2. runtime モジュールの generated ヘッダー（`string_ops.h` 等）の配置先が曖昧（`src/` に事前生成すべきか `out/` に動的生成すべきかが混乱）。
3. ビルドに必要なファイルが `src/` の深いパスに依存し、配布・CI で `src/` 全体が必要。

## 設計

### 出力ディレクトリ構造

namespace に従ったフォルダ階層。native コピーと generated が同じフォルダに混在する。

```
out/
  east/                              # compile 段の出力
    user_module.east
    ...

  cpp/                               # link → emit 段の出力（g++ ビルド一式）
    core/
      py_runtime.h                    # native コピー（src/runtime/cpp/core/）
      py_types.h
      py_scalar_types.h
      exceptions.h
      io.h
      process_runtime.h
      scope_exit.h

    built_in/
      base_ops.h                      # native コピー（src/runtime/cpp/built_in/）
      contains.h                      # native コピー
      io_ops.h                        # native コピー
      iter_ops.h                      # native コピー
      list_ops.h                      # native コピー
      scalar_ops.h                    # native コピー
      sequence.h                      # native コピー
      string_ops.h                    # .east から生成
      numeric_ops.h                   # .east から生成
      type_id.h                       # .east から生成
      format_value.h                  # .east から生成
      predicates.h                    # .east から生成
      zip_ops.h                       # .east から生成

    std/
      pathlib.h                       # .east から生成
      time.h                          # .east から生成
      time.cpp                        # native コピー（src/runtime/cpp/std/）
      math.h                          # .east から生成
      math.cpp                        # native コピー
      json.h                          # .east から生成
      sys.h                           # .east から生成
      sys.cpp                         # native コピー
      ...

    utils/
      png.h                           # .east から生成（将来）
      ...

    main.cpp                          # ユーザーコード
    Makefile                          # g++ -I out/cpp でビルド完結
```

### ビルドコマンド

```bash
cd out/cpp
make            # Makefile が -I . で全てを解決
```

または直接:

```bash
g++ -std=c++20 -O2 -I out/cpp out/cpp/main.cpp out/cpp/std/*.cpp -o app.out
```

### include パス解決

`-I out/cpp` の 1 つだけで全て解決。

| py_runtime.h 内の include | 解決先 |
|--------------------------|--------|
| `#include "py_types.h"` | → **変更**: `#include "core/py_types.h"` → `out/cpp/core/py_types.h` |
| `#include "runtime/cpp/generated/built_in/string_ops.h"` | → **変更**: `#include "built_in/string_ops.h"` → `out/cpp/built_in/string_ops.h` |
| `#include "runtime/cpp/built_in/base_ops.h"` | → **変更**: `#include "built_in/base_ops.h"` → `out/cpp/built_in/base_ops.h` |

**py_runtime.h の include パス変更が必要**:
- `"py_types.h"` → `"core/py_types.h"`（同一ディレクトリ参照を namespace パスに）
- `"runtime/cpp/generated/built_in/X.h"` → `"built_in/X.h"`（native も generated も同じフォルダ）
- `"runtime/cpp/built_in/X.h"` → `"built_in/X.h"`

native と generated が同じ namespace フォルダに入るので、include パスは `"built_in/string_ops.h"` で統一。出自（native / generated）を気にしない。

### エミッターの include 出力変更

エミッターが emit する `#include` パスも `out/cpp/` 基準に変更:

| 現在 | 変更後 |
|------|--------|
| `#include "runtime/cpp/core/py_runtime.h"` | `#include "core/py_runtime.h"` |
| `#include "generated/std/pathlib.h"` | `#include "std/pathlib.h"` |
| `#include "built_in/contains.h"` | `#include "built_in/contains.h"`（変更なし） |

### パイプライン

```
pytra compile foo.py -o out/east/foo.east

pytra link out/east/foo.east --target cpp -o out/cpp/
  → runtime .east を C++ に emit → out/cpp/generated/ に配置
  → ユーザーモジュールを C++ に emit → out/cpp/ に配置
  → native runtime を src/runtime/cpp/ から out/cpp/runtime/ にコピー
  → Makefile を out/cpp/ に生成
```

### pytra-cli.py の `--build` フロー

```
pytra-cli.py foo.py --target cpp --build --output-dir out
  1. compile: foo.py → out/east/foo.east
  2. link: out/east/foo.east → out/cpp/ (ユーザー C++ + runtime 一式)
  3. make: cd out/cpp && make
  4. (--run): ./app.out
```

## 対象ファイル

| ファイル | 変更内容 |
|---------|---------|
| `src/runtime/cpp/core/py_runtime.h` | include パスを `out/cpp/` 基準の相対パスに変更 |
| `src/runtime/cpp/built_in/*.h` | include パスを相対パスに変更 |
| `src/toolchain/emit/cpp/emitter/module.py` | emit する `#include` パスを `out/cpp/` 基準に変更 |
| `src/toolchain/emit/cpp/emitter/runtime_paths.py` | `module_name_to_cpp_include` の出力パスを変更 |
| `src/toolchain/emit/cpp/program_writer.py` | `write_cpp_rendered_program` で runtime コピー + generated emit を追加 |
| `tools/gen_makefile_from_manifest.py` | Makefile の `-I` パスを `out/cpp/` 基準に変更 |
| `src/pytra-cli.py` | `--build` フローを新パイプラインに対応 |

## 非対象

- 非 C++ バックエンドの出力構造（本タスクは C++ のみ）
- selfhost ビルドパイプラインの変更（P7 のスコープ）

## 受け入れ基準

- [ ] `out/east/` に `.east` ファイルが生成される。
- [ ] `out/cpp/` に native runtime コピー + generated ヘッダー + ユーザー C++ + Makefile が生成される。
- [ ] `out/cpp/` 内で `make` だけでビルドが完結する（`src/` への参照なし）。
- [ ] `from pytra.std.pathlib import Path` を含むコードが `out/cpp/` 内でビルドできる。
- [ ] `check_py2x_transpile --target cpp` pass。

## 子タスク

- [ ] [ID: P0-SELF-CONTAINED-CPP-OUTPUT-01-S1] `py_runtime.h` と native ヘッダーの include パスを namespace 基準の相対パスに変更する（`"py_types.h"` → `"core/py_types.h"`、`"runtime/cpp/built_in/X.h"` → `"built_in/X.h"` 等）。
- [ ] [ID: P0-SELF-CONTAINED-CPP-OUTPUT-01-S2] `write_cpp_rendered_program` を拡張し、native runtime を `out/cpp/{namespace}/` にコピーし、runtime `.east` を C++ に emit して同じ namespace フォルダに配置する。
- [ ] [ID: P0-SELF-CONTAINED-CPP-OUTPUT-01-S3] エミッターの `#include` 出力パスを `out/cpp/` 基準に変更する。
- [ ] [ID: P0-SELF-CONTAINED-CPP-OUTPUT-01-S4] Makefile 生成を `out/cpp/` 自己完結に対応させる。
- [ ] [ID: P0-SELF-CONTAINED-CPP-OUTPUT-01-S5] `pytra-cli.py --build` フローを新パイプラインに対応させる。
- [ ] [ID: P0-SELF-CONTAINED-CPP-OUTPUT-01-S6] 最小 repro（pathlib import）が `out/cpp/` 内で `make` でビルドできることを検証する。

## 決定ログ

- 2026-03-19: ユーザーから「ソースツリーにビルド生成物を置くのがおかしい。out/ に動的生成すべき」「py_runtime.h も out/ にコピーすればいい」「out/east, out/cpp のようにフォルダを分けるとすっきりする」「out/cpp に g++ ビルド一式が集まれば Makefile が書きやすい」と提案。自己完結ビルドディレクトリの設計で P0 起票。
- 2026-03-19: S1（include パス namespace 化）、S2（native コピー + .east → C++ 動的生成）、S3（エミッター出力パス変更）完了。g++ ビルドテストで `py_runtime.h` ↔ `type_id.h` の循環依存が発覚。`type_id.h` が `py_runtime_value_isinstance`（`py_runtime.h` 内で `type_id.h` の後に定義）を使う構造。S7 として循環解消タスクを追加。
