<a href="../../ja/plans/archive/20260306-p0-cpp-pyruntime-ext-slimming.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/archive/20260306-p0-cpp-pyruntime-ext-slimming.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/archive/20260306-p0-cpp-pyruntime-ext-slimming.md`

# P0: C++ `py_runtime.ext.h` 縮退（pure Python 正本への移管）

最終更新: 2026-03-06

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-EXT-01`

背景:
- `src/runtime/cpp/core/py_runtime.ext.h` には、C++ ABI / object 表現と、pure Python 正本へ移管できる高レベル built-in 意味論が混在している。
- すでに `src/pytra/built_in/{predicates,sequence,string_ops}.py` と `src/pytra/std/{re,argparse}.py` に正本があるにもかかわらず、`py_runtime.ext.h` 側にも同等実装が残っている。
- この重複は runtime 境界を曖昧にし、以後の多言語展開・selfhost・再生成で手戻りを生む。

目的:
- `py_runtime.ext.h` を「C++ ABI / object 表現 / 低レベル typed helper」に限定する。
- pure Python 正本がある処理は、C++ generated runtime (`*.gen.h/.gen.cpp`) へ寄せる。
- ただし、typed fastpath や template ベース adapter が必要なものは、薄い `*.ext.*` を残して良い。

対象:
- `src/runtime/cpp/core/py_runtime.ext.h`
- `src/pytra/built_in/{predicates,sequence,string_ops}.py`
- `src/pytra/std/{re,argparse}.py`
- `src/runtime/cpp/{built_in,std}/*.gen.*`
- C++ backend の include / runtime 参照 / guard / parity テスト

非対象:
- `PyObj` 派生クラス、`make_object`, `py_to<T>`, `obj_to_*`, `py_iter_or_raise`, `py_slice`, `py_at`, `py_dict_get` など ABI 直結 helper の設計変更
- 非 C++ backend の同時改修
- EAST3 での runtime_call 契約そのものの再設計

受け入れ基準:
- `py_runtime.ext.h` から以下が除去されている:
  - `sub(...)`
  - `ArgumentParser`
  - `py_any` / `py_all`
  - `py_strip` / `py_startswith` / `py_endswith` / `py_find` / `py_replace`
  - `py_range` / `py_repeat`
- 上記機能は対応する `src/pytra/*` 正本から生成された `*.gen.*` 側にのみ存在する。
- `py_runtime.ext.h` には、上記 generated runtime を呼ぶための薄い adapter だけが残るか、または call site が直接 generated runtime を参照する。
- 第二段階として `py_enumerate` / `py_reversed` / `py_contains` について、pure Python 正本 + typed adapter 分離方針が確定している。
- `python3 tools/check/check_runtime_cpp_layout.py` と `python3 tools/check/check_runtime_std_sot_guard.py` が通る。
- `python3 tools/check/verify_image_runtime_parity.py` が通る。
- 少なくとも runtime smoke として `--emit-runtime-cpp` で `predicates/sequence/string_ops/re/argparse` の生成が崩れない。

確認コマンド（予定）:
- `python3 tools/check/check_todo_priority.py`
- `python3 tools/check/check_runtime_cpp_layout.py`
- `python3 tools/check/check_runtime_std_sot_guard.py`
- `python3 tools/check/verify_image_runtime_parity.py`
- `PYTHONPATH=src python3 src/backends/cpp/cli.py src/pytra/built_in/predicates.py --emit-runtime-cpp`
- `PYTHONPATH=src python3 src/backends/cpp/cli.py src/pytra/built_in/sequence.py --emit-runtime-cpp`
- `PYTHONPATH=src python3 src/backends/cpp/cli.py src/pytra/built_in/string_ops.py --emit-runtime-cpp`
- `PYTHONPATH=src python3 src/backends/cpp/cli.py src/pytra/std/re.py --emit-runtime-cpp`
- `PYTHONPATH=src python3 src/backends/cpp/cli.py src/pytra/std/argparse.py --emit-runtime-cpp`

実施方針:
1. 先に「重複している実装」を inventory 化し、正本・生成物・adapter の責務を固定する。
2. すでに pure Python 正本がある処理から先に ext から追い出す。
3. `enumerate/reversed/contains` のように typed fastpath を伴うものは、正本と adapter を分離して段階移行する。
4. ext 側で新たな stdlib/built-in 実装を増やさないよう、ガードを追加する。

## 棚卸し

### ext から先に除去する重複実装

| ext 側の残置 | 正本 | 移管先 | 補足 |
| --- | --- | --- | --- |
| `sub(...)` | `src/pytra/std/re.py` | `src/runtime/cpp/std/re.gen.*` | 既に generated runtime があるため、重複排除のみ |
| `ArgumentParser` | `src/pytra/std/argparse.py` | `src/runtime/cpp/std/argparse.gen.*` | built-in ではなく std の責務 |
| `py_any` / `py_all` | `src/pytra/built_in/predicates.py` | `src/runtime/cpp/built_in/predicates.gen.*` | call site 名寄せまたは薄い adapter |
| `py_strip` / `py_startswith` / `py_endswith` / `py_find` / `py_replace` | `src/pytra/built_in/string_ops.py` | `src/runtime/cpp/built_in/string_ops.gen.*` | call site 名寄せまたは薄い adapter |
| `py_range` / `py_repeat` | `src/pytra/built_in/sequence.py` | `src/runtime/cpp/built_in/sequence.gen.*` | call site 名寄せまたは薄い adapter |

### 第二段階で adapter 分離する候補

| 関数 | 現状 | 移行方針 |
| --- | --- | --- |
| `py_enumerate` | `list<T>`, `str`, `object`, `any` の overload が ext に集中 | pure Python 正本を追加し、typed overload は薄い adapter に縮退 |
| `py_reversed` | typed / any の overload が ext に残る | pure Python 正本を追加し、typed overload は adapter 化 |
| `py_contains` | `dict/list/set/str/object/tuple` の template 群が ext に残る | 共通意味論を正本化し、template fastpath は ext 側の最小 helper に限定 |

## 分解

- [x] [ID: P0-CPP-PYRUNTIME-EXT-01-S1-01] `py_runtime.ext.h` の関数棚卸しを行い、`ABI/core` と `pure Python 正本へ移管可能` を分類して固定する。
- [x] [ID: P0-CPP-PYRUNTIME-EXT-01-S1-02] `sub` / `ArgumentParser` / `py_any` / `py_all` / string_ops / `py_range` / `py_repeat` の正本・生成物・adapter 対応表を決定ログへ固定する。
- [x] [ID: P0-CPP-PYRUNTIME-EXT-01-S2-01] `sub(...)` の ext 側重複実装を除去し、`re.gen.*` 参照へ一本化する。
- [x] [ID: P0-CPP-PYRUNTIME-EXT-01-S2-02] `ArgumentParser` を ext から除去し、`argparse.gen.*` を正本 runtime として使うよう C++ 側導線を揃える。
- [x] [ID: P0-CPP-PYRUNTIME-EXT-01-S2-03] `py_any` / `py_all` を ext から除去し、`predicates.gen.*` 参照へ一本化する。
- [x] [ID: P0-CPP-PYRUNTIME-EXT-01-S2-04] `py_strip` / `py_startswith` / `py_endswith` / `py_find` / `py_replace` を ext から除去し、`string_ops.gen.*` 参照へ一本化する。
- [x] [ID: P0-CPP-PYRUNTIME-EXT-01-S2-05] `py_range` / `py_repeat` を ext から除去し、`sequence.gen.*` 参照へ一本化する。
- [x] [ID: P0-CPP-PYRUNTIME-EXT-01-S3-01] `py_enumerate` / `py_reversed` / `py_contains` について、pure Python 正本 + typed adapter 分離の仕様を決め、必要な `src/pytra/built_in/*.py` を追加する。
- [x] [ID: P0-CPP-PYRUNTIME-EXT-01-S3-02] 上記 3 系統のうち、移しやすいものから 1 系統以上を ext 縮退まで実装し、残件を同計画内で継続可能な形にする。
- [x] [ID: P0-CPP-PYRUNTIME-EXT-01-S4-01] `py_runtime.ext.h` へ正本重複実装が再混入しないよう、静的ガードを追加する。
- [x] [ID: P0-CPP-PYRUNTIME-EXT-01-S4-02] layout / SoT guard / runtime parity / runtime emit smoke を更新し、縮退後の非退行を固定する。

決定ログ:
- 2026-03-06: ユーザー指示に基づき、`py_runtime.ext.h` をさらに縮退し、pure Python 正本がある処理を `*.gen.*` 側へ移す P0 計画として再整理した。
- 2026-03-06: 第一波は「すでに正本がある重複実装の除去」（`sub`, `ArgumentParser`, `py_any`, `py_all`, string_ops, `py_range`, `py_repeat`）に限定し、第二波として `py_enumerate` / `py_reversed` / `py_contains` の adapter 分離を扱う方針を確定した。
- 2026-03-06: `PyObj` 派生クラス、`make_object`, `py_to<T>`, `obj_to_*`, `py_iter_or_raise`, `py_slice`, `py_at`, `py_dict_get` は ABI/typed helper のため本計画の非対象に固定した。
- 2026-03-06: 第一波を実装し、`py_runtime.ext.h` から `sub`, `ArgumentParser`, `py_any`, `py_all`, string helper 群, `py_range`, `py_repeat(str, int)` の本体を撤去した。`predicates.py` / `string_ops.py` は public runtime 名に合わせて再生成し、`py_repeat(list<T>, int64)` だけを `src/runtime/cpp/built_in/sequence.ext.h` へ薄い typed adapter として残した。
- 2026-03-06: C++ backend 側は `any/all` を `make_object(...)` 経由で `predicates.gen.*` へ接続し、`find/rfind` の window 付き呼び出しは `py_find_window` / `py_rfind_window` へ寄せた。`pytra.std.argparse.ArgumentParser` と `pytra.std.re.sub` の runtime call mapping も namespaced generated runtime へ更新した。
- 2026-03-06: `tools/check/check_runtime_cpp_layout.py` に `py_runtime.ext.h` への高レベル重複実装再混入ガードを追加した。`check_runtime_cpp_layout.py`, `check_runtime_std_sot_guard.py`, `verify_image_runtime_parity.py`, built_in+`re` の syntax-only compile, `predicates/sequence/string_ops/re/argparse` の `--emit-runtime-cpp` smoke は通過した。
- 2026-03-06: `src/runtime/cpp/std/argparse.gen.cpp` には本タスク以前から存在する C++ emission 問題（`default` 識別子、`setattr`/`SystemExit`、`optional<list<str>>` など）が残っており、これは `py_runtime.ext.h` 縮退とは別件として扱う。今回の S2-02 は「導線の差し替えと ext 側重複実装の除去」に限定して完了扱いとする。
- 2026-03-06: 第二波の先行分として `src/pytra/built_in/iter_ops.py` を追加し、`py_reversed` / `py_enumerate` の object 経路本体を generated runtime (`iter_ops.gen.*`) へ移した。`py_runtime.ext.h` には typed `list<T>` / `str` / `any` adapter と `py_enumerate_list_as<T>` だけを残し、object overload は `src/runtime/cpp/built_in/iter_ops.ext.h` の薄い wrapper に置き換えた。
- 2026-03-06: `py_reversed` / `py_enumerate` の typed `list<T>` / `str` / `any` adapter と `py_enumerate_list_as<T>` も `src/runtime/cpp/built_in/iter_ops.ext.h` へ移し、`py_runtime.ext.h` から iterator helper 本体を除去した。第二波の残件は `py_contains` の pure Python 正本化と adapter 分離に絞られた。
- 2026-03-06: `src/pytra/built_in/contains.py` を追加し、`py_contains` の object 経路（`dict/list/set/str`）を `src/runtime/cpp/built_in/contains.gen.*` へ移した。typed `dict/list/set/str/tuple` fastpath と object dispatch は `src/runtime/cpp/built_in/contains.ext.h` へ分離し、`py_runtime.ext.h` から `py_contains` 本体を撤去した。
- 2026-03-06: `tools/unittest/common/test_pytra_built_in_{predicates,string_ops,contains}.py` を更新し、public 名で pure Python 正本の観測を固定した。`check_runtime_cpp_layout.py`, `check_runtime_std_sot_guard.py`, `verify_image_runtime_parity.py`, built_in/re の syntax-only compile は継続通過した。
