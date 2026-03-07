# P1: 全target sample parity 完了

最終更新: 2026-03-08

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-ALLTARGET-SAMPLE-PARITY-01`

背景:
- 2026-03-08 時点の sample parity baseline では、`cpp/js/ts` だけが `18/18` で green であり、他の parity target は backend bug を潰した後も `toolchain_missing` として残っている。
- `P4-NONCPP-BACKEND-RECOVERY-01` により non-C++ backend の `static/smoke/transpile` は green になったが、これは「実行環境が無いため parity を最後まで確認できていない」状態を含む。
- GC を持たない言語を C++ runtime に近い ownership 構成へ寄せる議論を進める前に、各 target が現実に sample parity を完走できる状態を作り、layout 問題と toolchain 不足を切り分ける必要がある。

目的:
- parity target 全体について、`sample/py` 18 ケースの parity が `toolchain_missing` なしで実行できる状態にする。
- `toolchain_missing` を infra baseline ではなく修復対象として扱い、target ごとの実行環境不足を解消する。
- toolchain 導入後に露出する runtime / backend / build bug を潰し、全 target の sample parity を `pass` に揃える。

対象:
- parity target 全体:
  - `cpp`, `rs`, `cs`, `js`, `ts`, `go`, `java`, `kotlin`, `swift`, `scala`, `ruby`, `lua`, `php`, `nim`
- `tools/runtime_parity_check.py`
- `src/toolchain/compiler/pytra_cli_profiles.py` が返す target profile / runner needs
- target ごとの runtime/build/run 導線
- 必要な `docs/ja/spec` / `docs/en/spec` / `docs/ja/how-to-use.md`

非対象:
- runtime layout を `generated/native` へ統一する設計変更そのもの
- sample の見た目品質改善
- selfhost 完全化
- parity target 以外の backend 追加

受け入れ基準:
- parity target 全体について、sample parity 実行時に `toolchain_missing` が 0 件になる。
- `cpp/js/ts` は引き続き `18/18 ok` を維持する。
- `rs/cs/go/java/kotlin/swift/scala/ruby/lua/php/nim` も、sample parity 18 ケースを `run_failed=0`, `output_mismatch=0`, `artifact_*_mismatch=0` で完了する。
- `tools/runtime_parity_check.py --case-root sample --targets <all-targets> --all-samples` 相当の実行手順が docs に固定される。
- target ごとの必要 toolchain と bootstrap 手順が明文化され、`toolchain_missing` が新しい常態にならない。
- full green 判定では `ok` 以外の parity category を 1 件も許容しない。具体的には `case_missing`, `python_failed`, `python_artifact_missing`, `toolchain_missing`, `transpile_failed`, `run_failed`, `output_mismatch`, `artifact_presence_mismatch`, `artifact_missing`, `artifact_size_mismatch`, `artifact_crc32_mismatch` をすべて 0 件にする。

基本方針:
1. まず target profile が要求する toolchain を棚卸しし、どの実行ファイル不足で `toolchain_missing` になっているかを確定する。
2. toolchain を入れた段階で parity を回し、露出した runtime / emitter / build bug を target 単位で潰す。
3. 既に green な `cpp/js/ts` は baseline target として継続監視し、他 target の修復で壊していないことを確認する。
4. 最後に docs / scripts / health check を「toolchain が入っていれば全 target parity が通る」前提へ更新する。

2026-03-08 current machine toolchain matrix:

| target | runner_needs | current status | missing tools |
| --- | --- | --- | --- |
| `cpp` | `python`, `make`, `g++` | available | - |
| `rs` | `python`, `rustc` | toolchain_missing | `rustc` |
| `cs` | `python`, `mcs`, `mono` | toolchain_missing | `mcs`, `mono` |
| `js` | `python`, `node` | available | - |
| `ruby` | `python`, `ruby` | toolchain_missing | `ruby` |
| `lua` | `python`, `lua` | toolchain_missing | `lua` |
| `php` | `python`, `php` | toolchain_missing | `php` |
| `ts` | `python`, `node`, `npx` | available | - |
| `go` | `python`, `go` | toolchain_missing | `go` |
| `java` | `python`, `javac`, `java` | toolchain_missing | `javac`, `java` |
| `swift` | `python`, `swiftc` | toolchain_missing | `swiftc` |
| `kotlin` | `python`, `kotlinc`, `java` | toolchain_missing | `kotlinc`, `java` |
| `scala` | `python`, `scala` | toolchain_missing | `scala` |
| `nim` | `python`, `nim` | toolchain_missing | `nim` |

Phase 1 snapshot:
- baseline available target は `cpp/js/ts` の 3 target。
- compiled target 群は `rs/cs/go/java/kotlin/swift/scala` が全件 `toolchain_missing`。
- scripting / mixed target 群は `ruby/lua/php/nim` が全件 `toolchain_missing`。
- `runner_needs` は `src/toolchain/compiler/pytra_cli_profiles.py`、tool presence は `shutil.which(...)` 実測を正本とする。

2026-03-08 bootstrap commands executed on current Debian 12 machine:

- compiled target 群:
  - `apt-get update`
  - `apt-get install -y rustc mono-mcs golang-go openjdk-17-jdk kotlin scala nim`
  - `apt-get install -y binutils-gold gcc git libcurl4-openssl-dev libedit-dev libpython3-dev libsqlite3-dev uuid-dev gnupg2`
  - `curl -fL -o /opt/swift-6.2.2-RELEASE-debian12.tar.gz https://download.swift.org/swift-6.2.2-release/debian12/swift-6.2.2-RELEASE/swift-6.2.2-RELEASE-debian12.tar.gz`
  - `tar -xf /opt/swift-6.2.2-RELEASE-debian12.tar.gz -C /opt`
  - `ln -sfn /opt/swift-6.2.2-RELEASE-debian12/usr/bin/swift /usr/local/bin/swift`
  - `ln -sfn /opt/swift-6.2.2-RELEASE-debian12/usr/bin/swiftc /usr/local/bin/swiftc`
