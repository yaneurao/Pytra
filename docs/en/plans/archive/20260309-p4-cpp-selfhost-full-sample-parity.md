<a href="../../ja/plans/archive/20260309-p4-cpp-selfhost-full-sample-parity.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/archive/20260309-p4-cpp-selfhost-full-sample-parity.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/archive/20260309-p4-cpp-selfhost-full-sample-parity.md`

# P4: C++ 多段 selfhost binary の full sample parity

最終更新: 2026-03-09

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P4-CPP-SELFHOST-FULLPARITY-01`

関連:
- [archive/20260308-p4-cpp-selfhost-rollout.md](./archive/20260308-p4-cpp-selfhost-rollout.md)
- [spec-tools.md](../spec/spec-tools.md)
- [how-to-use.md](../how-to-use.md)
- [tools/build_selfhost.py](../../tools/build_selfhost.py)
- [tools/build_selfhost_stage2.py](../../tools/build_selfhost_stage2.py)
- [tools/verify_selfhost_end_to_end.py](../../tools/verify_selfhost_end_to_end.py)
- [tools/check_selfhost_stage2_cpp_diff.py](../../tools/check_selfhost_stage2_cpp_diff.py)

背景:
- `P4-CPP-SELFHOST-ROLLOUT-01` で、stage1 build、direct `.py` route、representative diff/e2e、stage2 build、stage2 strict diff までは復旧済みである。
- しかし 2026-03-09 時点で確認済みなのは representative case だけであり、`selfhost/py2cpp_stage2.out` を使って `sample/py/*.py` 全件を C++ 化し、compile/run まで含めた parity を通した記録は無い。
- したがって現在の selfhost は「代表ケースでは使える」が、「stage2 binary で full sample parity を通した」とまでは言えない。
- user-facing にはここが重要であり、stage2 selfhost binary が host Python route と同等に sample corpus を処理できることを明示的に確認する必要がある。

目的:
- `selfhost/py2cpp_stage2.out` を canonical multi-stage selfhost binary として、`sample/py/*.py` 全件に対する transpile + compile + run parity を green にする。
- representative diff では見えない sample corpus 固有の regressions を洗い出し、host route と selfhost route の差を full sample レベルで把握できるようにする。
- 確認コマンドを docs / local CI へ戻せる形まで整理する。

対象:
- `tools/build_selfhost_stage2.py`
- `tools/verify_selfhost_end_to_end.py`
- 必要なら新設する `tools/check_selfhost_stage2_sample_parity.py` または同等 wrapper
- `sample/py/*.py`
- selfhost stage2 binary (`selfhost/py2cpp_stage2.out`)

非対象:
- stage1 direct compile の再確認（既存 plan で完了済み）
- host/selfhost representative strict diff の再設計
- 非 C++ target の selfhost parity
- `py_runtime.h` の追加縮退

受け入れ基準:
- `python3 tools/build_selfhost_stage2.py` が green である。
- stage2 binary を使って `sample/py/*.py` 全件を C++ 化し、compile/run parity を確認できる canonical command が存在する。
- canonical command の実行結果として `sample` 全件が `pass` になる。
- 失敗が出た場合は sample 名・failure class を決定ログへ記録し、最終的に `pass=18 fail=0` へ戻す。
- docs に「representative selfhost check」と「full sample parity through stage2 binary」の違いを明記する。

確認コマンド:
- `python3 tools/build_selfhost_stage2.py`
- `python3 tools/verify_selfhost_end_to_end.py --skip-build --selfhost-bin selfhost/py2cpp_stage2.out --cases sample/py/01_mandelbrot.py ... sample/py/18_mini_language_interpreter.py`
- `python3 tools/check_selfhost_stage2_cpp_diff.py --mode strict`

## 1. 基本方針

1. canonical target は `selfhost/py2cpp_stage2.out` に固定する。multi-stage selfhost binary の parity を確認したいので、stage1 binary は使わない。
2. 既存の `verify_selfhost_end_to_end.py` を再利用できるなら wrapper を足すだけにし、専用 runner の重複実装は避ける。
3. representative diff/smoke は既に別 plan で green なので、本計画は `sample/py/*.py` の full corpus に集中する。
4. failure は「transpile」「compile」「run」「stdout mismatch」に分類して決定ログへ残す。sample corpus が広いので、再現不能な総論だけを残さない。

## 2. フェーズ

### Phase 1: canonical command 固定

- stage2 binary 用 full sample parity の正本コマンドを決める。
- 既存 `verify_selfhost_end_to_end.py` をそのまま使うか、`sample/py` 全件を列挙する薄い wrapper を作るかを決める。
- sample corpus の ignore-prefix (`elapsed_sec:` など) を stage2 binary route でも host route と同じ規約で扱うことを確認する。

### Phase 2: full sample parity 実行

- `build_selfhost_stage2.py` を実行して stage2 binary を最新化する。
- `sample/py/*.py` 全件を stage2 binary で transpile し、compile/run parity を回す。
- failure を `transpile/compile/run/stdout` に分類し、再現コマンドを決定ログへ残す。

### Phase 3: blocker 修正

- sample corpus で露見した stage2 selfhost 固有 failure を修正する。
- host route は green のまま、stage2 route だけが落ちる regressions を優先して潰す。
- 必要なら stage2 runtime / selfhost source / direct route glue を調整する。

### Phase 4: 運用固定

- docs に canonical full sample parity コマンドを追記する。
- local CI に戻すかどうかを判断し、少なくとも advisory command として残す。
- plan と TODO を archive へ移す。

## 3. 着手時の注意

- `check_selfhost_stage2_cpp_diff.py --mode strict` が green でも full sample parity の代替にはならない。差分一致と compile/run parity は別物である。
- `verify_selfhost_end_to_end.py` はデフォルトで stage1 binary を前提にしているため、stage2 binary を使うときは `--selfhost-bin selfhost/py2cpp_stage2.out` を明示する。
- sample corpus は時間依存出力を持つため、既存の ignore-prefix 規約から外れる差分を増やさない。

## 4. タスク分解

- [ ] [ID: P4-CPP-SELFHOST-FULLPARITY-01] `selfhost/py2cpp_stage2.out` を使った full sample parity を green にする。
- [x] [ID: P4-CPP-SELFHOST-FULLPARITY-01-S1-01] stage2 full sample parity の canonical command を固定する。
- [x] [ID: P4-CPP-SELFHOST-FULLPARITY-01-S1-02] `verify_selfhost_end_to_end.py` 再利用か wrapper 新設かを決定する。
- [ ] [ID: P4-CPP-SELFHOST-FULLPARITY-01-S2-01] stage2 binary で sample 全件 parity を実行し、failure を分類する。
- [ ] [ID: P4-CPP-SELFHOST-FULLPARITY-01-S2-02] failure 一覧と再現コマンドを決定ログへ固定する。
- [ ] [ID: P4-CPP-SELFHOST-FULLPARITY-01-S3-01] stage2 selfhost 固有 blocker を修正する。
- [ ] [ID: P4-CPP-SELFHOST-FULLPARITY-01-S3-02] `sample` 全件 `pass=18 fail=0` を確認する。
- [ ] [ID: P4-CPP-SELFHOST-FULLPARITY-01-S4-01] docs / local CI 運用を更新する。
- [ ] [ID: P4-CPP-SELFHOST-FULLPARITY-01-S4-02] archive を同期して本計画を閉じる。

## 5. 決定ログ

- 2026-03-09: 起票時点では representative selfhost checks（direct compile / representative e2e / representative strict diff / stage2 strict diff）は green だが、`selfhost/py2cpp_stage2.out` を使った full sample parity の実行記録は無い。したがって本計画は stage2 binary に限定した full corpus parity を対象にする。
- 2026-03-09: canonical command は `python3 tools/check_selfhost_stage2_sample_parity.py [--skip-build]` とし、実体は `verify_selfhost_end_to_end.py --skip-build --selfhost-bin selfhost/py2cpp_stage2.out --cases sample/py/*.py` を呼ぶ thin wrapper で統一する。full sample 列挙と stage2 binary 固定だけを wrapper 側で持ち、e2e 実装は重複させない。
