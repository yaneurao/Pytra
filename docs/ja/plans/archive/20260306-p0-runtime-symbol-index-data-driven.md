<a href="../../../en/plans/archive/20260306-p0-runtime-symbol-index-data-driven.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

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

## S1-01 棚卸し結果（2026-03-06 固定）

### 1. 直書き箇所の分類表

| レイヤ | ファイル | 現在持っている情報 | 問題 | あるべき移管先 |
| - | - | - | - | - |
| IR 構築 | `src/toolchain/ir/core.py` | `enumerate -> py_enumerate`, `any -> py_any`, `all -> py_all`, `reversed -> py_reversed`, `bytes/bytearray/list/set/dict ctor` などの裸 `runtime_call` | symbol 名だけで module 所属がない | `runtime_module_id` + `runtime_symbol` を IR に保持 |
| frontend | `src/toolchain/frontends/signature_registry.py` | `perf_counter`, `Path`, `json.loads`, `write_rgb_png`, `save_gif`, `math.sqrt` などの runtime call 対応、owner method 対応、型推定 | module/file/path 推定責務まで持っている。target 非依存情報と target 依存情報が混在 | module/symbol の正規化だけ最小限残し、file/artifact 対応は index へ移管 |
| backend(C++) | `src/backends/cpp/emitter/module.py` | `pytra.std.*` / `pytra.utils.*` / `pytra.built_in.*` から include path / namespace を推定 | module tail と file path を backend 実装が再推定している | index を読んで include/header を導出 |
| backend(C++) | `src/backends/cpp/emitter/runtime_paths.py` | `module_tail -> *.gen.h`、`module_name -> runtime/cpp/...` 変換 | C++ path 規則の中心実装としては妥当だが、symbol 所属決定まで抱えると責務過多 | 「module -> target artifact」の導出専用に縮退 |
| backend(C++) | `src/backends/cpp/profiles/runtime_calls.json` | `os.path.join`, `glob.glob`, `ArgumentParser`, `re.sub`, `sys.stdout.write` などの C++ 呼び先 | symbol 所属と最終描画名が混在。index 不在だと ad-hoc fallback の温床になる | 当面は C++ 描画名テーブルとして維持しつつ、所属 module は IR + index へ分離 |
| tooling | `tools/build_multi_cpp.py` | manifest 内 source を起点に runtime source を再帰収集 | include から `.gen/.ext` companion を再構成するが、module/symbol 単位では見ていない | index を参照して module 単位で必要 artifact を導出 |
| tooling | `tools/gen_makefile_from_manifest.py` | manifest から runtime source を再収集 | build graph が include 依存の推測に寄る | index + manifest module 情報で compile source を決定 |

### 2. 何をどこへ残すか

| 情報 | IR に残す | index に移す | backend/tooling が導出 |
| - | - | - | - |
| `runtime_module_id` | はい | いいえ | いいえ |
| `runtime_symbol` | はい | いいえ | いいえ |
| `runtime_dispatch`（function / method / ctor など） | 必要最小限のみ | 補助的に保持可 | 描画時に参照 |
| target 別 header path (`runtime/cpp/std/time.gen.h`) | いいえ | はい | index から読む |
| target 別 compile source (`*.gen.cpp`, `*.ext.cpp`) | いいえ | はい | index から読む |
| `gen/ext` companion 規則 | いいえ | はい | index から読む |
| C++ namespace / fully-qualified symbol | いいえ | いいえ | backend が module + symbol + profile から導出 |
| include 並び順 / dedupe | いいえ | いいえ | backend/tooling |

### 3. この段階で固定する判断

- `runtime_call` 裸文字列だけでは不十分であり、S3 以降では `runtime_module_id` と `runtime_symbol` を正本にする。
- target 固有 file path は IR へ埋めない。
- `signature_registry.py` は「SoT から読み取れる symbol / 型 / owner-method 契約」を補助するだけに縮退し、artifact path や companion 推定を持たせない。
- C++ backend は `module.py` / `runtime_paths.py` / `runtime_calls.json` に責務が分散しているが、所属決定は index 化後に backend 外へ出す。

## S1-02 schema 固定（2026-03-06 版）

### 1. schema の責務

`runtime symbol index` は次の責務だけを持つ。

- module 単位で「どの symbol がその module から提供されるか」を示す
- target 単位で「その module を使うとき、どの artifact が必要か」を示す
- `gen/ext` companion の有無を示す

逆に、次は持たせない。

- EAST3 ノード全体
- C++ namespace 文字列
- backend 固有の描画構文
- owner method 解決ロジックそのもの

### 2. 最小 schema