- scripting / mixed target 群:
  - `apt-get install -y ruby lua5.4 php-cli`

Post-bootstrap snapshot:
- parity target 全体で `runner_needs` は解決済み。
- `toolchain_missing` は current machine baseline から除去された。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/runtime_parity_check.py --targets cpp,rs,cs,js,ruby,lua,php,ts,go,java,swift,kotlin,scala,nim --case-root sample --all-samples --ignore-unstable-stdout --east3-opt-level 2 --cpp-codegen-opt 3`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root sample --all-samples --east3-opt-level 2 --cpp-codegen-opt 3`
- `python3 tools/runtime_parity_check.py --targets js,ts --case-root sample --ignore-unstable-stdout --all-samples --east3-opt-level 2`
- `python3 tools/runtime_parity_check.py --targets rs,cs,go,java,kotlin,swift,scala --case-root sample --ignore-unstable-stdout --all-samples --east3-opt-level 2`
- `python3 tools/runtime_parity_check.py --targets ruby,lua,php,nim --case-root sample --ignore-unstable-stdout --all-samples --east3-opt-level 2`
- `python3 tools/check_noncpp_backend_health.py --family all`

## 分解

- [x] [ID: P1-ALLTARGET-SAMPLE-PARITY-01-S1-01] parity target 全体の `runner_needs` と current `toolchain_missing` を棚卸しし、target ごとの不足 toolchain を matrix 化する。
- [x] [ID: P1-ALLTARGET-SAMPLE-PARITY-01-S1-02] 「全target parity green」の done 条件、許容しない failure category、確認コマンドを spec/plan に固定する。
- [x] [ID: P1-ALLTARGET-SAMPLE-PARITY-01-S2-01] compiled target 群（`rs/cs/go/java/kotlin/swift/scala`）の toolchain bootstrap 手順を整備し、`toolchain_missing` を解消する。
- [x] [ID: P1-ALLTARGET-SAMPLE-PARITY-01-S2-02] scripting / mixed target 群（`ruby/lua/php/nim`）の toolchain bootstrap 手順を整備し、`toolchain_missing` を解消する。
- [x] [ID: P1-ALLTARGET-SAMPLE-PARITY-01-S3-01] baseline target（`cpp/js/ts`）の sample parity を再確認し、他 target 修復中も `18/18` を維持する。
- [ ] [ID: P1-ALLTARGET-SAMPLE-PARITY-01-S3-02] compiled target 群（`rs/cs/go/java/kotlin/swift/scala`）の sample parity を green へ持ち上げる。
- [ ] [ID: P1-ALLTARGET-SAMPLE-PARITY-01-S3-03] scripting / mixed target 群（`ruby/lua/php/nim`）の sample parity を green へ持ち上げる。
- [ ] [ID: P1-ALLTARGET-SAMPLE-PARITY-01-S4-01] 全 target parity 一括実行の scripts / docs / how-to-use を整備し、再実行手順を固定する。
- [ ] [ID: P1-ALLTARGET-SAMPLE-PARITY-01-S4-02] full parity 実行結果を記録し、計画を archive へ移して閉じる。

