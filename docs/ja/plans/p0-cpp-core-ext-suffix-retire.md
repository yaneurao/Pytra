# P0: C++ core runtime の `.ext` suffix 退役（`core/*.h` + `native/core/*.{h,cpp}`）

最終更新: 2026-03-07

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-CORE-EXT-SUFFIX-RETIRE-01`
- 参照仕様: `docs/ja/spec/spec-runtime.md`
- 参照仕様: `docs/ja/spec/spec-abi.md`
- 先行整理: `docs/ja/plans/archive/20260307-p0-cpp-core-ownership-split.md`

背景:
- `P0-CPP-CORE-OWNERSHIP-SPLIT-01` により、`src/runtime/cpp/core/` は low-level runtime の stable include surface、`src/runtime/cpp/native/core/` は handwritten 正本、`src/runtime/cpp/generated/core/` は将来の generated lane として整理された。
- しかし file name は旧 layout の名残を引きずっており、`core/*.ext.h` は shim / forwarder なのに handwritten origin を示す `.ext` suffix を持っている。
- `native/core/*.ext.h` と `native/core/*.ext.cpp` も ownership は directory で十分に表現できているため、`.ext` suffix は重複情報であり、現状では「handwritten と generated が file suffix で混在している」ように見えるノイズになっている。
- この suffix は `std/built_in/utils` の directory-based ownership へ移行した現在の C++ runtime 設計と整合しておらず、特に `core/` surface では「forwarder なのに `.ext`」という名前の嘘を作っている。

目的:
- `src/runtime/cpp/core/` の stable include surface から `.ext` suffix を外し、shim/forwarder であることと plain public name を一致させる。
- `src/runtime/cpp/native/core/` の handwritten 正本からも `.ext` suffix を外し、ownership を directory で表す設計に揃える。
- 将来の `generated/core/` も plain file name 前提に揃え、core runtime だけ suffix-based naming を持ち越さないようにする。

対象:
- `src/runtime/cpp/core/*.ext.h -> *.h`
- `src/runtime/cpp/native/core/*.ext.h -> *.h`
- `src/runtime/cpp/native/core/*.ext.cpp -> *.cpp`
- `src/runtime/cpp/generated/core/` の naming rule
- C++ backend / generated runtime / tooling / docs / tests の core file path 参照
  - `src/backends/cpp/cli.py`
  - `src/backends/cpp/emitter/header_builder.py`
  - `src/backends/cpp/emitter/multifile_writer.py`
  - `tools/gen_runtime_symbol_index.py`
  - `tools/cpp_runtime_deps.py`
  - `tools/check_runtime_cpp_layout.py`
  - `tools/check_runtime_core_gen_markers.py`
  - core runtime 関連 unit/integration test

非対象:
- `pytra/core/` という新しい public include root の導入
- `std/built_in/utils` runtime の rename
- `generated/std` / `native/std` など module runtime の plain/suffix 再整理
- core helper の semantic change
- list ref-first TODO の実装

受け入れ基準:
- `src/runtime/cpp/core/` に残る public header は `*.h` のみで、`.ext.h` は 0 件になる。
- `src/runtime/cpp/native/core/` に残る handwritten 正本は `*.h` / `*.cpp` のみで、`.ext.h` / `.ext.cpp` は 0 件になる。
- backend / generated runtime / native companion / tests / docs / symbol index は `runtime/cpp/core/*.h` と `src/runtime/cpp/native/core/*.{h,cpp}` を参照し、旧 `.ext` path へ依存しない。
- `generated/core/` に real artifact が入る場合は plain naming を使い、core だけ suffix-based naming を再導入しない。
- representative verification が green で、`rg -n 'core/.*\\.ext|native/core/.*\\.ext' src test tools docs` は archive/history 以外で一致 0 件になる。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_runtime_cpp_layout.py`
- `python3 tools/check_runtime_core_gen_markers.py`
- `python3 tools/gen_runtime_symbol_index.py --check`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_runtime_symbol_index.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_cpp_runtime_build_graph.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_cpp_runtime_symbol_index_integration.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_cpp_runtime_iterable.py'`

## 先に固定する設計判断

### A. 目標レイアウト

```text
src/runtime/cpp/
  core/
    dict.h
    exceptions.h
    gc.h
    io.h
    list.h
    py_runtime.h
    py_scalar_types.h
    py_types.h
    set.h
    str.h
  native/
    core/
      dict.h
      exceptions.h
      gc.h
      gc.cpp
      io.h
      io.cpp
      list.h
      py_runtime.h
      py_scalar_types.h
      py_types.h
      set.h
      str.h
  generated/
    core/
      README.md
      # future generated files use plain naming only
```

### B. rename の基本方針

- `core/` は shim / forwarder なので plain name にする。
- `native/core/` は ownership を directory が表すので plain name にする。
- `generated/core/` も future artifact は plain name に限定する。
- `pytra/core` は導入しない。include root は `core/...` のままにする。

### C. compatibility の扱い

- この P0 では「最終状態を plain naming に切り替える」ことを優先し、旧 `.ext` path は最終的に repo から除去する。
- ただし implementation フェーズでは、一時的に tooling / backend へ fallback を入れて安全に rename してよい。
- closeout では fallback を削り、docs/test も plain naming を正本として固定する。

## 実装で迷いやすい点

### 1. `core/*.ext.h` を `core/*.h` にする理由

- `core/` は handwritten origin を表す場所ではなく、stable include surface である。
- したがって file suffix で ownership を表すべきではない。
- plain name にすることで、「public/stable name」と「forwarder/shim の役割」を一致させる。

### 2. `native/core/*.ext.*` も plain name にしてよい理由

- `native/core/` は handwritten ownership を directory で表している。
- `native/core/py_runtime.h` と `generated/core/py_runtime.h` は directory が異なるので basename collision は起きない。
- そのため `.ext` は識別に不要である。

### 3. `generated/core` は real artifact がなくても plain naming rule を先に固定する

- 既に `generated/core/README.md` は正式 lane として存在する。
- ここで naming rule も plain に固定しておけば、将来最初の generated core artifact を入れるときに `.ext` を再導入せずに済む。

### 4. `pytra/core` はこの計画に混ぜない

- include root の改名と file name suffix の整理は別問題である。
- 両方を同時にやると diff 範囲が広がり、失敗時の切り戻しと regression triage が難しくなる。
- まず `core/...` を保ったまま `.ext` を消し、その後必要なら別計画で `pytra/core` を検討する。

## フェーズ

### Phase 1: 現状棚卸しと命名契約の固定

- `core/*.ext.h` / `native/core/*.ext.{h,cpp}` の inventory を取り、rename map を作る。
- plain naming を採用する理由、`pytra/core` を同時にやらない理由、`generated/core` も plain naming に揃える方針を plan/spec へ固定する。

### Phase 2: tooling / index / deps の rename 耐性を先に入れる

- `runtime_symbol_index` / `cpp_runtime_deps.py` / `check_runtime_cpp_layout.py` / `check_runtime_core_gen_markers.py` を、移行中に `.ext` と plain name の両方を読める状態へ拡張する。
- representative synthetic test を足し、rename 途中でも compile/source 解決が壊れないことを確認する。

### Phase 3: `core/` public surface の rename

- `src/runtime/cpp/core/*.ext.h` を `*.h` へ rename し、forwarder 内容を同期する。
- backend / generated runtime / native companion / tests の include を `runtime/cpp/core/*.h` へ更新する。
- `core` surface は plain name のみ、`.ext.h` は 0 件にする。

### Phase 4: `native/core/` 正本の rename

- `src/runtime/cpp/native/core/*.ext.h` と `*.ext.cpp` を plain name へ rename する。
- `core` forwarder, native source, tooling, runtime symbol index, parity tool, docs, tests を新 path に同期する。
- representative compile source が `native/core/gc.cpp`, `native/core/io.cpp` などを返す状態へ揃える。

### Phase 5: generated/core naming 契約の固定と closeout

- `generated/core/README.md` と spec に「future generated core is plain-name only」を明記する。
- fallback / compatibility code を削除し、archive/docs/guard を更新して `.ext` naming が core runtime へ再侵入しない状態で完了扱いにする。

## Phase 1 実施結果

2026-03-07 時点の `core` / `native/core` inventory は次のとおり。

- `core/` public forwarder rename 対象: 10 files
  - `dict.ext.h -> dict.h`
  - `exceptions.ext.h -> exceptions.h`
  - `gc.ext.h -> gc.h`
  - `io.ext.h -> io.h`
  - `list.ext.h -> list.h`
  - `py_runtime.ext.h -> py_runtime.h`
  - `py_scalar_types.ext.h -> py_scalar_types.h`
  - `py_types.ext.h -> py_types.h`
  - `set.ext.h -> set.h`
  - `str.ext.h -> str.h`
- `native/core/` handwritten header rename 対象: 10 files
  - `dict.ext.h -> dict.h`
  - `exceptions.ext.h -> exceptions.h`
  - `gc.ext.h -> gc.h`
  - `io.ext.h -> io.h`
  - `list.ext.h -> list.h`
  - `py_runtime.ext.h -> py_runtime.h`
  - `py_scalar_types.ext.h -> py_scalar_types.h`
  - `py_types.ext.h -> py_types.h`
  - `set.ext.h -> set.h`
  - `str.ext.h -> str.h`
- `native/core/` handwritten source rename 対象: 2 files
  - `gc.ext.cpp -> gc.cpp`
  - `io.ext.cpp -> io.cpp`
- `generated/core/` 既存ファイル: 1 file
  - `README.md` のみ。real artifact はまだ 0 件で、plain naming rule だけが先行して存在する。

確認事項:

- `core/` 側で `.ext` を持っている tracked file は forwarder header 10 件のみで、`.cpp` 実体は残っていない。
- `native/core/` 側で `.ext` を持っている tracked file は handwritten 正本 header 10 件と source 2 件だけであり、rename 後の basename collision は起きない。
- `generated/core/` は既に plain naming side (`README.md`) で存在しているため、今後の real artifact も plain name に限定して問題ない。
- 現時点の rename 対象は low-level core lane に閉じており、`generated/std|built_in|utils` や `native/std|built_in` を同時に巻き込む必要はない。

## 分解

- [ ] [ID: P0-CPP-CORE-EXT-SUFFIX-RETIRE-01] C++ core runtime から `.ext` suffix を退役し、`core` surface / `native/core` 正本 / `generated/core` lane を plain file name 契約へ揃える。

- [x] [ID: P0-CPP-CORE-EXT-SUFFIX-RETIRE-01-S1-01] `core/*.ext.h` と `native/core/*.ext.{h,cpp}` の rename inventory を作り、plain name 対応表を決定ログへ固定する。
- [ ] [ID: P0-CPP-CORE-EXT-SUFFIX-RETIRE-01-S1-02] `core` は shim、`native/core` は ownership 正本、`generated/core` は plain naming future lane とする命名契約を plan/spec に固定する。

- [ ] [ID: P0-CPP-CORE-EXT-SUFFIX-RETIRE-01-S2-01] `runtime_symbol_index` / `cpp_runtime_deps.py` / layout guard を rename 耐性ありの導線へ拡張し、移行中でも source/header 解決が通るようにする。
- [ ] [ID: P0-CPP-CORE-EXT-SUFFIX-RETIRE-01-S2-02] synthetic test を追加し、`core/*.h` + `native/core/*.{h,cpp}` の plain naming で compile/source 解決できることを固定する。

- [ ] [ID: P0-CPP-CORE-EXT-SUFFIX-RETIRE-01-S3-01] `src/runtime/cpp/core/*.ext.h` を `*.h` へ rename し、forwarder surface を plain name へ切り替える。
- [ ] [ID: P0-CPP-CORE-EXT-SUFFIX-RETIRE-01-S3-02] backend / generated runtime / native companion / tests の include を `runtime/cpp/core/*.h` へ更新し、`runtime/cpp/core/*.ext.h` 依存を除去する。

- [ ] [ID: P0-CPP-CORE-EXT-SUFFIX-RETIRE-01-S4-01] `src/runtime/cpp/native/core/*.ext.h` / `*.ext.cpp` を plain name へ rename し、public forwarder と compile source の参照先を同期する。
- [ ] [ID: P0-CPP-CORE-EXT-SUFFIX-RETIRE-01-S4-02] runtime symbol index / parity tool / representative tests を plain `native/core/*.{h,cpp}` 前提へ更新し、旧 `.ext` path を返さないことを固定する。

- [ ] [ID: P0-CPP-CORE-EXT-SUFFIX-RETIRE-01-S5-01] `generated/core` の plain naming rule を README/spec/guard に固定し、future artifact が `.ext` を再導入しないようにする。
- [ ] [ID: P0-CPP-CORE-EXT-SUFFIX-RETIRE-01-S5-02] fallback / docs / archive / guard を更新し、core runtime の `.ext` naming を完了扱いで閉じる。

決定ログ:
- 2026-03-07: ユーザー指示により、`core` surface は shim なので `.ext` を外し、`native/core` も directory で ownership が表現できる以上 `.ext` は不要と判断した。
- 2026-03-07: `pytra/core` への include-root 移行は rename と独立した大きな変更なので、この計画には含めない。まず `core/...` を維持したまま file name を plain に揃える。
- 2026-03-07: `S1-01` として rename inventory を固定した。対象は `core/` forwarder header 10 件、`native/core/` handwritten header 10 件、`native/core/` source 2 件で、`generated/core/` は `README.md` のみだった。basename collision はなく、Phase 3 と Phase 4 で `core` surface と `native/core` 正本を段階分離できることを確認した。
