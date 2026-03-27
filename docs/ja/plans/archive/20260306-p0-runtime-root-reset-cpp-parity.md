<a href="../../../en/plans/archive/20260306-p0-runtime-root-reset-cpp-parity.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: runtime ルート再編（`runtime2` 退避 + 新 `runtime/` 再構築）と C++ parity 復旧

最終更新: 2026-03-05

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-RUNTIME-ROOT-RESET-CPP-01`
- 2026-03-14: `P2-CPP-LEGACY-CORE-COMPAT-RETIRE-01` で stale-complete live plan から archive へ移管。

背景:
- ABI 境界を固定する前に runtime 実装を進めた結果、責務境界違反（emitter 側への実装漏れ）が再発してきた。
- 現行の `src/runtime/<lang>/pytra/`, `pytra-core/`, `pytra-gen/` の3層は責務が曖昧で、`pytra/` は実質 shim のみで保守負債になっている。
- `docs/ja/spec/spec-abi.md` で、runtime は `core/`（手書き）+ `gen/`（SoT 生成）の2層に整理する方針を固定した。
- 大規模移行の安全性を優先し、既存 tree を `src/runtime2/` に退避してから、新 `src/runtime/` を段階的に再構築する。
- まずは C++ の `test` / `sample` parity を復旧し、移行方式を確定してから他言語へ展開する。

目的:
- 既存 runtime を退避し、新レイアウトの `src/runtime/` をクリーンに構築する。
- C++ runtime を `src/runtime/cpp/core` + `src/runtime/cpp/gen` に限定し、`pytra` shim を廃止する。
- C++ の fixture/sample parity（artifact size + CRC32 含む）を通過させる。

対象:
- `src/runtime`（rename + 再構築）
- `src/backends/cpp/*` の runtime パス参照
- `src/toolchain/compiler/*` の C++ runtime 参照/コピー導線
- `tools/gen_runtime_from_manifest.py` / `tools/runtime_generation_manifest.json`（C++向け）
- parity 実行導線（`tools/runtime_parity_check.py`）
- 関連ドキュメント（`docs/ja/spec/*` の runtime パス記述）

非対象:
- 非C++ backend の runtime 移行
- runtime API の機能追加
- 実行速度改善（最適化）

受け入れ基準:
- `src/runtime2/` に旧 runtime が退避され、新規実装は `src/runtime/` のみを参照する。
- `src/runtime/cpp/` 配下は `core/` と `gen/` のみで、`pytra/` shim は存在しない。
- C++ の runtime 参照が `runtime/cpp/core` と `runtime/cpp/gen` に統一され、`runtime/cpp/pytra` 参照が消える。
- `tools/runtime_parity_check.py --targets cpp --case-root fixture` が通る。
- `tools/runtime_parity_check.py --targets cpp --case-root sample --all-samples` が通る。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `rg -n "runtime/cpp/pytra|src/runtime2" src/backends/cpp src/toolchain tools`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root sample --all-samples`

## 分解

- [x] [ID: P0-RUNTIME-ROOT-RESET-CPP-01-S1-01] C++ runtime 参照点（backend/toolchain/tools）を棚卸しし、`runtime/cpp/{core,gen}` へ移行する影響範囲を固定する。
- [x] [ID: P0-RUNTIME-ROOT-RESET-CPP-01-S1-02] `src/runtime` を `src/runtime2` へ `git mv` し、新規 `src/runtime/cpp/{core,gen}` を作成する。
- [x] [ID: P0-RUNTIME-ROOT-RESET-CPP-01-S1-03] `src/runtime2` 参照禁止ガード（CI/静的チェック）を追加し、新実装が旧treeへ依存しないことを強制する。
- [x] [ID: P0-RUNTIME-ROOT-RESET-CPP-01-S2-01] C++ backend の include/runtime 解決パスを `core/gen` 前提へ更新し、`pytra` shim 経路を削除する。
- [x] [ID: P0-RUNTIME-ROOT-RESET-CPP-01-S2-02] runtime generator（manifest/出力先/marker）を `runtime/cpp/gen` へ切り替える。
- [x] [ID: P0-RUNTIME-ROOT-RESET-CPP-01-S2-03] C++ build manifest/コピー導線を `runtime/cpp/core` + `runtime/cpp/gen` のみに統一する。
- [x] [ID: P0-RUNTIME-ROOT-RESET-CPP-01-S3-01] C++ 必要 runtime（std/utils）を SoT から再生成し、`gen/` のみへ配置する。
- [x] [ID: P0-RUNTIME-ROOT-RESET-CPP-01-S3-02] C++ 固有手書き実装（`*-impl.*`）を `core/` へ整理し、責務境界を固定する。
- [x] [ID: P0-RUNTIME-ROOT-RESET-CPP-01-S4-01] C++ fixture parity を通過させる（stdout + artifact size/CRC32）。
- [x] [ID: P0-RUNTIME-ROOT-RESET-CPP-01-S4-02] C++ sample parity（`--all-samples`）を通過させる（stdout + artifact size/CRC32）。
- [x] [ID: P0-RUNTIME-ROOT-RESET-CPP-01-S4-03] parity fail の原因を潰し切り、再実行で安定通過を確認する。
- [x] [ID: P0-RUNTIME-ROOT-RESET-CPP-01-S5-01] runtime レイアウト変更を `docs/ja/spec` に反映し、運用手順（生成/検証）を更新する。

決定ログ:
- 2026-03-05: ユーザー指示により、後方互換を捨てて `src/runtime -> src/runtime2` 退避後に新 `src/runtime` を構築する方針を採用。
- 2026-03-05: 初期スコープは C++ の parity 復旧までに限定し、他言語展開は C++ 完了後に別 ID で段階化する。
- 2026-03-05: [ID: `P0-RUNTIME-ROOT-RESET-CPP-01-S1-01`] 参照棚卸しを実施し、`work/logs/p0_runtime_root_reset_cpp_ref_inventory_targets_20260305_s1_01.txt`（50件）を固定した。影響範囲は `src/backends/cpp/*`, `src/toolchain/compiler/*`, `tools/*` に集中し、移行順序を「(1) emitter/cli include-path, (2) toolchain copy/build manifest, (3) tools 監査/検証スクリプト」に確定。
- 2026-03-05: [ID: `P0-RUNTIME-ROOT-RESET-CPP-01-S1-02`] `git mv src/runtime src/runtime2` を実施し、新規 `src/runtime/cpp/` を作成。C++ runtime の本体を `src/runtime/cpp/core`（旧 `pytra-core`）/`src/runtime/cpp/gen`（旧 `pytra-gen`）へ移動し、旧 shim（旧 `pytra`）は `src/runtime2/cpp/pytra` 側へ隔離した。
- 2026-03-05: [ID: `P0-RUNTIME-ROOT-RESET-CPP-01-S1-03`] `tools/check_runtime2_references_absent.py` と unit test（`test_check_runtime2_references_absent.py`）を追加し、`tools/run_local_ci.py` に組み込んだ。`src/runtime2` 参照の再流入を CI で fail-fast 化。
- 2026-03-05: [ID: `P0-RUNTIME-ROOT-RESET-CPP-01-S2-01`] C++ backend の include 解決を `runtime/cpp/core` + `runtime/cpp/gen` 前提へ更新。`cpp/cli.py`・`emitter/{runtime_paths,module,multifile_writer,header_builder}.py` の `runtime/cpp/pytra*` 参照を撤去し、`sample/py/01_mandelbrot.py` の再変換で include が `core/gen` 経路へ切り替わることを確認。
- 2026-03-05: [ID: `P0-RUNTIME-ROOT-RESET-CPP-01-S2-02`] runtime manifest の C++ 出力先を `src/runtime/cpp/gen/...` に更新し、`tools/gen_runtime_from_manifest.py --targets cpp --items utils/png,utils/gif` で再生成して `pytra-gen` 経路の再作成を防止。
- 2026-03-05: [ID: `P0-RUNTIME-ROOT-RESET-CPP-01-S2-03`] `tools/gen_makefile_from_manifest.py` / `tools/build_multi_cpp.py` / `tools/verify_sample_outputs.py` / `tools/verify_image_runtime_parity.py` を `runtime/cpp/{core,gen}` 前提へ更新。さらに `src/runtime/cpp/{core,gen}` 内 include を新パスへ正規化し、`python3 src/pytra-cli.py sample/py/01_mandelbrot.py --target cpp --build --output-dir out/p0_s203_build` で `core+gen` のみを用いたビルド通過を確認。
- 2026-03-05: [ID: `P0-RUNTIME-ROOT-RESET-CPP-01-S3-01`] `Path` の import/module-attr 解決（`os.path`, `sys.stdout/stderr`）を `CodeEmitter/CppCallEmitter` で補強し、`runtime/cpp/gen/std/{os,pathlib,sys,json}.cpp` と `gen/built_in/type_id.cpp` を SoT から再生成した。
- 2026-03-05: [ID: `P0-RUNTIME-ROOT-RESET-CPP-01-S4-01`] `tools/runtime_parity_check.py --targets cpp --case-root fixture --summary-json work/logs/p0_runtime_root_reset_cpp_fixture_20260305_s401.json` を通過（`math_extended/pathlib_extended/inheritance_virtual_dispatch_multilang` = 3/3）。
- 2026-03-05: [ID: `P0-RUNTIME-ROOT-RESET-CPP-01-S4-02`] sample parity をケース分割で再実行し、`01-05,07-13,15,17,18` は一致。`06_julia_parameter_sweep`・`14_raymarching_light_cycle`・`16_glass_sculpture_chaos` で GIF artifact CRC32 mismatch が残ることを固定した。
- 2026-03-05: [ID: `P0-RUNTIME-ROOT-RESET-CPP-01-S4-03`] GIF mismatch 3件の共通要因を `math.pi/e` の未初期化参照（`__pytra_module_init` 未呼び出し）と特定し、`src/runtime/cpp/gen/std/math.cpp` の `pi/e` を宣言時初期化へ変更。`tools/runtime_parity_check.py --targets cpp --case-root sample 06_julia_parameter_sweep 14_raymarching_light_cycle 16_glass_sculpture_chaos` を再実行して 3/3 pass を確認。
- 2026-03-05: [ID: `P0-RUNTIME-ROOT-RESET-CPP-01-S3-01`] `src/pytra/std/*`・`src/pytra/utils/*`・`src/pytra/built_in/type_id.py`・`src/toolchain/compiler/east_parts/core.py` を `--emit-runtime-cpp` で再生成し、`src/runtime/cpp/gen/*.cpp` のみが更新されることを確認した。あわせて `CppEmitter` に runtime module 用の静的 `__pytra_module_init` 呼び出しを追加して、再生成後も `math.pi/e` 初期化差分が再発しない形へ固定した。
- 2026-03-05: [ID: `P0-RUNTIME-ROOT-RESET-CPP-01-S3-02`] `tools/check_runtime_cpp_layout.py` と `tools/check_runtime_std_sot_guard.py` を `runtime/cpp/{core,gen}` 前提へ更新し、旧 `pytra-core/pytra-gen/pytra` forwarder 仮定を撤去した。`check_runtime_cpp_layout.py` / `check_runtime_std_sot_guard.py` / `check_runtime_core_gen_markers.py` を通過。
- 2026-03-05: [ID: `P0-RUNTIME-ROOT-RESET-CPP-01-S5-01`] `docs/ja/spec/spec-runtime.md` を `runtime/cpp/{core,gen}` 前提へ更新し、SoT再生成（`--emit-runtime-cpp`）と guard/parity 検証コマンド、`src/runtime/cpp/pytra` 再導入禁止を運用手順として明文化した。
