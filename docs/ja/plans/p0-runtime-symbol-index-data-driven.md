# P0: runtime symbol 対応表のデータ駆動化（SoT 生成 JSON + IR 正規化）

最終更新: 2026-03-06

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-RUNTIME-SYMBOL-INDEX-01`

背景:
- 現状の EAST3 / backend は、runtime 呼び出しの所属モジュールを十分に保持していない。
- 具体的には `py_enumerate` / `py_any` / `py_strip` / `dict.get` のような symbol について、IR 上では裸の `runtime_call` 文字列だけを持ち、後段で backend が「たぶんこれは `pytra.built_in.iter_ops`」「たぶんこれは `pytra.built_in.string_ops`」と推定している箇所が残っている。
- `import pytra.std.time` / `from pytra.utils.png import write_rgb_png` のような import 解決も、`module_id` / `export_name` を meta に保持している一方、最終的な runtime header/source への解決規則が backend 側実装に分散している。
- `signature_registry.py` や IR 構築コードに runtime symbol 対応表が散在しているため、責務が崩れやすい。これは再発しやすい設計であり、transpiler として本来あるべき姿ではない。
- ユーザー方針:
  - どのファイルがどの symbol を持つかの対応関係は、コードへ直書きせず、JSON 等のデータとして扱う。
  - ただし hand-written JSON を増やすのではなく、SoT（`src/pytra/*` と runtime レイアウト）から生成する。
  - IR には target 非依存な情報だけを持たせる。target 別の file path（`*.gen.h`, `*.ext.cpp` 等）を IR に埋め込まない。

目的:
- runtime symbol の所属モジュールと companion 規則を、SoT から生成する index JSON に一本化する。
- EAST3 には `runtime_module_id + runtime_symbol (+ companion など最小属性)` を保持させ、backend はその index を読んで target 別 include/source を導出するだけに縮退させる。
- `signature_registry.py` / `core.py` / 各 backend emitter に散った runtime symbol 直書きの再発を止める。

対象:
- `src/toolchain/ir/core.py`
- `src/toolchain/frontends/signature_registry.py`
- `src/backends/*/`
- `tools/`（index generator / guard / test）
- `src/pytra/{built_in,std,utils}/`
- `src/runtime/<lang>/{core,built_in,std,utils}/`

非対象:
- target 別 codegen 品質の改善
- runtime API の新規追加
- 各 backend の全面書き直し
- `.gen.*` の手修正

## この計画で守るルール

1. `runtime symbol -> module/file` 対応を Python ソースに直書きしない。
2. hand-written JSON を source-of-truth にしない。JSON は必ず生成物にする。
3. EAST3 に埋めるのは target 非依存な情報だけにする。
4. `runtime/cpp/std/math.gen.h` のような target 固有 file path を EAST3 に埋めない。
5. backend は `runtime_module_id` と `runtime_symbol` から target 別 path を導出するだけに縮退させる。
6. `*.gen.*` を直接直してテストを通すことを禁止する。

## 設計ゴール

最終的に、runtime call 系ノードは少なくとも次の情報を持つ:

```json
{
  "lowered_kind": "BuiltinCall",
  "runtime_module_id": "pytra.built_in.iter_ops",
  "runtime_symbol": "py_enumerate",
  "runtime_dispatch": "function",
  "runtime_companion": "gen+ext"
}
```

また import 由来 symbol は少なくとも次を持つ:

```json
{
  "binding_module_id": "pytra.std.time",
  "binding_export_name": "perf_counter",
  "runtime_module_id": "pytra.std.time",
  "runtime_symbol": "perf_counter"
}
```

ここで重要なのは:
- `runtime_module_id` / `runtime_symbol` は target 非依存
- `runtime/cpp/std/time.gen.h` のような path は backend が index を使って導出
- `gen/ext companion の有無` は index 側で持つ

## 生成する index の最小仕様

仮称: `tools/runtime_symbol_index.json`

想定構造:

```json
{
  "schema_version": 1,
  "generated_by": "tools/gen_runtime_symbol_index.py",
  "modules": {
    "pytra.built_in.iter_ops": {
      "source_py": "src/pytra/built_in/iter_ops.py",
      "exports": {
        "py_enumerate_object": {
          "kind": "function",
          "companions": ["gen", "ext"]
        },
        "py_reversed_object": {
          "kind": "function",
          "companions": ["gen", "ext"]
        }
      }
    }
  },
  "targets": {
    "cpp": {
      "pytra.built_in.iter_ops": {
        "header": "src/runtime/cpp/built_in/iter_ops.gen.h",
        "sources": [
          "src/runtime/cpp/built_in/iter_ops.gen.cpp",
          "src/runtime/cpp/built_in/iter_ops.ext.h"
        ]
      }
    }
  }
}
```

補足:
- 実装時に `sources` へ `*.ext.h` を入れるか `public_headers` / `compile_sources` に分けるかは、担当者が confusion しない形へ整理してよい。
- ただし schema は「module 単位」「symbol 単位」「target ごとの artifact 単位」を区別すること。

## 詳細分解

- [ ] [ID: P0-RUNTIME-SYMBOL-INDEX-01] runtime symbol 所属と companion 規則を SoT 生成 JSON へ移し、IR/Backend/Tooling をその index ベースへ切り替える。
- [ ] [ID: P0-RUNTIME-SYMBOL-INDEX-01-S1-01] 現状の runtime symbol 直書き箇所を棚卸しし、「IR に残す情報」「index に移す情報」「backend が導出する情報」を表にして固定する。
- [ ] [ID: P0-RUNTIME-SYMBOL-INDEX-01-S1-02] `runtime symbol index` の schema を定義し、`module / symbol / target artifact / companion` の各責務を文書化する。
- [ ] [ID: P0-RUNTIME-SYMBOL-INDEX-01-S2-01] `src/pytra/{built_in,std,utils}` と `src/runtime/<lang>/{core,built_in,std,utils}` を走査して index JSON を生成する generator を追加する。
- [ ] [ID: P0-RUNTIME-SYMBOL-INDEX-01-S2-02] generator の unit test を追加し、`py_enumerate` / `py_any` / `py_strip` / `perf_counter` / `write_rgb_png` / `Path` の representative cases を index 上で固定する。
- [ ] [ID: P0-RUNTIME-SYMBOL-INDEX-01-S2-03] index generator を CI/ローカルチェックへ組み込み、runtime レイアウト変更時に stale index を fail-fast できるようにする。
- [ ] [ID: P0-RUNTIME-SYMBOL-INDEX-01-S3-01] EAST3 の runtime call ノードへ `runtime_module_id` と `runtime_symbol` を追加し、裸の `runtime_call` 文字列だけに依存しない形へ広げる。
- [ ] [ID: P0-RUNTIME-SYMBOL-INDEX-01-S3-02] import 解決済み symbol（`from X import Y` / `import X` + `X.Y`）についても `runtime_module_id` / `runtime_symbol` を埋める経路を追加する。
- [ ] [ID: P0-RUNTIME-SYMBOL-INDEX-01-S3-03] `signature_registry.py` の runtime symbol 直書きを段階撤去し、最低でも「file path を推定する責務」が残らない状態へ縮退させる。
- [ ] [ID: P0-RUNTIME-SYMBOL-INDEX-01-S4-01] C++ backend を先行対象として、include 収集・namespace 解決・runtime source 収集を index JSON ベースへ切り替える。
- [ ] [ID: P0-RUNTIME-SYMBOL-INDEX-01-S4-02] `build_multi_cpp.py` / `gen_makefile_from_manifest.py` が index を参照して `*.gen.*` と `*.ext.*` companion を一貫導出するよう整理する。
- [ ] [ID: P0-RUNTIME-SYMBOL-INDEX-01-S4-03] C++ emitter から `py_enumerate` / `py_any` / `py_strip` / `dict.get` / `perf_counter` / `Path` の所属推定ロジックを撤去し、IR + index 依存へ寄せる。
- [ ] [ID: P0-RUNTIME-SYMBOL-INDEX-01-S5-01] 非C++ backend への適用方針を整理し、`resolved_runtime_call` と module/file 解決の責務境界を index 前提で揃える。
- [ ] [ID: P0-RUNTIME-SYMBOL-INDEX-01-S5-02] docs/ja/spec に「IR は module+symbol を持つ」「target file path は index + backend が導出する」と明記する。
- [ ] [ID: P0-RUNTIME-SYMBOL-INDEX-01-S5-03] representative regression（C++ include 解決、runtime build graph、import resolution、unit parity）を通し、既存の ad-hoc fallback が不要になったことを確認する。

## 実施手順（担当者向け）

### Step 1: 現状棚卸し

やること:
- `runtime_call` / `resolved_runtime_call` / `runtime_owner` / `module_id` / `export_name` を検索する。
- `signature_registry.py` の dict 群を洗い出す。
- backend 側で module 名や symbol 名から include path を推定している箇所を洗い出す。

最低限見るべきファイル:
- `src/toolchain/ir/core.py`
- `src/toolchain/frontends/signature_registry.py`
- `src/backends/cpp/emitter/module.py`
- `src/backends/cpp/emitter/runtime_paths.py`
- `tools/build_multi_cpp.py`
- `tools/gen_makefile_from_manifest.py`

この段階で残す成果:
- `work/logs/...` などへ棚卸しメモを残す。
- 「これは module 所属情報」「これは target file path」「これは companion 規則」と分類する。

やってはいけないこと:
- いきなり `core.py` の `runtime_call` を全面書換えしない。
- `signature_registry.py` の map を消すだけで代替なしにしない。

### Step 2: index schema 固定

やること:
- JSON schema を最小限に決める。
- 少なくとも以下を持つようにする:
  - module id
  - exported symbols
  - symbol kind
  - target ごとの artifact 情報
  - `gen/ext` companion 情報

判断基準:
- backend が file path を再推定しなくてよいか
- IR が target 固有 path を持たずに済むか

### Step 3: generator 実装

やること:
- 新規 `tools/gen_runtime_symbol_index.py` のような generator を作る。
- 入力は SoT:
  - `src/pytra/built_in/*.py`
  - `src/pytra/std/*.py`
  - `src/pytra/utils/*.py`
  - `src/runtime/<lang>/{core,built_in,std,utils}`
- 出力は JSON。

実装方針:
- module id は Python module 名ベースで統一する。
- runtime/cpp 側では `*.gen.h`, `*.gen.cpp`, `*.ext.h`, `*.ext.cpp` を走査し、対応 module にぶら下げる。
- file existence をもって companion を判定する。

やってはいけないこと:
- module->file 対応を generator 内の巨大 if/elif に直書きしない。
- `py_enumerate -> iter_ops` を dict で固定しない。SoT/module 走査から出す。

### Step 4: IR 拡張

やること:
- `BuiltinCall` などの payload へ `runtime_module_id` と `runtime_symbol` を追加する。
- `runtime_call` は移行期間だけ併存してよいが、最終的には補助情報へ縮退させる。
- import 解決済み symbol にも同じ情報を入れる。

重要:
- ここで埋めるのは `pytra.built_in.iter_ops` と `py_enumerate` まで。
- `runtime/cpp/built_in/iter_ops.gen.h` は埋めない。

### Step 5: C++ backend を index 消費へ移行

やること:
- include 収集を `runtime_module_id` -> index -> include path の 1 経路にする。
- build source 収集も index 参照に寄せる。
- `py_enumerate` などの所属 module 推定を backend から消す。

最低限通すもの:
- include dedupe/sort 系 unit
- `from pytra.std.time import perf_counter`
- `from pytra.utils import png`
- `from pytra.std.pathlib import Path`

### Step 6: guard / docs / regression

やること:
- index stale 検知チェックを CI に入れる。
- docs へ責務境界を書く。
- representative regression を通す。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/gen_runtime_symbol_index.py --check`
- `python3 -m unittest discover -s test/unit/tooling -p 'test_runtime_symbol_index*.py'`
- `python3 -m unittest discover -s test/unit/backends/cpp -p test_*.py`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root sample --all-samples`

決定ログ:
- 2026-03-06: user 指示により、`runtime symbol -> module/file` 対応を Python ソースへ直書きする設計をやめ、SoT 生成 JSON + IR 正規化へ寄せる方針を確定。
- 2026-03-06: 本計画では「IR に埋めるのは target 非依存情報のみ」「target 別 file path は index + backend が導出」とする。
