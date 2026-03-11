# P5 Backend Feature Parity Contract

最終更新: 2026-03-12

目的:
- C++ を事実上の仕様実装として扱う状態をやめ、syntax / builtins / `pytra.std.*` の共通 feature contract を backend 横断で固定する。
- backend 未対応 feature が silent fallback や ad-hoc degrade に流れず、必ず fail-closed する運用を確立する。
- 後段の conformance suite / support matrix / rollout policy の正本となる feature inventory を作る。

背景:
- 現在の Pytra は representative lane として C++ が先行しやすく、同じ feature でも Rust / C# / 他 backend の扱いが uneven になりやすい。
- `py_runtime.h` の縮小を急ぐ都合上、直近は C++ / runtime 契約整理が優先されるが、その後ろで backend parity の基準を制度として固める必要がある。
- parity を「後で追いつく作業」として扱うと、C++ だけ実装済み・他 backend は object/String fallback という drift が再発する。
- 先に feature ID、support contract、fail-closed rule を固定しておけば、各 backend の進捗差があっても仕様と品質評価の基準は揃えられる。

非対象:
- すべての backend へ即時に同じ feature を実装すること。
- `pytra.std.*` の全面 rewrite。
- `py_runtime.h` の即時削減作業。
- 各 backend の runtime 実装詳細の最終整理。

受け入れ基準:
- syntax / builtins / `pytra.std.*` を feature ID 単位で inventory 化する plan が定義されている。
- `supported` / `fail_closed` / `not_started` / `experimental` など backend support state の分類が固定されている。
- 未対応 backend は silent fallback ではなく `unsupported_syntax` / `not_implemented` 系で止める方針が明文化されている。
- 新 feature を merge する際の acceptance rule（C++ だけで完了扱いにしない条件）が決まっている。
- `docs/en/` mirror が日本語版と同じ内容に追従している。

## 子タスク

- [x] [ID: P5-BACKEND-FEATURE-PARITY-CONTRACT-01-S1-01] syntax / builtins / `pytra.std.*` の representative feature を feature ID 単位で棚卸しし、inventory の category と naming rule を固定する。
- [x] [ID: P5-BACKEND-FEATURE-PARITY-CONTRACT-01-S1-02] backend support state（`supported` / `fail_closed` / `not_started` / `experimental`）と、その判定条件を decision log に固定する。
- [x] [ID: P5-BACKEND-FEATURE-PARITY-CONTRACT-01-S2-01] backend 未対応 feature の fail-closed policy と diagnostic category を整理し、silent fallback 禁止 rule を明文化する。
- [x] [ID: P5-BACKEND-FEATURE-PARITY-CONTRACT-01-S2-02] 新 feature 導入時の acceptance rule を決め、`C++ だけ通れば完了` としない運用を定義する。
- [ ] [ID: P5-BACKEND-FEATURE-PARITY-CONTRACT-01-S3-01] representative inventory document / tooling / docs handoff を整え、後段 conformance suite と support matrix へ接続する。

## S1-01 Representative Inventory

- source of truth: [backend_feature_contract_inventory.py](/workspace/Pytra/src/toolchain/compiler/backend_feature_contract_inventory.py)
- validation: [check_backend_feature_contract_inventory.py](/workspace/Pytra/tools/check_backend_feature_contract_inventory.py), [test_check_backend_feature_contract_inventory.py](/workspace/Pytra/test/unit/tooling/test_check_backend_feature_contract_inventory.py)
- category rule:
  - `syntax`: `syntax.<area>.<feature>`
  - `builtin`: `builtin.<domain>.<feature>`
  - `stdlib`: `stdlib.<module>.<feature>`
- representative inventory は exhaustive 一覧ではなく、後段の conformance suite / support matrix が寄り掛かる representative feature set として固定する。
- `syntax` representative:
  - `syntax.assign.tuple_destructure`
  - `syntax.expr.lambda`
  - `syntax.expr.list_comprehension`
  - `syntax.control.for_range`
  - `syntax.control.try_raise`
  - `syntax.oop.virtual_dispatch`
- `builtin` representative:
  - `builtin.iter.range`
  - `builtin.iter.enumerate`
  - `builtin.iter.zip`
  - `builtin.type.isinstance`
  - `builtin.bit.invert_and_mask`
- `stdlib` representative:
  - `stdlib.json.loads_dumps`
  - `stdlib.pathlib.path_ops`
  - `stdlib.enum.enum_and_intflag`
  - `stdlib.argparse.parse_args`
  - `stdlib.math.imported_symbols`
  - `stdlib.re.sub`

