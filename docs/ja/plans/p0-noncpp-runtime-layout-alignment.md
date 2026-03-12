# P0: non-C++ runtime を C++ 比較可能な `generated/native` layout へ揃える

最終更新: 2026-03-12

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01`

背景:
- 現行 non-C++ runtime は `pytra-core/pytra-gen/pytra` 命名に依存しているが、C++ は `generated/native/core/pytra` の ownership split を持ち、runtime file を lane 単位で比較しやすい。
- この差で、`json/pathlib/gif/png/...` のような SoT 由来 module が「未生成で欠けている」のか「手書き実装が core に残っている」のかを tree diff だけで判断しづらい。
- ユーザー方針として、`generated/` に置かれるものはすべて SoT (`src/pytra/**`) からの自動生成物でなければならず、hand-written file を直接移す運用は認めない。

目的:
- non-C++ backend でも `generated/` と `native/` を正式 lane とし、C++ と同じ観点で runtime tree を比較可能にする。
- `generated/` には SoT 自動生成物のみ、`native/` には hand-written runtime のみを置く。
- `rs/cs` を先行対象として、current work target に直結する runtime layout を先に切り替える。

対象:
- `src/runtime/{rs,cs}/**`
- `tools/gen_runtime_from_manifest.py`
- `tools/runtime_generation_manifest.json`
- `src/toolchain/compiler/backend_registry_metadata.py`
- `src/toolchain/compiler/pytra_cli_profiles.py`
- runtime guard / allowlist / docs

非対象:
- C++ runtime 自体の再設計
- 1 turn で全 backend を一括 rename すること
- `pytra/` public shim の即時廃止

受け入れ基準:
- `src/runtime/{rs,cs}/generated/**` が存在し、そこに置かれる file はすべて `source:` と `generated-by:` を持つ自動生成物である。
- `src/runtime/{rs,cs}/native/**` が存在し、そこに `generated-by:` marker は存在しない。
- `tools/runtime_generation_manifest.json` は `rs/cs` の SoT 生成物を `generated/` へ出力する。
- `backend_registry_metadata.py` / `pytra_cli_profiles.py` / selfhost check は `rs/cs` の新 layout を参照する。
- runtime guard は `pytra-gen/pytra-core` 前提ではなく、`generated/native` lane を正本として監査する。
- 比較単位を `lane/bucket/module` に固定したとき、`rs/cs` で `generated/utils/{png,gif}` と `native/{built_in,std}` の欠落/残置が tree diff で判別できる。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_runtime_core_gen_markers.py`
- `python3 tools/check_runtime_pytra_gen_naming.py`
- `python3 tools/check_runtime_std_sot_guard.py`
- `python3 tools/check_cs_single_source_selfhost_compile.py`
- `PYTHONPATH=src:.:test/unit python3 -m unittest discover -s test/unit/backends/cs -p 'test_py2cs_smoke.py'`

実施方針:
1. `generated/` へ hand-written file を移すのではなく、manifest/generator から再生成して配置する。
2. `native/` は current `pytra-core` の rename lane として導入し、必要最小限の hand-written runtime だけを残す。
3. `pytra/` は public shim / compatibility lane として当面残してよいが、ownership 判定の正本にしてはならない。
4. file-level compare は拡張子差を無視した `<lane>/<bucket>/<module>` 単位で行う。

## 期待レイアウト

`rs/cs` の canonical layout:

- `src/runtime/<lang>/generated/{built_in,std,utils}/`
  - SoT (`src/pytra/**`) からの自動生成物のみ
- `src/runtime/<lang>/native/{built_in,std,utils}/`
  - hand-written runtime のみ
- `src/runtime/<lang>/pytra/{built_in,std,utils}/`
  - public shim / compatibility lane（必要時のみ）

注記:
- C++ 固有の `core/` と `.h/.cpp` 2-file split は non-C++ にそのまま持ち込まない。
- ただし compare 単位は C++ と揃え、`generated/std/json` / `generated/utils/gif` / `native/built_in/py_runtime` のように lane と module が 1 対 1 に見えることを優先する。

## compare 単位

canonical compare unit は `<lane>/<bucket>/<module>` とし、拡張子差分や backend 固有の source/header 分割は比較対象から外す。

- lane:
  - `generated`
  - `native`
  - `pytra`（compat/public shim、ownership 判定には使わない）
- bucket:
  - `built_in`
  - `std`
  - `utils`
  - `compiler`
- module 例:
  - `generated/utils/gif`
  - `generated/utils/png`
  - `native/built_in/py_runtime`
  - `native/std/json`

この compare 単位を基準に、`missing generated artifact` と `hand-written residual still in native` を tree diff だけで判別できる状態を正とする。

## current → target 対応表（first wave: rs/cs）

### Rust

| current path | target lane/module | ownership |
| --- | --- | --- |
| `src/runtime/rs/pytra-core/built_in/py_runtime.rs` | `native/built_in/py_runtime` | hand-written |
| `src/runtime/rs/pytra-gen/utils/gif.rs` | `generated/utils/gif` | SoT generated |
| `src/runtime/rs/pytra-gen/utils/png.rs` | `generated/utils/png` | SoT generated |
| `src/runtime/rs/pytra-gen/utils/image_runtime.rs` | `generated/utils/image_runtime` | SoT generated |
| `src/runtime/rs/pytra/**` | `pytra/**` | compat/public shim |

### C#

| current path | target lane/module | ownership |
| --- | --- | --- |
| `src/runtime/cs/pytra-core/built_in/math.cs` | `native/built_in/math` | hand-written |
| `src/runtime/cs/pytra-core/built_in/py_runtime.cs` | `native/built_in/py_runtime` | hand-written |
| `src/runtime/cs/pytra-core/built_in/time.cs` | `native/built_in/time` | hand-written |
| `src/runtime/cs/pytra-core/std/json.cs` | `native/std/json` | hand-written |
| `src/runtime/cs/pytra-core/std/pathlib.cs` | `native/std/pathlib` | hand-written |
| `src/runtime/cs/pytra-gen/utils/gif.cs` | `generated/utils/gif` | SoT generated |
| `src/runtime/cs/pytra-gen/utils/png.cs` | `generated/utils/png` | SoT generated |
| `src/runtime/cs/pytra/**` | `pytra/**` | compat/public shim |

## 分解

- [x] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S1-01] non-C++ runtime の canonical `generated/native/pytra` layout と compare 単位を spec/plan に固定する。
- [x] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S1-02] `rs/cs` の current `pytra-core/pytra-gen` tree と、新 `generated/native` tree の対応表を作る。
- [x] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S2-01] `rs` を `pytra-core -> native`, `pytra-gen -> generated` へ切り替え、runtime hook と guard を同期する。
- [x] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S2-02] `cs` を `pytra-core -> native`, `pytra-gen -> generated` へ切り替え、build/selfhost/runtime path を同期する。
- [x] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S2-03] `rs/cs` の `png/gif` を新 `generated/utils` へ SoT から再生成し、旧 path 依存を除去する。
- [ ] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S3-01] `cs` の `json/pathlib/math/re/argparse/enum` について、`generated/std` へ載せる対象と `native` に残す対象を module 単位で確定する。
- [ ] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S3-02] `rs/cs` の std lane を `generated/std` へ段階移管し、hand-written 実装を `native` へ縮退させる。
- [ ] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S4-01] runtime guard / allowlist / docs を `generated/native` vocabulary に全面更新する。
- [ ] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S4-02] `go/java/kt/scala/swift/nim/js/ts/lua/rb/php` へ同 layout を展開する wave plan を確定する。

決定ログ:
- 2026-03-12: ユーザー指示により、non-C++ runtime を `generated/` と `native/` に揃え、`generated/` には SoT 自動生成物だけを置く方針を P0 として最優先化した。
- 2026-03-12: C++ と完全同一の tree を複製するのではなく、比較単位を `lane/bucket/module` に揃える方針を採用した。`.h/.cpp` と単一 `.rs/.cs` の差は compare 上の枝葉として扱う。
- 2026-03-12: `S1-01/S1-02` として `generated/native/pytra` の canonical compare unit を `<lane>/<bucket>/<module>` に固定し、`rs/cs` の current `pytra-core/pytra-gen` tree を target lane/module に写像した。first wave では `pytra/**` を compat/public shim として残し、ownership 正本には使わない。
- 2026-03-12: `P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S2-01` / `P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S2-02` / `P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S2-03` として、`src/runtime/{rs,cs}/{native,generated}` へ実 tree を切り替え、Rust runtime hook、C# build/selfhost/runtime path、runtime guard / allowlist / inventory を同期し、`tools/gen_runtime_from_manifest.py --targets rs,cs --items utils/png,utils/gif` を再実行した。
- 2026-03-12: `P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S3-01` の先行調査として `json.py` / `pathlib.py` の `cs/rs` 生成可能性を確認した。`json.py` は `@abi` target 制限で `cs/rs` が停止し、`pathlib.py` は `os/os_path/glob` runtime import lane の未整備で generated std としては未配線だったため、std lane 移管は次 wave へ繰り越す。