```json
{
  "schema_version": 1,
  "generated_by": "tools/gen_runtime_symbol_index.py",
  "modules": {
    "pytra.built_in.iter_ops": {
      "source_py": "src/pytra/built_in/iter_ops.py",
      "runtime_group": "built_in",
      "symbols": {
        "py_enumerate_object": {
          "kind": "function",
          "dispatch": "function"
        },
        "py_reversed_object": {
          "kind": "function",
          "dispatch": "function"
        }
      }
    }
  },
  "targets": {
    "cpp": {
      "modules": {
        "pytra.built_in.iter_ops": {
          "public_headers": [
            "src/runtime/cpp/built_in/iter_ops.gen.h",
            "src/runtime/cpp/built_in/iter_ops.ext.h"
          ],
          "compile_sources": [
            "src/runtime/cpp/built_in/iter_ops.gen.cpp"
          ],
          "companions": [
            "gen",
            "ext"
          ]
        }
      }
    }
  }
}
```

### 3. field ごとの意味

| field | 所属 | 意味 |
| - | - | - |
| `schema_version` | ルート | 互換性判定用。破壊的変更時のみ更新 |
| `generated_by` | ルート | generator 名の固定 |
| `modules` | ルート | target 非依存の module/symbol 定義 |
| `source_py` | module | SoT となる Python module |
| `runtime_group` | module | `core / built_in / std / utils` の責務分類 |
| `symbols` | module | その module から公開される runtime symbol 群 |
| `kind` | symbol | `function` / `class` / `const` など |
| `dispatch` | symbol | `function` / `method` / `ctor` 等。IR の描画補助 |
| `targets` | ルート | target 別 artifact 情報 |
| `public_headers` | target module | include 対象となる header 群 |
| `compile_sources` | target module | build に載せる source 群 |
| `companions` | target module | `gen` / `ext` の存在宣言 |

### 4. companion 規則

- `companions=["gen"]`
  - `.gen.*` のみ存在する module
- `companions=["gen","ext"]`
  - `.gen.*` に加えて `.ext.h` または `.ext.cpp` が存在する module
- `companions=["ext"]`
  - 将来 `core/` で SoT 非依存の低レベル module を index 化する場合のみ許可

現段階では、`src/pytra/{built_in,std,utils}` 由来 module は原則 `gen` を必須とする。

### 5. 実装者向け禁止事項

- `py_enumerate -> iter_ops` を generator 内 dict へ直書きしない。
- `runtime/cpp/std/time.gen.h` のような path を IR へ埋めない。
- `signature_registry.py` を新しい index の source-of-truth にしない。
- `public_headers` と `compile_sources` を backend 側で再発明しない。

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

### 非C++ backend への適用方針（S5-01 固定）

- 非C++ backend も、runtime 呼び出しの所属決定には `runtime_module_id + runtime_symbol` を使う。
- target 固有の import path / package path / fully-qualified name は backend 側で描画してよい。
- ただし「どの module がその symbol を持つか」の対応を backend ごとに別 table として再実装してはならない。
- `resolved_runtime_call` は移行互換の補助情報として保持してよいが、module/file 解決の source-of-truth にしてはならない。
- target ごとの file path / companion は index 消費層で導出し、emitter 本体へ `if target == ... and symbol == ...` の所有表を増やしてはならない。

