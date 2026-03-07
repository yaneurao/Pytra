# P4: linked-program 後の非C++ backend 修復

最終更新: 2026-03-07

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P4-NONCPP-BACKEND-RECOVERY-01`

背景:
- `P0-LINKED-PROGRAM-OPT-01` では、global optimizer の入力単位を linked program へ拡張し、backend 契約を `ModuleEmitter + ProgramWriter` へ再編する。この変更は C++ を主対象に進めるが、`backend_registry.py` / `py2x.py` / `ir2lang.py` の共通経路に触れるため、非C++ backend 側の single-file 導線が壊れやすい。
- 非C++ backend は `P1-MULTILANG-BACKEND-3LAYER-01` で `lower/optimizer/emitter` の3層化までは完了しているが、linked-program 契約を前提にした互換層、health matrix、修復順序、共通 gate はまだ固定されていない。
- 現状の checker は `tools/check_noncpp_east3_contract.py`、`tools/check_py2x_transpile.py`、`test/unit/common/test_py2x_smoke_common.py`、各言語 smoke、`tools/runtime_parity_check.py` に分散しており、「どの target が、どの層で、なぜ壊れているか」を 1 枚で見渡せない。
- linked-program 導入と非C++ backend の修復を同時に進めると、互換層不足による共通経路破壊と、各言語固有の runtime / quality 差分が混ざり、blocking chain が見えなくなる。

目的:
- `P0-LINKED-PROGRAM-OPT-01` の完了後、非C++ backend を linked-program 時代の backend 契約へ順次追従させる。
- `backend_registry` / `py2x` / `ir2lang` の共通経路について、非C++ backend は `SingleFileProgramWriter` ベースで安定動作する状態へ揃える。
- backend ごとの壊れ方を `static contract` / `smoke` / `transpile` / `parity` / `toolchain missing` に分類し、修復順序を family 単位で固定する。
- linked-program 導入後も「C++ だけが新契約で、他言語は壊れたまま」という状態を解消し、非C++ backend の回帰を継続監視できる運用にする。

依存関係:
- 本計画は `P0-LINKED-PROGRAM-OPT-01` の後続として扱う。少なくとも `P0-LINKED-PROGRAM-OPT-01-S5-02`（旧 `emit -> str` 互換 wrapper と `SingleFileProgramWriter`）が完了していることを前提とする。
- 本計画は C++ backend の設計・品質改善を目的としない。C++ は linked-program 導入の先行対象として別 P0/P1 で扱う。

対象:
- `src/backends/{rs,cs,js,ts,go,java,kotlin,swift,ruby,lua,php,scala,nim}/`
- `src/toolchain/compiler/backend_registry.py`
- `src/py2x.py`, `src/ir2lang.py`, `src/pytra-cli.py`
- `tools/check_noncpp_east3_contract.py`
- `tools/check_py2x_transpile.py` と各 profile
- `test/unit/common/test_py2x_smoke_common.py`
- 各言語 smoke / transpile / parity 導線
- 必要な `docs/ja/spec` / `docs/en/spec`

非対象:
- C++ backend の追加修復
- linked-program schema 自体の再設計
- 各言語 runtime の全面刷新
- selfhost の完全化
- sample 出力品質の微調整のみを目的とした改善

受け入れ基準:
- 非C++ backend 全 target が linked-program 導入後の共通経路で fail-closed に動作し、旧 `emit -> str` 互換に依存する箇所が明示管理される。
- 各 target について、少なくとも `static contract`、共通 smoke、言語別 smoke、`check_py2x_transpile.py --target <lang>` の状態が fixed baseline として記録される。
- `toolchain missing` を除く infra failure は family 単位で解消され、`runtime_parity_check.py` の failure は runtime/quality 差分として切り分けられる。
- `run_local_ci.py` または同等の回帰導線で、non-C++ backend の最低限 gate が継続監視される。
- 修復順序と done 条件が `docs/ja/spec` / `docs/en/spec` / 計画書に固定され、今後の backend 追加でも同じ手順で追従できる。

修復の基本方針:
1. まず「backend が壊れている」状態をカテゴリ分解して health matrix 化する。
2. linked-program 対応で必要な互換層は、backend 共通経路で先に止血する。
3. 修復は backend family 単位で進め、同じ壊れ方をまとめて直す。
4. 各 family で `static -> smoke -> transpile -> parity` の順に gate を閉じる。
5. `toolchain missing` は infra failure と混ぜず、別カテゴリとして baseline 管理する。

推奨 wave:
- Wave 1: `rs`, `cs`, `js`, `ts`
  - 共通 `CodeEmitter` 系と `SingleFileProgramWriter` の相性確認に向く。
- Wave 2: `go`, `java`, `kotlin`, `swift`, `scala`
  - native emitter 系の typed backend 群。
- Wave 3: `ruby`, `lua`, `php`, `nim`
  - runtime 差分や動的言語寄りの failure を持ちやすい群。

health matrix の failure category:
- `static_contract_fail`
  - `tools/check_noncpp_east3_contract.py` 不通、layer 契約・逆流 import・責務境界違反。
- `common_smoke_fail`
  - `test_py2x_smoke_common.py` 失敗。
- `target_smoke_fail`
  - 各言語の smoke suite 失敗。
- `transpile_fail`
  - `tools/check_py2x_transpile.py --target <lang>` 失敗。
- `parity_fail`
  - `tools/runtime_parity_check.py` 失敗。
- `toolchain_missing`
  - compiler / runtime 未導入により parity 実行不能。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_noncpp_east3_contract.py --skip-transpile`
