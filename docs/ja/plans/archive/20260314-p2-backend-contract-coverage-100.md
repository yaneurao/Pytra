<a href="../../../en/plans/archive/20260314-p2-backend-contract-coverage-100.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P2: backend 契約カバレッジ 100% を bundle-based coverage で固定する

最終更新: 2026-03-14

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P2-BACKEND-CONTRACT-COVERAGE-100-01`

背景:
- 現行の `docs/ja/language/backend-parity-matrix.md` は representative feature の support state を公開する canonical support matrix であり、全 test suite の総覧ではない。
- support matrix の row は `feature_id + representative_fixture` の curated inventory に固定されている一方、`test/unit/backends/*` では `property_method_call` や `list_bool_index` のように多 backend で既に見ている fixture があり、coverage の実態と docs の見え方がずれている。
- `test/ir` は EAST3(JSON) 起点の backend-only smoke、`test/integration` は backend-specific integration suite、`test/transpile` は artifact 比較系の fixture 群だが、これらは parity matrix の row taxonomy に直接接続されていない。
- その結果、「どの feature/lane/backend がどの大きな test bundle で検証されているか」「未掲載だが既に見ている fixture は何か」「coverage がどこまで 100% か」が docs と tooling から即答できない。

目的:
- support matrix は `feature x backend support-state` の canonical claim として維持しつつ、別に bundle-based coverage matrix / inventory を導入して verification coverage を可視化する。
- coverage 100% を line/branch coverage ではなく、`feature x required_lane x backend` が必ず 1 つ以上の coverage bundle に所属する contract coverage として定義する。
- `test/unit` / `test/ir` / `test/integration` / `test/transpile` を bundle taxonomy に接続し、「未掲載だけど実はテスト済み」の状態を減らす。

対象:
- `backend_feature_contract_inventory.py` と `backend_conformance_inventory.py` にある representative feature / lane contract
- `docs/ja|en/language/backend-parity-matrix.md` と将来の coverage docs/export
- `test/unit/common` / `test/unit/backends` / `test/ir` / `test/integration` / `test/transpile`
- coverage bundle taxonomy、manifest、checker、export tool、mirror docs
- representative inventory に未昇格だが multi-backend で既に見ている fixture の棚卸し

非対象:
- 各 backend の実装機能そのものを一気に full support にすること
- Python 行カバレッジや branch coverage を 100% にすること
- 既存 support-state taxonomy（`supported` / `fail_closed` / `not_started` / `experimental`）の redesign
- backend-specific integration suite を cross-backend support claim と混同すること

受け入れ基準:
- support matrix と coverage matrix の役割分担が docs / tooling contract 上で明文化されている。
- `feature_id x required_lane x backend` の contract coverage について、各 cell が少なくとも 1 つの coverage bundle、または explicit な non-applicable / backend-specific lane rule に紐付く。
- coverage bundle taxonomy が最低限 `frontend`, `emit`, `runtime`, `import_package`, `ir2lang`, `integration` 相当の責務分割を持ち、各 bundle が source suite / harness / evidence lane を持つ。
- `test/unit`, `test/ir`, `test/integration`, `test/transpile` の live suite が coverage taxonomy へ接続されるか、意図的な非対象として明示される。
- `property_method_call` や `list_bool_index` のような multi-backend smoke fixture は、support matrix へ昇格するか、coverage-only representative として inventory に現れる。
- 新規 feature や suite を追加した際、coverage bundle 未接続の `feature/lane/backend` を checker が fail させる。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `rg -n "property_method_call|list_bool_index|test/ir|test/integration|test/transpile|support matrix|coverage matrix" src tools test docs -g '!**/archive/**'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_backend_*coverage*.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends -p 'test_py2*_smoke.py'`
- `python3 tools/check_ir2lang_smoke.py`
- `git diff --check`

## Coverage Bundle 方針

- `support_matrix`: representative feature の support claim を公開する。support state を答える面であり、suite inventory の全件一覧は持たない。
- `coverage_matrix`: verification coverage を公開する。各 `feature x lane x backend` がどの bundle で検証されるかを示す。
- `frontend` bundle: parse / east / east3_lowering を担当する。
- `emit` bundle: backend emitter の source generation smoke / compare を担当する。
- `runtime` bundle: representative runtime parity と stdlib runtime strategy を担当する。
- `import_package` bundle: relative import / package layout / multi-file ownership を担当する。
- `ir2lang` bundle: `test/ir` を起点に frontend 非依存で backend-only smoke を担当する。
- `integration` bundle: `test/integration` など backend-specific execution / GC / linker 連携を担当する。

## 100% の定義

- 100% は `feature x required_lane x backend` の contract coverage であり、行カバレッジや branch coverage ではない。
- `required_lane` は conformance inventory の lane policy から引く。
- 各 coverage cell には `bundle_id`, `suite_kind`, `harness_kind`, `evidence_ref` のいずれかが固定される。
- support claim が `supported` でなくても、coverage claim は `fail_closed` / `not_started` / `experimental` の検証 bundle を持てる。
- backend-specific integration は support matrix に混ぜず、coverage matrix 上で `backend_specific` lane として扱う。

## 分解

- [x] [ID: P2-BACKEND-CONTRACT-COVERAGE-100-01-S1-01] 既存 representative inventory と `test/unit` / `test/ir` / `test/integration` / `test/transpile` の live suite を棚卸しし、coverage bundle 候補を分類する。
- [x] [ID: P2-BACKEND-CONTRACT-COVERAGE-100-01-S1-02] support matrix と coverage matrix の役割分担、および contract coverage 100% の定義を docs / tooling contract に固定する。
- [x] [ID: P2-BACKEND-CONTRACT-COVERAGE-100-01-S2-01] coverage bundle taxonomy と machine-readable manifest/checker を導入し、`feature x lane x backend` の bundle 所属を検証可能にする。
- [x] [ID: P2-BACKEND-CONTRACT-COVERAGE-100-01-S2-02] `test/unit`, `test/ir`, `test/integration`, `test/transpile` を coverage bundle へ接続し、未接続 suite を明示的に洗い出す。
- [x] [ID: P2-BACKEND-CONTRACT-COVERAGE-100-01-S2-03] multi-backend で既に使われている未掲載 fixture を、support-matrix 昇格候補と coverage-only representative に仕分ける。
- [x] [ID: P2-BACKEND-CONTRACT-COVERAGE-100-01-S3-01] docs/export/checker/English mirror を同期し、新規 feature/suite の coverage 漏れを fail-fast にする。

決定ログ:
- 2026-03-14: `backend-parity-matrix` が representative support claim であって suite inventory ではないことを確認し、bundle-based coverage matrix を別建てして contract coverage 100% を定義する P2 task として起票した。
- 2026-03-14: `backend_contract_coverage_inventory.py` / checker / unit test を追加し、representative inventory seed、coverage bundle taxonomy、live suite family inventory、未掲載 multi-backend fixture seed（`property_method_call`, `list_bool_index`）を first-pass の machine-readable inventory として固定した。`test/unit/link|selfhost|tooling` は supporting-only、`test/unit/common|backends|ir`, `test/ir`, `test/integration`, `test/transpile` は direct matrix input 候補として分類する。
- 2026-03-14: `backend_contract_coverage_contract.py` / checker / unit test を追加し、support matrix / future coverage matrix / backend test matrix の役割分担と `feature x required_lane x backend` contract coverage 100% の定義を tooling contract に固定した。`docs/ja|en/language/backend-parity-matrix.md` と `backend-test-matrix.md` にも同じ wording を入れ、suite health と contract coverage を混同しない状態を doc needle で検証する。
- 2026-03-14: `backend_contract_coverage_matrix_contract.py` / checker / unit test を追加し、representative feature の `required_lane x backend` seed ownership を machine-readable に固定した。`parse/east/east3_lowering/emit` は bundle owner、`runtime` は `case_runtime_followup` / `module_runtime_strategy_followup` rule として seed 化し、bundle 未接続 lane を explicit rule 付きで可視化する。
- 2026-03-14: `backend_contract_coverage_suite_attachment_contract.py` / checker / unit test を追加し、live suite family ごとの bundle attachment / explicit exclusion を machine-readable に固定した。`unit_common`, `unit_backends`, `unit_ir`, `ir_fixture`, `integration`, `transpile_artifact` は direct bundle attachment、`unit_link`, `unit_selfhost`, `unit_tooling` は supporting-only exclusion reason を必須にして、未接続 suite を checker で可視化する。
- 2026-03-14: unpublished multi-backend fixture inventory に `target_surface` と `status -> target_surface` invariant を追加し、`property_method_call` は `support_matrix_promotion_candidate`、`list_bool_index` は `coverage_matrix_only` 維持の `coverage_only_representative` として固定した。これにより、support matrix へ昇格させる候補と coverage matrix 専用の回帰 fixture を machine-readable seed の段階で区別できるようにした。
- 2026-03-14: `backend-coverage-matrix.md` の ja/en live surface、`export_backend_contract_coverage_docs.py`、`backend_contract_coverage_handoff_contract.py` / checker / unit test を追加し、coverage bundle taxonomy / suite attachment / required-lane seed ownership / unpublished fixture classification を exporter 管理の docs surface に同期した。support/test docs から coverage page へのリンクも固定し、coverage docs drift を checker で fail-fast にした。
