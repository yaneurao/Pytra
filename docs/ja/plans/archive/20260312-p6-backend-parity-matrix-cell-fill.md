<a href="../../../en/plans/archive/20260312-p6-backend-parity-matrix-cell-fill.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P6: backend parity matrix cell fill

最終更新: 2026-03-12

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P6-BACKEND-PARITY-MATRIX-CELL-FILL-01`

背景:
- 現在の backend parity matrix には canonical publish target と tooling contract がある。
- ただし現状の matrix は `feature_id / category / representative_fixture / backend_order / support_state_order` を row seed として持つだけで、各 `feature × backend` cell の support state をまだ埋めていない。
- 一方、C++ だけは [spec-support.md](/workspace/Pytra/docs/ja/language/cpp/spec-support.md) という詳細表があり、backend ごとの見え方が不均衡になっている。
- multi-backend compiler としては、C++ 専用の詳細表より先に、全 backend を横断する canonical 2 次元表を正本化する必要がある。

目的:
- `docs/ja/language/backend-parity-matrix.md` を、実際の `feature × backend` support state を持つ canonical matrix にする。
- 各 cell を `supported / fail_closed / not_started / experimental` のいずれかで埋め、state の根拠を tooling manifest から export できるようにする。
- C++ 個別 matrix は drill-down として残しつつ、全体の正本は cross-backend matrix に移す。

対象:
- parity matrix contract の cell schema 追加
- representative feature row ごとの backend state seed の整備
- state ごとの evidence / fixture / diagnostic handoff の export
- docs publish target の table 実体化
- representative lane から順に matrix を埋めるための rollout order 固定

非対象:
- 全 backend の full feature parity を同時に達成すること
- per-backend 詳細 docs の廃止
- representative feature inventory 自体の全面作り直し
- support state taxonomy の再設計

受け入れ基準:
- parity matrix contract が per-cell state を持つこと。
- docs publish target が row seed だけでなく `feature × backend` の state table を出せること。
- 各 cell に少なくとも `support_state` と `evidence_kind` を export できること。
- C++ 個別 matrix は補助資料扱いで、cross-backend matrix が canonical source と明記されること。
- `python3 tools/check_todo_priority.py` と parity matrix tooling test が通ること。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_backend_parity_matrix*.py'`
- `python3 tools/export_backend_parity_matrix_manifest.py`
- `git diff --check`

決定ログ:
- 2026-03-12: current matrix は scaffold であり、per-cell support state table ではないことを baseline として固定する。
- 2026-03-12: cross-backend matrix を canonical source、各言語の support table は drill-down と位置付ける。
- 2026-03-12: initial cell schema は `support_state` と `evidence_kind` を必須にし、details は optional handoff にとどめる。
- 2026-03-12: `S1-01` として matrix contract / manifest / docs publish target に `row_seed_scaffold` baseline と per-cell gap summary を追加し、scaffold 段階を fail-closed に固定した。
- 2026-03-12: `S2-01` として per-cell schema を `backend/support_state/evidence_kind` required、`details/evidence_ref/diagnostic_kind` optional に固定し、manifest へ top-level export した。
- 2026-03-12: `S3-01` として docs page に seeded 2D table を載せ、table block は contract-generated markdown と marker で drift guard する形に固定した。
- 2026-03-12: `S2-02` として representative rows に `backend_cells` seed を追加し、`cpp=supported/build_run_smoke`、その他 backend は conservative な `not_started/not_started_placeholder` seed に固定した。
- 2026-03-12: `S3-02` として cross-backend matrix を canonical source、`py2cpp` support matrix を cpp-only drill-down と明記し、matrix -> cpp の maintenance order を docs / tooling contract に固定した。
- 2026-03-12: `S4-01` として matrix manifest に rollout-tier order (`representative -> secondary -> long_tail`) を追加し、docs でも fill order を固定した。
- 2026-03-12: `S4-02` として direct fixture-backed smoke がある representative `rs/cs` cell だけを conservative seed から `supported/transpile_smoke` へ上げ、secondary / long_tail は placeholder seed を維持する。
- 2026-03-12: `S4-03` として secondary tier の direct-evidence cell を reviewed state に上げ、`go/java/kt/scala/swift/nim` の representative fixture-backed smoke がある lane だけを `supported/transpile_smoke` へ更新した。
- 2026-03-12: `S4-04` として long-tail tier では representative fixture-backed smoke が確認できる `js/ts/lua/rb/php` の cell だけを `supported/transpile_smoke` へ上げ、`bitwise_invert_basic`、`inheritance_virtual_dispatch_multilang`、`for_range`、`is_instance` に限って conservative seed を更新した。

## 分解

- [x] [ID: P6-BACKEND-PARITY-MATRIX-CELL-FILL-01-S1-01] current scaffold baseline と gap を docs / contract / tooling で固定する。
- [x] [ID: P6-BACKEND-PARITY-MATRIX-CELL-FILL-01-S2-01] parity matrix contract に per-cell schema を追加し、manifest export を更新する。
- [x] [ID: P6-BACKEND-PARITY-MATRIX-CELL-FILL-01-S2-02] representative feature rows へ backend cell seed を追加し、`support_state` / `evidence_kind` を埋められるようにする。
- [x] [ID: P6-BACKEND-PARITY-MATRIX-CELL-FILL-01-S3-01] docs publish target を 2 次元 table として実体化し、cross-backend canonical source を明記する。
- [x] [ID: P6-BACKEND-PARITY-MATRIX-CELL-FILL-01-S3-02] C++ 詳細 table との役割分担、drill-down link、maintenance order を docs / tooling contract に固定する。
- [x] [ID: P6-BACKEND-PARITY-MATRIX-CELL-FILL-01-S4-01] rollout-tier の fill order を matrix manifest と docs に固定する。
- [x] [ID: P6-BACKEND-PARITY-MATRIX-CELL-FILL-01-S4-02] representative tier (`cpp/rs/cs`) の reviewed cell を conservative seed から実値へ埋める。
- [x] [ID: P6-BACKEND-PARITY-MATRIX-CELL-FILL-01-S4-03] secondary tier (`go/java/kt/scala/swift/nim`) の direct-evidence cell を reviewed state に上げる。
- [x] [ID: P6-BACKEND-PARITY-MATRIX-CELL-FILL-01-S4-04] long-tail tier (`js/ts/lua/rb/php`) の reviewed / fail-closed cell を matrix に反映する。