- `PYTHONPATH=src:. python3 -m unittest discover -s test/unit/common -p 'test_py2x_smoke*.py'`
- `PYTHONPATH=src:. python3 -m unittest discover -s test/unit/backends -p 'test_py2*_smoke.py'`
- `python3 tools/check_py2x_transpile.py --target rs`
- `python3 tools/check_py2x_transpile.py --target cs`
- `python3 tools/check_py2x_transpile.py --target js`
- `python3 tools/check_py2x_transpile.py --target ts`
- `python3 tools/check_py2x_transpile.py --target go`
- `python3 tools/check_py2x_transpile.py --target java`
- `python3 tools/check_py2x_transpile.py --target kotlin`
- `python3 tools/check_py2x_transpile.py --target swift`
- `python3 tools/check_py2x_transpile.py --target ruby`
- `python3 tools/check_py2x_transpile.py --target lua`
- `python3 tools/check_py2x_transpile.py --target php`
- `python3 tools/check_py2x_transpile.py --target scala`
- `python3 tools/check_py2x_transpile.py --target nim`
- `python3 tools/runtime_parity_check.py --targets rs,cs,js,ts --case-root sample --ignore-unstable-stdout`
- `python3 tools/runtime_parity_check.py --targets go,java,kotlin,swift,scala --case-root sample --ignore-unstable-stdout`
- `python3 tools/runtime_parity_check.py --targets ruby,lua,php,nim --case-root sample --ignore-unstable-stdout`

## 分解

- [ ] [ID: P4-NONCPP-BACKEND-RECOVERY-01-S1-01] linked-program 後の non-C++ backend health matrix を作成し、各 target を failure category ごとに分類する。
- [ ] [ID: P4-NONCPP-BACKEND-RECOVERY-01-S1-02] done 条件（static/smoke/transpile/parity/toolchain missing の扱い）と修復順序を spec/plan に固定する。
- [ ] [ID: P4-NONCPP-BACKEND-RECOVERY-01-S2-01] `backend_registry.py` / `py2x.py` / `ir2lang.py` の non-C++ 互換層を点検し、`SingleFileProgramWriter` 前提の backend 共通契約不足を埋める。
- [ ] [ID: P4-NONCPP-BACKEND-RECOVERY-01-S2-02] non-C++ backend health checker を追加または既存 checker を統合し、family 単位の broken/green を 1 コマンドで見られるようにする。
- [ ] [ID: P4-NONCPP-BACKEND-RECOVERY-01-S3-01] Wave 1（`rs/cs/js/ts`）の static contract / smoke / transpile failure を解消し、compat route を安定化する。
- [ ] [ID: P4-NONCPP-BACKEND-RECOVERY-01-S3-02] Wave 1 の parity baseline を更新し、runtime 差分と infra failure を分離する。
- [ ] [ID: P4-NONCPP-BACKEND-RECOVERY-01-S4-01] Wave 2（`go/java/kotlin/swift/scala`）の static contract / smoke / transpile failure を解消する。
- [ ] [ID: P4-NONCPP-BACKEND-RECOVERY-01-S4-02] Wave 2 の parity baseline を更新し、`toolchain missing` / 実行 failure / artifact 差分を固定化する。
- [ ] [ID: P4-NONCPP-BACKEND-RECOVERY-01-S5-01] Wave 3（`ruby/lua/php/nim`）の static contract / smoke / transpile failure を解消する。
- [ ] [ID: P4-NONCPP-BACKEND-RECOVERY-01-S5-02] Wave 3 の parity baseline を更新し、runtime 差分と backend bug を切り分ける。
- [ ] [ID: P4-NONCPP-BACKEND-RECOVERY-01-S6-01] `run_local_ci.py` または同等の回帰導線へ non-C++ backend health check を統合する。
- [ ] [ID: P4-NONCPP-BACKEND-RECOVERY-01-S6-02] `docs/ja/spec` / `docs/en/spec` / `docs/ja/how-to-use.md` を更新し、linked-program 後の non-C++ backend 修復運用を固定して計画を閉じる。

## フェーズ詳細

### Phase 1: 現状固定

やること:
- 現行 non-C++ target を 1 言語ずつ実測し、health matrix を作る。
- failure を `static_contract_fail/common_smoke_fail/target_smoke_fail/transpile_fail/parity_fail/toolchain_missing` に分類する。
- `check_noncpp_east3_contract.py` の対象外や盲点があれば、計画上で gap を明示する。

