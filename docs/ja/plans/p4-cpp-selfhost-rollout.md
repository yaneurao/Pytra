# P4: C++ selfhost 復旧と常用導線の再有効化

最終更新: 2026-03-08

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P4-CPP-SELFHOST-ROLLOUT-01`

関連:
- [spec-dev.md](../spec/spec-dev.md)
- [spec-tools.md](../spec/spec-tools.md)
- [how-to-use.md](../how-to-use.md)
- [p0-py2x-dual-entrypoints-host-selfhost.md](./p0-py2x-dual-entrypoints-host-selfhost.md)
- [archive/20260308-p0-cpp-selfhost-any-compat-retirement.md](./archive/20260308-p0-cpp-selfhost-any-compat-retirement.md)
- [archive/20260308-p2-jsonvalue-selfhost-decode-alignment.md](./archive/20260308-p2-jsonvalue-selfhost-decode-alignment.md)

背景:
- C++ selfhost の検証導線自体は残っている。代表的には [tools/build_selfhost.py](../../tools/build_selfhost.py), [tools/check_selfhost_direct_compile.py](../../tools/check_selfhost_direct_compile.py), [tools/check_selfhost_cpp_diff.py](../../tools/check_selfhost_cpp_diff.py), [tools/verify_selfhost_end_to_end.py](../../tools/verify_selfhost_end_to_end.py) がある。
- しかし 2026-03-08 時点では `python3 tools/build_selfhost.py` が失敗する。生成された [selfhost/py2cpp.cpp](../../selfhost/py2cpp.cpp) が `runtime/cpp/generated/utils/backend_registry_static.h` と `runtime/cpp/generated/utils/transpile_cli.h` を include する一方、その C++ runtime artifact が存在しないためである。
- つまり現在の selfhost は「検証スクリプトはあるが stage1 build が壊れている」状態であり、日常導線としては利用できない。
- また selfhost には複数段階がある。
  - stage1: host Python で `src/py2x-selfhost.py` を C++ に変換して `selfhost/py2cpp.out` を作る
  - direct route: できた selfhost binary が `.py` を直接受けて C++ を出せる
  - diff/e2e: host 版出力と selfhost 版出力の差分、生成バイナリ挙動の parity を見る
  - stage2: selfhost binary 自身で `src/py2x-selfhost.py` を再変換して再ビルドする

目的:
- 壊れている stage1 build を復旧し、`tools/build_selfhost.py` を green に戻す。
- その上で direct `.py` route・diff・e2e・stage2 build を順に再有効化し、C++ selfhost を「実際に使える検証導線」へ戻す。
- 既存の host/selfhost entry split や linked-program 化以後の契約に合うよう、selfhost 専用 compat debt を必要最小限に抑える。

対象:
- `tools/build_selfhost.py`
- `tools/build_selfhost_stage2.py`
- `tools/check_selfhost_direct_compile.py`
- `tools/check_selfhost_cpp_diff.py`
- `tools/verify_selfhost_end_to_end.py`
- `src/py2x-selfhost.py`
- selfhost 生成 C++ が参照する C++ runtime / generated helper artifact

非対象:
- 非 C++ target の selfhost 復旧
- selfhost source の全面 Pythonic 化
- `py_runtime.h` の追加縮退
- `match` / `cast` / `JsonValue` の新言語機能設計

受け入れ基準:
- `python3 tools/build_selfhost.py` が成功し、`selfhost/py2cpp.out` を生成できる。
- `python3 tools/check_selfhost_direct_compile.py` が representative case で green になる。
- `python3 tools/check_selfhost_cpp_diff.py` が current contract に沿って pass する。
- `python3 tools/verify_selfhost_end_to_end.py --skip-build` が representative case で green になる。
- 可能なら `python3 tools/build_selfhost_stage2.py` も green にし、少なくとも stage2 build 失敗理由を既知 debt から外す。

確認コマンド:
- `python3 tools/build_selfhost.py`
- `python3 tools/check_selfhost_direct_compile.py`
- `python3 tools/check_selfhost_cpp_diff.py`
- `python3 tools/verify_selfhost_end_to_end.py --skip-build`
- `python3 tools/build_selfhost_stage2.py`

## 1. 基本方針

1. stage1 build を最優先に直す。selfhost binary が無い状態では、それ以降の direct route / diff / e2e / stage2 は議論しても進まない。
2. selfhost 生成 C++ が include する artifact は「その場しのぎの手書き shim」ではなく、host path と同じ source of truth から供給する。
3. direct `.py` route を bridge route の暫定代替でごまかさない。selfhost binary が `.py` を直接受ける current contract を復旧する。
4. diff / e2e は stage1 build 復旧後に順次戻す。build が壊れたまま expected diff をいじって通したことにしない。

## 2. フェーズ

### Phase 1: 失敗点の棚卸しと契約固定

- `tools/build_selfhost.py` 失敗点を棚卸しし、missing include / missing runtime artifact / compile error / link error に分類する。
- `src/py2x-selfhost.py` が現在参照する static frontend helper のうち、C++ selfhost が runtime artifact として必要なものを固定する。
- `build_selfhost.py` / `build_selfhost_stage2.py` / `check_selfhost_direct_compile.py` / `check_selfhost_cpp_diff.py` / `verify_selfhost_end_to_end.py` の受け入れ順序を決定ログへ固定する。

### Phase 2: stage1 build 復旧

- `selfhost/py2cpp.cpp` が参照する `backend_registry_static` / `transpile_cli` などの C++ runtime artifact を正規生成するか、selfhost source 側参照を current generated layout に揃える。
- `tools/build_selfhost.py` が runtime source の探索先や include path を current `generated/native/pytra/core` layout に合わせて build できるようにする。
- stage1 build を green に戻し、`selfhost/py2cpp.out` を再生成する。

### Phase 3: direct route / diff / e2e 復旧

- `tools/check_selfhost_direct_compile.py` を通し、selfhost binary が `.py` 入力から C++ を吐いて `-fsyntax-only` compile まで通る状態にする。
- `tools/check_selfhost_cpp_diff.py` を current contract に合わせて再基線化し、host vs selfhost の差分が既知 baseline に収まることを確認する。
- `tools/verify_selfhost_end_to_end.py --skip-build` を representative case で green に戻す。

### Phase 4: stage2 と運用固定

- `tools/build_selfhost_stage2.py` を回し、stage2 build を current layout / current selfhost entry に合わせて復旧する。
- `spec-tools` / `how-to-use` に selfhost 復旧後の正しい運用コマンドと failure triage を反映する。
- 必要なら `run_local_ci.py` への gate 戻しを検討する。

## 3. 着手時の注意

- selfhost は generated C++ と runtime layout の両方にまたがる。selfhost 側だけの ad-hoc include patch を入れると、host/selfhost divergence が増える。
- `tools/selfhost_transpile.py` は transitional bridge であり、direct `.py` route の未復旧を恒久化するために使わない。
- `runtime/cpp/generated/utils/backend_registry_static.h` のような include が出ているなら、どこが source of truth かを確認し、missing artifact を正規 lane へ出すか generated source の include path を直すかを先に決める。

## 4. タスク分解

- [ ] [ID: P4-CPP-SELFHOST-ROLLOUT-01] C++ selfhost の stage1 build / direct route / diff / stage2 を current runtime/layout 契約に合わせて復旧する。
- [x] [ID: P4-CPP-SELFHOST-ROLLOUT-01-S1-01] `tools/build_selfhost.py` 失敗点と missing artifact を棚卸しする。
- [x] [ID: P4-CPP-SELFHOST-ROLLOUT-01-S1-02] selfhost 復旧の受け入れ順序と current source of truth を決定ログへ固定する。
- [x] [ID: P4-CPP-SELFHOST-ROLLOUT-01-S2-01] stage1 build に必要な generated/static frontend artifact 供給を current layout に合わせて復旧する。
- [ ] [ID: P4-CPP-SELFHOST-ROLLOUT-01-S2-02] `tools/build_selfhost.py` を green に戻し、`selfhost/py2cpp.out` を再生成する。
- [ ] [ID: P4-CPP-SELFHOST-ROLLOUT-01-S3-01] direct `.py` route を復旧し、`tools/check_selfhost_direct_compile.py` を通す。
- [ ] [ID: P4-CPP-SELFHOST-ROLLOUT-01-S3-02] host/selfhost diff と representative e2e を green に戻す。
- [ ] [ID: P4-CPP-SELFHOST-ROLLOUT-01-S4-01] `tools/build_selfhost_stage2.py` を current contract に合わせて復旧する。
- [ ] [ID: P4-CPP-SELFHOST-ROLLOUT-01-S4-02] docs / archive / local CI gate 方針を更新して本計画を閉じる。

## 5. 決定ログ

- 2026-03-08: plan 起票時点では `python3 tools/build_selfhost.py` が `[selfhost/py2cpp.cpp:7] runtime/cpp/generated/utils/backend_registry_static.h not found` で失敗している。まず stage1 build を直し、その後に direct route / diff / e2e / stage2 を順に扱う。
- 2026-03-08: `python3 tools/build_selfhost.py` の current failure は 1 段目で `selfhost/py2cpp.cpp` が `runtime/cpp/generated/utils/backend_registry_static.h` と `runtime/cpp/generated/utils/transpile_cli.h` を include する一方、対応 artifact が repo 内に存在しない点で再現した。`rg --files src/runtime/cpp | rg 'backend_registry_static|transpile_cli'` でも runtime lane に該当 header は見つからない。
- 2026-03-08: build script 自体も current runtime layout に追随していない。`tools/build_selfhost.py` の `runtime_cpp_sources()` は `src/runtime/cpp/pytra/**/*.cpp` だけを列挙しており、current tree では 0 件だった。つまり stage1 build の blocker は「missing generated/static frontend artifact」と「compile source discovery が `generated/native/core` を見ていない」の二系統に分かれる。
- 2026-03-08: 受け入れ順序は `stage1 build artifact供給 -> build_selfhost.py green -> direct .py route -> host/selfhost diff + e2e -> stage2` に固定する。`tools/selfhost_transpile.py` の bridge route は temporary fallback であり、direct `.py` route の未復旧を正当化する用途には使わない。
- 2026-03-08: current source of truth は `src/py2x-selfhost.py` が import している `toolchain.compiler.backend_registry_static` と `toolchain.compiler.transpile_cli` の Python source であり、selfhost 側だけの ad-hoc hand-written shim は増やさない。必要なら current runtime generation lane へ `generated/utils/*` artifact を正式追加するか、selfhost source 側 import を current exported C++ surface へ寄せる。
- 2026-03-08: `toolchain.compiler.*` の selfhost runtime lane は `src/runtime/cpp/{generated,native,pytra}/compiler` に追加し、`runtime_paths.py` も `generated/compiler/*.h` を返すように揃えた。`build_selfhost.py` / `build_selfhost_stage2.py` / `verify_selfhost_end_to_end.py` の runtime source 解決は `collect_runtime_cpp_sources(...)` に一本化し、`check_runtime_cpp_layout.py` と build-graph test も `compiler` bucket を current layout として許可した。