## S1-02 Support-state Taxonomy

- source of truth: [backend_feature_contract_inventory.py](/workspace/Pytra/src/toolchain/compiler/backend_feature_contract_inventory.py)
- validation: [check_backend_feature_contract_inventory.py](/workspace/Pytra/tools/check_backend_feature_contract_inventory.py), [test_check_backend_feature_contract_inventory.py](/workspace/Pytra/test/unit/tooling/test_check_backend_feature_contract_inventory.py)
- support states:
  - `supported`: representative fixture / regression lane が preview caveat なしで通る。
  - `fail_closed`: feature は未実装でも、silent fallback せず `unsupported_syntax` / `not_implemented` 系で止まる。
  - `not_started`: representative 実装も fail-closed lane もまだ無く、parity summary で support を主張しない。
  - `experimental`: preview-only / opt-in lane はあるが、stable support としては扱わない。

## S2-01 Fail-closed Policy

- source of truth: [backend_feature_contract_inventory.py](/workspace/Pytra/src/toolchain/compiler/backend_feature_contract_inventory.py)
- diagnostics vocabulary anchor: [backend_registry_diagnostics.py](/workspace/Pytra/src/toolchain/compiler/backend_registry_diagnostics.py)
- accepted fail-closed detail categories:
  - `not_implemented`
  - `unsupported_by_design`
  - `preview_only`
  - `blocked`
- forbidden silent fallback labels:
  - `object_fallback`
  - `string_fallback`
  - `comment_stub_fallback`
  - `empty_output_fallback`
- phase rules:
  - `parse_and_ir`: unsupported syntax / frontend lane は emit 前に停止する。
  - `emit_and_runtime`: unsupported backend lane は known-block diagnostic で止まり、汎用 object/String/comment 出力へ落とさない。
  - `preview_rollout`: preview-only lane は `experimental` から昇格するまで `supported` 扱いしない。

## S2-02 New-feature Acceptance Rule

- source of truth: [backend_feature_contract_inventory.py](/workspace/Pytra/src/toolchain/compiler/backend_feature_contract_inventory.py)
- validation: [check_backend_feature_contract_inventory.py](/workspace/Pytra/tools/check_backend_feature_contract_inventory.py), [test_check_backend_feature_contract_inventory.py](/workspace/Pytra/test/unit/tooling/test_check_backend_feature_contract_inventory.py)
- fixed acceptance rules:
  - `feature_id_required`: 新 feature は representative scope 外と明示しない限り feature ID を持つ。
  - `inventory_or_followup_required`: representative fixture entry か parity follow-up task のどちらかを merge 前に持つ。
  - `cxx_only_not_complete`: C++ support 単独では feature contract を閉じない。
  - `noncpp_state_required`: merge 時点で少なくとも 1 つの non-C++ backend state を記録する。
  - `unsupported_lanes_fail_closed`: `supported` 以外の lane は `fail_closed` / `not_started` / `experimental` のいずれかで、silent fallback を使わない。
  - `docs_mirror_required`: parity contract 更新時は `docs/en` mirror を同時更新する。

## 決定ログ

- 2026-03-12: backend parity は重要だが、直近の `py_runtime.h` shrink 系 `P0-P4` を止めるべきではないため `P5` に置く。
- 2026-03-12: parity の正本は C++ 実装ではなく feature contract / EAST3 contract / `pytra.std.*` 契約とする。
- 2026-03-12: `S1-01` の representative inventory 正本は [backend_feature_contract_inventory.py](/workspace/Pytra/src/toolchain/compiler/backend_feature_contract_inventory.py) に置き、category は `syntax` / `builtin` / `stdlib` の 3 系統に固定する。
- 2026-03-12: `S1-02` では backend support state を `supported` / `fail_closed` / `not_started` / `experimental` の 4 つへ固定し、`fail_closed` を parity summary 上の正式 state として扱う。
- 2026-03-12: `S2-01` では unsupported backend lane の diagnostic category を `not_implemented` / `unsupported_by_design` / `preview_only` / `blocked` に固定し、`object/String/comment/empty-output` fallback を parity contract 上の forbidden silent fallback とする。
- 2026-03-12: `S2-02` では feature merge acceptance rule を固定し、C++ lane が通っても non-C++ state と docs mirror が揃うまでは feature-complete とみなさない。
