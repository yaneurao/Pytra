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

- [ ] [ID: P5-BACKEND-FEATURE-PARITY-CONTRACT-01-S1-01] syntax / builtins / `pytra.std.*` の representative feature を feature ID 単位で棚卸しし、inventory の category と naming rule を固定する。
- [ ] [ID: P5-BACKEND-FEATURE-PARITY-CONTRACT-01-S1-02] backend support state（`supported` / `fail_closed` / `not_started` / `experimental`）と、その判定条件を decision log に固定する。
- [ ] [ID: P5-BACKEND-FEATURE-PARITY-CONTRACT-01-S2-01] backend 未対応 feature の fail-closed policy と diagnostic category を整理し、silent fallback 禁止 rule を明文化する。
- [ ] [ID: P5-BACKEND-FEATURE-PARITY-CONTRACT-01-S2-02] 新 feature 導入時の acceptance rule を決め、`C++ だけ通れば完了` としない運用を定義する。
- [ ] [ID: P5-BACKEND-FEATURE-PARITY-CONTRACT-01-S3-01] representative inventory document / tooling / docs handoff を整え、後段 conformance suite と support matrix へ接続する。

## 決定ログ

- 2026-03-12: backend parity は重要だが、直近の `py_runtime.h` shrink 系 `P0-P4` を止めるべきではないため `P5` に置く。
- 2026-03-12: parity の正本は C++ 実装ではなく feature contract / EAST3 contract / `pytra.std.*` 契約とする。
