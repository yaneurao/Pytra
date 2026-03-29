<a href="../../../en/plans/archive/20260313-p0-noncpp-runtime-layout-alignment.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: `rs/cs` runtime を C++ 比較可能な `generated/native` layout へ揃える

最終更新: 2026-03-13

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01`

背景:
- 現行 `rs/cs` runtime は `pytra-core/pytra-gen/pytra` 命名に依存しているが、C++ は `generated/native/core/pytra` の ownership split を持ち、runtime file を lane 単位で比較しやすい。
- この差で、`json/pathlib/gif/png/...` のような SoT 由来 module が「未生成で欠けている」のか「手書き実装が core に残っている」のかを tree diff だけで判断しづらい。
- ユーザー方針として、`generated/` に置かれるものはすべて SoT (`src/pytra/**`) からの自動生成物でなければならず、hand-written file を直接移す運用は認めない。
- ユーザー指示として、`rs/cs` は P0 に固定し、残 backend の同種 rollout は別 P1 task に切り分ける。

目的:
- `rs/cs` で `generated/` と `native/` を正式 lane とし、C++ と同じ観点で runtime tree を比較可能にする。
- `generated/` には SoT 自動生成物のみ、`native/` には hand-written runtime のみを置く。
- `src/pytra/built_in/*.py` に対応する `generated/built_in/*` も `rs/cs` に実体化し、`std/utils` と同じ SoT lane に揃える。

対象:
- `src/runtime/{rs,cs}/**`
- `tools/gen/gen_runtime_from_manifest.py`
- `tools/runtime_generation_manifest.json`
- `src/toolchain/compiler/backend_registry_metadata.py`
- `src/toolchain/compiler/pytra_cli_profiles.py`
- runtime guard / allowlist / docs

非対象:
- C++ runtime 自体の再設計
- `go/java/kt/scala/swift/nim/js/ts/lua/rb/php` への rollout
- Rust `pytra/` compatibility lane の即時廃止

受け入れ基準:
- `src/runtime/{rs,cs}/generated/**` が存在し、そこに置かれる file はすべて `source:` と `generated-by:` を持つ自動生成物である。
- `src/runtime/{rs,cs}/native/**` が存在し、そこに `generated-by:` marker は存在しない。
- `tools/runtime_generation_manifest.json` は `rs/cs` の SoT 生成物を `generated/` へ出力する。
- `src/runtime/{rs,cs}/generated/built_in/*` に `src/pytra/built_in/*.py` 起源の module が揃い、`cpp/generated/built_in/*` と `<lane>/<bucket>/<module>` 単位で比較できる。
- `backend_registry_metadata.py` / `pytra_cli_profiles.py` / selfhost check は `rs/cs` の新 layout を参照する。
- runtime guard は `pytra-gen/pytra-core` 前提ではなく、`generated/native` lane を正本として監査する。
- 比較単位を `lane/bucket/module` に固定したとき、`rs/cs` で `generated/{built_in,std,utils}` と `native/{built_in,std}` の欠落/残置が tree diff で判別できる。
- `src/runtime/cs/pytra/**` は canonical 実装を持たず、残る場合でも一時互換物に限る。最終的には空にするか削除する。

確認コマンド（予定）:
- `python3 tools/check/check_todo_priority.py`
- `python3 tools/check/check_runtime_core_gen_markers.py`
- `python3 tools/check/check_runtime_pytra_gen_naming.py`
- `python3 tools/check/check_runtime_std_sot_guard.py`
- `python3 tools/check/check_cs_single_source_selfhost_compile.py`
- `PYTHONPATH=src:.:test/unit python3 -m unittest discover -s tools/unittest/emit/cs -p 'test_py2cs_smoke.py'`

実施方針:
1. `generated/` へ hand-written file を移すのではなく、manifest/generator から再生成して配置する。
2. `native/` は current `pytra-core` の rename lane として導入し、必要最小限の hand-written runtime だけを残す。
3. Rust の `pytra/` は compatibility lane として当面残してよいが、ownership 判定の正本にしてはならない。C# の `pytra/` は shim 置き場にならないので、実装本体を置かず削除対象として扱う。
4. file-level compare は拡張子差を無視した `<lane>/<bucket>/<module>` 単位で行う。
5. `generated/built_in/*` は `src/pytra/built_in/*.py` の SoT lane とし、`py_runtime.*` のような substrate は `native/built_in/*` に残す。

## 期待レイアウト

`rs/cs` の canonical layout:

- `src/runtime/<lang>/generated/{built_in,std,utils}/`
  - SoT (`src/pytra/**`) からの自動生成物のみ
- `src/runtime/<lang>/native/{built_in,std,utils}/`
  - hand-written runtime のみ
- `src/runtime/<lang>/pytra/{built_in,std,utils}/`
  - Rust では compatibility lane（必要時のみ）
  - C# では原則不要。実装本体は置かず、残置 duplicate は削除対象

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
| `src/runtime/cs/pytra/**` | remove / empty lane | duplicate residual (delete target) |

## 分解

- [x] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S1-01] non-C++ runtime の canonical `generated/native/pytra` layout と compare 単位を spec/plan に固定する。
- [x] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S1-02] `rs/cs` の current `pytra-core/pytra-gen` tree と、新 `generated/native` tree の対応表を作る。
- [x] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S2-01] `rs` を `pytra-core -> native`, `pytra-gen -> generated` へ切り替え、runtime hook と guard を同期する。
- [x] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S2-02] `cs` を `pytra-core -> native`, `pytra-gen -> generated` へ切り替え、build/selfhost/runtime path を同期する。
- [x] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S2-03] `rs/cs` の `png/gif` を新 `generated/utils` へ SoT から再生成し、旧 path 依存を除去する。
- [x] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S3-01] `cs` の `json/pathlib/math/re/argparse/enum` について、`generated/std` へ載せる対象と `native` に残す対象を module 単位で確定する。
- [x] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S3-02] `rs/cs` の std lane を `generated/std` へ段階移管し、hand-written 実装を `native` へ縮退させる。
  - [x] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S3-02-A] `rs` std lane の current ownership を固定し、`math/time` native・`pathlib/os/os_path/glob` compare artifact・`json/re/argparse/enum` no-live-module の baseline を guard する。
  - [x] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S3-02-B] `cs` の first live-generated std candidate を `time` に固定し、`json/pathlib/math` を deferred native-canonical lane、`re/argparse/enum` を deferred no-runtime lane と切り分ける。
  - [x] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S3-02-C] 選定した `rs/cs` std lane を build/runtime hook へ実配線し、compare artifact だけの状態を縮退させる。
- [x] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S4-01] `src/pytra/built_in/*.py` から `rs/cs` の `generated/built_in/*` を生成し、`cpp/generated/built_in/*` と compare 可能な lane を揃える。
- [x] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S4-02] `generated/built_in/*` と `native/built_in/*` の責務境界を確定し、`py_runtime.*` に残る built-in 相当実装を縮退させる。あわせて C# の `pytra/**` duplicate lane（`math/time/json/pathlib/png/gif` など）を削除対象として整理する。
- [x] [ID: P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S5-01] runtime guard / allowlist / docs を `generated/native` vocabulary に全面更新する。

決定ログ:
- 2026-03-12: ユーザー指示により、non-C++ runtime を `generated/` と `native/` に揃え、`generated/` には SoT 自動生成物だけを置く方針を P0 として最優先化した。
- 2026-03-12: C++ と完全同一の tree を複製するのではなく、比較単位を `lane/bucket/module` に揃える方針を採用した。`.h/.cpp` と単一 `.rs/.cs` の差は compare 上の枝葉として扱う。
- 2026-03-12: `S1-01/S1-02` として `generated/native/pytra` の canonical compare unit を `<lane>/<bucket>/<module>` に固定し、`rs/cs` の current `pytra-core/pytra-gen` tree を target lane/module に写像した。first wave では `pytra/**` を compat/public shim として残し、ownership 正本には使わない。
- 2026-03-12: `P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S2-01` / `P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S2-02` / `P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S2-03` として、`src/runtime/{rs,cs}/{native,generated}` へ実 tree を切り替え、Rust runtime hook、C# build/selfhost/runtime path、runtime guard / allowlist / inventory を同期し、`tools/gen/gen_runtime_from_manifest.py --targets rs,cs --items utils/png,utils/gif` を再実行した。
- 2026-03-12: `P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S3-01` の先行調査として `json.py` / `pathlib.py` の `cs/rs` 生成可能性を確認した。`json.py` は `@abi` target 制限で `cs/rs` が停止し、`pathlib.py` は `os/os_path/glob` runtime import lane の未整備で generated std としては未配線だったため、std lane 移管は次 wave へ繰り越す。
- 2026-03-12: `P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01` の compare lane 拡張として、`tools/runtime_generation_manifest.json` に `rs/cs` の `std/{time,math,os,os_path,glob,pathlib}` を追加し、`src/runtime/{rs,cs}/generated/std/*` を SoT から生成した。現時点では tree compare 用 lane を先行実体化し、build/runtime hook は `native` 優先のまま維持する。
- 2026-03-12: `P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S3-01` として C# std lane ownership contract を `noncpp_runtime_layout_contract.py` / `check_noncpp_runtime_layout_contract.py` に固定した。current decision は `json=native/std + generated blocked`, `pathlib=native/std canonical + generated compare artifact`, `math=native/built_in canonical + generated compare artifact`, `re/argparse/enum=no runtime module` で、build profile / emitter alias / C# smoke の 3 面で guard する。
- 2026-03-12: ユーザー指示に従い、この P0 は `rs/cs` 専用 lane に再定義し、残 backend の同種 rollout は別 P1 task へ切り出す方針に変更した。`generated/built_in/*` も P0 の必須対象に含める。
- 2026-03-12: `P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S3-02-A` として Rust std lane ownership baseline を `noncpp_runtime_layout_contract.py` / `check_noncpp_runtime_layout_contract.py` に追加した。current decision は `time/math=native/built_in canonical + generated compare artifact`, `pathlib/os/os_path/glob=no live runtime module + generated compare artifact`, `json=generated blocked + no live runtime module`, `re/argparse/enum=no runtime module` で、manifest / native scaffold / rs smoke の 3 面で guard する。
- 2026-03-12: `P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S4-01` として `tools/runtime_generation_manifest.json` に `built_in/{contains,io_ops,iter_ops,numeric_ops,predicates,scalar_ops,sequence,string_ops,type_id,zip_ops}` の `rs/cs` target を追加し、`tools/gen/gen_runtime_from_manifest.py --targets rs,cs --items ...` で `src/runtime/{rs,cs}/generated/built_in/*` を SoT から再生成した。C# compare lane は `Program` class 衝突を避けるため `cs_program_to_helper` を通して helper class 化する。
- 2026-03-12: `P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S3-02-B` として C# の first live-generated std candidate を `time` に固定した。`generated/std/time.cs` は compare artifact のままだが、representative surface が `perf_counter()` の単一 lane で最も薄いため、次の live-generated wiring 候補とする。一方で `json/pathlib/math` は deferred native-canonical、`re/argparse/enum` は deferred no-runtime lane として contract / smoke / docs で切り分けた。
- 2026-03-12: `P0-NONCPP-RUNTIME-LAYOUT-ALIGN-01-S3-02-C` として C# `generated/std/time.cs` を `cs_std_time_live_wrapper` 経由で `namespace Pytra.CsModule { public static class time { ... } }` に再生成し、native `time_native` backing seam を参照する live-generated lane に切り替えた。`pytra_cli_profiles.py` の C# build plan は generated/std/time.cs を canonical module として compile しつつ native/built_in/time.cs を backing seam として残し、contract checker も wrapper 内容まで監査する。
- 2026-03-12: ユーザー指示により、C# の `pytra/` は shim/public lane として扱わない方針を明文化した。`#include` 相当の仕組みがないため、`src/runtime/cs/pytra/**` に実装本体を置く理由はなく、残る duplicate file は `S4-02` で削除対象として整理する。
- 2026-03-12: `S4-02` の current boundary inventory として、`generated/built_in/*` は `contains/io_ops/iter_ops/numeric_ops/predicates/scalar_ops/sequence/string_ops/type_id/zip_ops` の exact SoT set、`native/built_in/*` residual は `rs={py_runtime}` / `cs={math,py_runtime,time}`、C# `pytra/**` duplicate delete target は `built_in/{math,py_runtime,time}`, `std/{json,pathlib}`, `utils/{gif,png}` の 7 file に固定した。Rust `pytra/**` は `README* + built_in/py_runtime.rs` だけを compatibility allowlist として残す。
- 2026-03-12: `S4-02` を完了し、`src/runtime/cs/pytra/**` の 7 つの duplicate lane (`built_in/{math,py_runtime,time}`, `std/{json,pathlib}`, `utils/{gif,png}`) を物理削除した。checker は allowlist 固定から「duplicate lane は空で、delete target はすべて不存在」へ切り替え、crossruntime residual/thincompat inventory と docs も native/generated canonical lane 前提に同期した。
- 2026-03-13: `S5-01` の first docs/guard bundle として、`check_runtime_pytra_gen_naming.py` / `check_runtime_core_gen_markers.py` の policy 文言を `rs/cs = generated/native canonical, pytra-gen/pytra-core = legacy scan target` に更新し、user-facing docs でも Rust runtime path を `src/runtime/rs/{native,generated}/` 正本・`src/runtime/rs/pytra/` 互換 lane として明記した。
- 2026-03-13: `S5-01` の second guard bundle として `check_rs_runtime_layout.py` を `src/runtime/rs/native/**` 正本・`src/runtime/rs/pytra/**` 互換 lane 前提に更新し、`test_check_rs_runtime_layout.py` で canonical runtime 必須 / compat lane 任意の contract を固定した。
- 2026-03-13: `S5-01` の third docs/guard bundle として `check_runtime_std_sot_guard.py` と `spec-tools.md` の vocabulary を `rs/cs = generated/native canonical, pytra-gen/pytra-core = legacy/未移行 backend context` に同期し、`std/utils` guard も `generated/native/pytra` ownership を前提に説明するよう揃えた。
- 2026-03-13: `S5-01` の fourth guard bundle として `runtime_std_sot_allowlist.txt` と `check_runtime_std_sot_guard.py` の出力文言を canonical generated lane 前提に更新し、allowlist 自体を `legacy migration debt only` として説明するよう揃えた。