決定ログ:
- 2026-03-06: user 指示により、`runtime symbol -> module/file` 対応を Python ソースへ直書きする設計をやめ、SoT 生成 JSON + IR 正規化へ寄せる方針を確定。
- 2026-03-06: 本計画では「IR に埋めるのは target 非依存情報のみ」「target 別 file path は index + backend が導出」とする。
- 2026-03-06: [ID: `P0-RUNTIME-SYMBOL-INDEX-01-S1-01`] 直書き箇所の棚卸しを行い、`core.py` は裸 `runtime_call`、`signature_registry.py` は runtime symbol 対応、C++ backend (`module.py`, `runtime_paths.py`, `runtime_calls.json`) は module/file/namespace 推定、tooling (`build_multi_cpp.py`, `gen_makefile_from_manifest.py`) は include 起点の runtime source 再収集を担っていると固定した。役割分担は「IR=module+symbol」「index=artifact+companion」「backend/tooling=描画と build graph 導出」とする。
- 2026-03-06: [ID: `P0-RUNTIME-SYMBOL-INDEX-01-S1-02`] index schema は `modules` と `targets` を分離し、target 非依存の symbol 所属と target 別 artifact 情報を分ける形で固定した。`public_headers` / `compile_sources` / `companions` を最小集合とし、path を IR へ埋めないことを明文化した。
- 2026-03-06: [ID: `P0-RUNTIME-SYMBOL-INDEX-01-S2-01`] `tools/gen_runtime_symbol_index.py` を追加し、`src/pytra/{built_in,std,utils}` と modern runtime layout (`src/runtime/<lang>/{core,built_in,std,utils}`) を走査して `tools/runtime_symbol_index.json` を生成できるようにした。第1段階では modern layout を持つ target のみ artifact を index 化し、legacy runtime layout は index 対象外とする。
- 2026-03-06: [ID: `P0-RUNTIME-SYMBOL-INDEX-01-S2-02`] representative case を `test/unit/tooling/test_runtime_symbol_index.py` で固定し、`py_enumerate_object`, `py_any`, `py_strip`, `perf_counter`, `write_rgb_png`, `Path` の module/symbol/artifact/companion を検証するようにした。
- 2026-03-06: [ID: `P0-RUNTIME-SYMBOL-INDEX-01-S2-03`] generator に `--check` を追加し、`tools/run_local_ci.py` へ組み込んだ。stale index は fail-fast とする。
- 2026-03-06: [ID: `P0-RUNTIME-SYMBOL-INDEX-01-S3-01`] EAST3 の `BuiltinCall` へ `runtime_module_id` と `runtime_symbol` を併置した。第1段階では `runtime_call` は互換のため維持しつつ、`perf_counter -> pytra.std.time/perf_counter`, `enumerate -> pytra.built_in.iter_ops/enumerate`, `any -> pytra.built_in.predicates/any`, `dict.get -> pytra.core.dict/dict.get`, `Path.exists -> pytra.std.pathlib/Path.exists` のような target 非依存表現を持たせる。`test_east_core.py` は既存の `toolchain.compiler.east_parts` import 破綻で直接は起動できないため、同一 API を使う ad-hoc 実行で実値を確認した。
- 2026-03-06: [ID: `P0-RUNTIME-SYMBOL-INDEX-01-S3-02`] import 解決済み symbol にも `runtime_module_id` / `runtime_symbol` を埋めるよう拡張した。`from pytra.std import json` の `json.loads`、`from pytra.utils import png` の `png.write_rgb_png`、`import math` の `math.sin` / `math.pi` について、Call/Attribute の両ノードに module/symbol が付与されることを ad-hoc 実行で確認した。
- 2026-03-06: [ID: `P0-RUNTIME-SYMBOL-INDEX-01-S3-03`] `signature_registry.py` に `runtime/cpp`, `*.gen.*`, `*.ext.*`, `src/runtime` といった artifact path 推定責務が再混入しないことを `test_stdlib_signature_registry.py` で固定した。現段階では runtime symbol / 型 / owner-method 契約は残すが、file path 推定責務は generator + index 側へ完全に分離した状態を回帰で保証する。
- 2026-03-06: [ID: `P0-RUNTIME-SYMBOL-INDEX-01-S4-01`] index generator を `pytra.core.*` artifact まで拡張し、`runtime_symbol_index.py` に `canonical_runtime_module_id` / `resolve_import_binding_runtime_module` / `lookup_cpp_namespace_for_runtime_module` を追加した。C++ backend は `module.py` の import include 収集と namespace 解決を index ベースへ切り替え、`from pytra.utils import png`・`from pytra.std.time import perf_counter`・`import math` の C++ 出力が index 経由で `runtime/cpp/...` include と namespace を解決することを unit/integration test で固定した。
- 2026-03-06: [ID: `P0-RUNTIME-SYMBOL-INDEX-01-S4-02`] `tools/cpp_runtime_deps.py` に index 逆引きを追加し、`build_multi_cpp.py` / `gen_makefile_from_manifest.py` の runtime companion 導出を `runtime_symbol_index.json` ベースへ寄せた。forwarder header から `math.ext.cpp` を引く既存テスト (`test_cpp_runtime_build_graph.py`) は通過した。
- 2026-03-06: [ID: `P0-RUNTIME-SYMBOL-INDEX-01-S4-03`] C++ emitter の `BuiltinCall` dispatch と imported symbol call 描画で、`runtime_call` 文字列のみに依存せず `runtime_module_id/runtime_symbol` を優先するようにした。対象は `py_enumerate` / `py_any` / `py_all` / `py_strip` 系 / `dict.get` 系 / `perf_counter` / `Path` で、IR に binding が載っていることと C++ 出力が namespaced call へ落ちることを `test_cpp_runtime_symbol_index_integration.py` で固定した。
- 2026-03-06: [ID: `P0-RUNTIME-SYMBOL-INDEX-01-S5-01` / `-S5-02`] 非C++ backend へも `runtime_module_id + runtime_symbol + runtime_symbol_index` を唯一の所属決定経路として適用する方針を本計画と `docs/ja/spec/{spec-runtime.md,spec-east.md}` へ明記した。target 固有 import/file path は backend が導出してよいが、module 所属対応を backend ごとの手書き table として再導入してはならない。
- 2026-03-06: [ID: `P0-RUNTIME-SYMBOL-INDEX-01-S5-03`] representative regression として `tools/gen_runtime_symbol_index.py --check`、`test_runtime_symbol_index.py`、`test_cpp_runtime_build_graph.py`、`test_cpp_runtime_symbol_index_integration.py`、`tools/runtime_parity_check.py --targets cpp --case-root fixture` を実行し、C++ include 解決・runtime build graph・import resolution・fixture parity が index 前提で通ることを確認した。`math_extended/pathlib_extended/inheritance_virtual_dispatch_multilang` はすべて `pass`。