成果物:
- target x category の matrix
- family ごとの優先順
- linked-program 後に共通経路だけで壊れるのか、言語固有 bug なのかの切り分け

### Phase 2: 共通 stop-ship 契約

やること:
- `backend_registry.py` / `py2x.py` / `ir2lang.py` の non-C++ 経路を点検し、`SingleFileProgramWriter` と module emit contract の不足を埋める。
- 非C++ backend を壊したときに最初に fail する checker を整理し、1 コマンド health check を用意する。

成果物:
- linked-program 後も non-C++ backend が即死しない互換層
- 修復 wave に入る前の stop-ship gate

### Phase 3-5: backend family 修復

共通手順:
1. static contract を通す。
2. 共通 smoke を通す。
3. 言語別 smoke を通す。
4. transpile check を通す。
5. parity を回して failure category を再分類する。

波ごとの狙い:
- Wave 1 は共通 emitter 系の template 固め。
- Wave 2 は native typed backend 群の共通 failure を潰す。
- Wave 3 は runtime 差分が大きい backend 群を最後に切り分ける。

### Phase 6: 運用固定

やること:
- `run_local_ci.py` か同等導線に family 単位 health check を追加する。
- docs に「新しい backend 契約変更を入れたら、どの checker を先に見るか」を固定する。

成果物:
- 回帰時の見方が統一された運用
- 低優先度の backlog ではなく、継続監視される状態

## 7. Health Matrix Snapshot（2026-03-08）

測定条件:
- `static_contract`: `python3 tools/check_noncpp_east3_contract.py --skip-transpile`
- `common_smoke`: `PYTHONPATH=src:.:test/unit python3 -m unittest discover -s test/unit/common -p 'test_py2x_smoke*.py'`
- `target_smoke`: `PYTHONPATH=src:.:test/unit python3 -m unittest discover -s test/unit/backends/<dir> -p 'test_py2<lang>_smoke.py'`
- `transpile`: `python3 tools/check_py2x_transpile.py --target <lang>`
- `parity`: smoke/transpile を通過した target だけ `python3 tools/runtime_parity_check.py --targets <lang> --case-root sample --ignore-unstable-stdout`

共通結果:
- `static_contract`: pass
- `common_smoke`: pass

| target | target_smoke | transpile | parity | primary_failure | notes |
| --- | --- | --- | --- | --- | --- |
| `rs` | fail | pass | blocked | `target_smoke_fail` | `test_py2rs_smoke.py` が 31 tests 中 1 fail。 |
| `cs` | pass | pass | `toolchain_missing` | `toolchain_missing` | sample parity 18 case 全件 skip。 |
| `js` | pass | pass | ok | `ok` | sample parity `18/18`。 |
| `ts` | pass | pass | ok | `ok` | sample parity `18/18`。 |
| `go` | fail | pass | blocked | `target_smoke_fail` | `test_go_native_emitter_uses_runtime_path_wrapper` fail。 |
| `java` | fail | pass | blocked | `target_smoke_fail` | `pathlib.Path` runtime path class smoke が fail。 |
| `kotlin` | pass | fail | blocked | `transpile_fail` | sample 群で多数 Traceback。 |
| `swift` | pass | fail | blocked | `transpile_fail` | sample 群で多数 Traceback。 |
| `scala` | fail | pass | blocked | `target_smoke_fail` | `pathlib_extended` smoke が fail。 |
| `ruby` | pass | fail | blocked | `transpile_fail` | sample 群で多数 Traceback。 |
| `lua` | fail | pass | blocked | `target_smoke_fail` | ifexp/joinedstr lowering smoke が fail。 |
| `php` | pass | fail | blocked | `transpile_fail` | fixture/sample mixed で 9 fail。 |
| `nim` | pass | fail | blocked | `transpile_fail` | fixture/sample mixed で 6 fail。 |

## 決定ログ

- 2026-03-07: ユーザー指示により、「linked-program 導入後に壊れたままの非C++ backend を直していく計画」を低優先度の後続タスクとして起票する方針を採用。
- 2026-03-07: 本計画は `P0-LINKED-PROGRAM-OPT-01` の blocker にはせず、`SingleFileProgramWriter` を含む共通互換層の着地後に着手する P4 として定義した。
- 2026-03-07: 修復順序は `health matrix -> 互換 stop-ship 契約 -> family wave -> CI/運用固定` の4段階とし、`rs/cs/js/ts`、`go/java/kotlin/swift/scala`、`ruby/lua/php/nim` の3 wave で進める方針を確定した。
- 2026-03-08: [ID: P4-NONCPP-BACKEND-RECOVERY-01-S1-01] static contract と common smoke は pass、初期 health matrix では `js` / `ts` が green、`cs` は `toolchain_missing`、`rs/go/java/scala/lua` は `target_smoke_fail`、`kotlin/swift/ruby/php/nim` は `transpile_fail` を primary failure として確定した。`parity` は smoke/transpile green の target だけ追加測定し、`js` / `ts` は `18/18`、`cs` は 18 case 全件 `toolchain_missing` だった。