## フェーズ詳細

### Phase 1: baseline 固定

やること:
- `pytra_cli_profiles` の parity target と `runner_needs` を一覧化する。
- `toolchain_missing` の実測結果を target ごとに記録する。
- 「全 target parity green」を、`toolchain_missing=0` を含む明確な done 条件として固定する。

成果物:
- target x needs x status の matrix
- parity green の厳密な定義

### Phase 2: toolchain bootstrap

やること:
- compiled target と scripting/mixed target を分けて、必要な toolchain を整える。
- 手元で入れるべき実行ファイル名、PATH 前提、確認コマンドを固定する。

成果物:
- `toolchain_missing` を潰すための手順
- parity 実行可能な環境

### Phase 3: parity 修復

やること:
- 実際に sample parity を target 群ごとに回す。
- 露出した `run_failed`, `output_mismatch`, `artifact_size_mismatch`, `artifact_crc32_mismatch` を target ごとに潰す。
- 既に green な target を回帰から守る。

成果物:
- 全 target `sample 18/18`
- `toolchain_missing=0`

### Phase 4: 運用固定

やること:
- 全 target parity 実行コマンドを docs と scripts に反映する。
- 完了結果を archive へ残し、今後は parity を「実行できれば通る」状態として維持する。

成果物:
- docs 化された再実行手順
- archive 済みの完了計画

## 決定ログ

- 2026-03-08: ユーザー指示により、sample parity を「一部 target だけ green、他は `toolchain_missing`」の状態で止めず、全 parity target で実行完了できるようにする後続計画を起票する。
- 2026-03-08: 本計画は runtime layout 再編より先に行う。理由は、layout 問題と toolchain 不足を混ぜると設計判断がぶれるためである。
- 2026-03-08: 既存 baseline では `cpp/js/ts` が green、その他は `toolchain_missing` である。したがって本計画の主対象は「backend bug 修正」よりまず「実行環境不足の解消」とする。
- 2026-03-08 [ID: P1-ALLTARGET-SAMPLE-PARITY-01-S1-01]: `pytra_cli_profiles.list_parity_targets()` と `TargetProfile.runner_needs`、および current machine の `shutil.which(...)` 実測を突き合わせ、Phase 1 baseline を `cpp/js/ts` available、その他 11 target は `toolchain_missing` として matrix 化した。
- 2026-03-08 [ID: P1-ALLTARGET-SAMPLE-PARITY-01-S1-02]: full parity green は `runtime_parity_check.py` の category が `ok` のみである状態と定義し、canonical command を `--targets cpp,rs,cs,js,ruby,lua,php,ts,go,java,swift,kotlin,scala,nim --case-root sample --all-samples --ignore-unstable-stdout --east3-opt-level 2 --cpp-codegen-opt 3` に固定した。
- 2026-03-08 [ID: P1-ALLTARGET-SAMPLE-PARITY-01-S2-01]: compiled target 向けに `rustc`, `mono-mcs/mono`, `go`, `openjdk-17-jdk`, `kotlin`, `scala`, `nim` を apt で導入し、`swiftc` は official `swift-6.2.2-RELEASE-debian12` tarball を `/opt` へ展開して `/usr/local/bin/swiftc` へ symlink した。
- 2026-03-08 [ID: P1-ALLTARGET-SAMPLE-PARITY-01-S2-02]: scripting / mixed target 向けに `ruby`, `lua5.4`, `php-cli` を apt で導入し、導入後の `runner_needs` 実測で parity target 14 件すべてが `OK` になったことを確認した。
- 2026-03-08 [ID: P1-ALLTARGET-SAMPLE-PARITY-01-S3-01]: `python3 tools/runtime_parity_check.py --targets cpp,js,ts --case-root sample --all-samples --ignore-unstable-stdout --east3-opt-level 2 --cpp-codegen-opt 3` を current machine で実行し、`SUMMARY cases=18 pass=18 fail=0 targets=cpp,js,ts east3_opt_level=2` を確認した。
