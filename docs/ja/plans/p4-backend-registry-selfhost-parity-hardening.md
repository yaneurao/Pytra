# P4: backend_registry の正本化と selfhost parity gate の強化

最終更新: 2026-03-09

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01`

背景:
- host 実行系の `toolchain/compiler/backend_registry.py` と selfhost/static 系の `toolchain/compiler/backend_registry_static.py` は、backend spec・runtime copy・emitter wiring・option schema をかなり重複して持っている。
- この重複は bootstrap には有効だったが、backend surface を更新するたびに片側だけ修正する drift を生みやすい。
- selfhost 側にも確認ツールはある。`build_selfhost.py`、`build_selfhost_stage2.py`、`verify_selfhost_end_to_end.py`、`check_multilang_selfhost_suite.py` などが存在するが、運用上は補助ツール寄りで、変換器内部の変更に対する常設 gate としてはまだ弱い。
- さらに、current selfhost path には direct route / host Python bridge / preview lane など複数の暫定経路が混在し、どこまでが expected block でどこからが regression かが分かりづらい。
- P2/P3 で typed boundary と contract を強化しても、registry の SoT と selfhost parity gate が弱いままだと、host lane と selfhost lane の divergence が再発する。

目的:
- backend spec / runtime copy / layer option schema / writer rule の正本を一本化し、host registry と selfhost/static registry の drift を減らす。
- selfhost parity を「参考情報」ではなく、compiler 内部改良の非退行を守る gate として強化する。
- stage1 / stage2 / direct-route / multilang selfhost の failure category を整理し、どの失敗が既知 block でどの失敗が regression かを明確にする。

対象:
- `toolchain/compiler/backend_registry.py`
- `toolchain/compiler/backend_registry_static.py`
- backend spec / runtime copy / option schema / writer helper の共有化
- `tools/build_selfhost.py` / `build_selfhost_stage2.py` / `verify_selfhost_end_to_end.py`
- `tools/check_multilang_selfhost_stage1.py` / `check_multilang_selfhost_multistage.py` / `check_multilang_selfhost_suite.py`
- selfhost parity docs / reports / guard

非対象:
- typed carrier 設計そのもの
- host-Python bridge の完全撤去
- すべての backend を直ちに multistage selfhost 成功へ持ち上げること
- backend language feature の新規実装
- runtime の全面再設計

依存:
- `P2-COMPILER-TYPED-BOUNDARY-01` の boundary ownership が固まっていること
- `P3-COMPILER-CONTRACT-HARDENING-01` の validator / diagnostic 契約が少なくとも representative lane で使えること

## 必須ルール

推奨ではなく必須ルールとして扱う。

1. backend capability / runtime copy / option schema / writer rule の正本は 1 箇所に固定し、host/static へ手書き重複させてはならない。
2. host registry と selfhost/static registry が異なる挙動を持つ場合は、「意図的差分」か「drift」かを明示しなければならない。
3. selfhost parity の failure category は `known_block` / `not_implemented` / `regression` などに分類し、曖昧な preview 文言だけで終わらせてはならない。
4. stage1 / stage2 / direct-route / multilang の representative gate は、release 前または大きな compiler 内部変更前に定常実行できる形へ寄せる。
5. unsupported target / unsupported mode は、registry と parity report の両方で同じ診断カテゴリを返すべきである。
6. runtime copy list や backend spec を更新したときは、shared SoT と parity report の両方を更新しなければならない。
7. selfhost parity は「全部通るまで merge しない」ではなくてもよいが、既知 block と regression を区別できない状態を放置してはならない。

受け入れ基準:
- backend spec / runtime copy / option schema / writer metadata の正本が shared 化され、host/static registry の手書き重複が減る。
- drift を検知する guard または diff test が入り、片側だけ更新された registry surface を検知できる。
- selfhost parity suite に stage1 / stage2 / direct e2e / multilang representative lane の failure category が揃う。
- representative compiler 変更で、どの selfhost failure が expected block でどの failure が regression か追える。
- docs / report / archive で selfhost readiness と known block の文脈が追跡可能になる。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/build_selfhost.py`
- `python3 tools/build_selfhost_stage2.py --skip-stage1-build`
- `python3 tools/verify_selfhost_end_to_end.py --skip-build`
- `python3 tools/check_multilang_selfhost_suite.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/selfhost -p 'test_*selfhost*.py'`
- `git diff --check`

## 実装順

順序は固定する。まず drift source を棚卸しし、次に SoT を一本化し、その後に parity gate を強化する。

1. registry drift と parity blind spot の棚卸し
2. canonical backend spec / runtime metadata の固定
3. host/static registry の shared 化
4. selfhost parity gate / report / failure category の強化
5. docs / archive / migration note の更新

## 分解

- [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S1-01] `backend_registry.py` と `backend_registry_static.py` の重複 surface（backend spec、runtime copy、writer rule、option schema、direct-route behavior）を棚卸しし、intentional difference と drift 候補を分類する。
- [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S1-02] `build_selfhost` / `stage2` / `verify_selfhost_end_to_end` / `multilang selfhost` の現状 gate と blind spot を整理し、known block / regression の分類方針を decision log に固定する。
- [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S2-01] backend capability / runtime copy / option schema / writer metadata の canonical SoT を定義し、host/static の両方がそこから構成される形へ寄せる。
- [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S2-02] intentional difference を許す境界（例: host-only lazy import、selfhost-only direct route）と、その diagnostics 契約を固定する。
- [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S3-01] host registry / static registry を shared metadata または generator 経由へ寄せ、手書き重複を縮退する。
- [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S3-02] registry drift guard または diff test を追加し、片側だけ更新された backend surface を fail-fast で検知する。
- [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S4-01] stage1 / stage2 / direct e2e / multilang selfhost の representative parity suite を整理し、failure category と summary 出力を統一する。
- [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S4-02] unsupported / preview / known block / regression の診断カテゴリを registry と parity report で揃え、expected failure を明示管理できるようにする。
- [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S5-01] docs / plan report / archive を更新し、backend readiness・known block・gate 実行手順を追跡可能にする。
- [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S5-02] representative internal change に対して host lane と selfhost lane が同じ contract で検証されることを確認し、再流入 guard を固定する。

## 期待 deliverable

### S1 の deliverable

- host/static registry の drift 候補一覧
- selfhost parity の blind spot 一覧

### S2 の deliverable

- backend registry SoT の設計
- intentional difference と diagnostics 契約

### S3 の deliverable

- shared metadata / generator / adapter
- drift guard

### S4 の deliverable

- selfhost parity summary のカテゴリ統一
- stage1 / stage2 / direct-route / multilang の representative gate

### S5 の deliverable

- readiness と known block を追跡できる docs/report
- 今後の internal 改修で host/selfhost divergence を検知する再流入 guard

決定ログ:
- 2026-03-09: ユーザー指示により、backend registry の重複と selfhost parity 運用を内部改善タスクとして独立 P4 に切り出した。
- 2026-03-09: この P4 は backend language feature 追加ではなく、registry の SoT 一本化と selfhost non-regression gate の強化を主眼に置く。
- 2026-03-09: host lane と selfhost lane の差分を全面禁止するのではなく、intentional difference と drift を区別し、両者を report / guard で管理する方針を固定した。
