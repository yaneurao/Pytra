<a href="../../en/progress/top100-language-coverage.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# Top100 言語 coverage matrix

最終更新: 2026-05-03

## Source snapshot

- 出典: TIOBE Index for April 2026
- URL: https://www.tiobe.com/tiobe-index/
- 取得日: 2026-04-30
- machine-readable catalog: `docs/ja/progress/top100-language-coverage.json`
- 位置付け: 外部の人気指標スナップショット。Pytra では優先度付けに使い、技術的適性は別途 `backend` / `host` / `interop` / `syntax` / `defer` で判断する。

## 今回の実測

- 仮想環境: Docker Desktop CLI (`/Applications/Docker.app/Contents/Resources/bin/docker`) で `.devcontainer/Dockerfile` を直接 build。`devcontainer` 常設 CLI は PATH 上に無かったため、グローバル導入せず Dockerfile 直接 run に fallback。
- Docker: `docker version` と `docker run --rm hello-world` は PASS。初回 build は `docker-credential-desktop` が PATH に無く失敗し、Docker Desktop 同梱 bin を PATH に追加して再実行 PASS。
- toolchain: `.devcontainer/scripts/verify-toolchain.sh` は PASS。Python 3.12 / pytest / C/C++ / Java / .NET / PowerShell / Ruby / Lua / PHP / Go / Rust を確認。Swift は optional 未導入。`dart` / `zig` CLI は未導入。
- runtime east: `PYTHONPATH=src python3 tools/gen/regenerate_runtime_east.py` は `runtime-east total: 32 ok, 0 failed`。
- unit/top100 generator: `python3 -m pytest -q tools/unittest/tooling/test_gen_top100_language_coverage.py tools/unittest/toolchain2/test_tuple_unpack_emitter_hosts.py` は 10 tests PASS。`python3 tools/gen/gen_top100_language_coverage.py --check` と `python3 tools/check/check_tools_ledger.py` も PASS。
- emitter-host: `python3 src/pytra-cli.py -build src/toolchain/emit/cpp/cli.py --target dart ...` は PASS（25 files）。`--target zig ...` も PASS（emitted 30 files、検証ディレクトリ内 file count 39）。native Dart/Zig CLI は devcontainer 未導入のため compile/parity は blocker として残す。
- fixture/sample/stdlib/selfhost: C++ plain builtin fallback を runtime helper 経路へ戻し、Docker 直接 run で `fixture core/add`、`sample 17_monte_carlo_pi`、`stdlib math_extended` の C++ parity が PASS。sample full sweep は 18件中 7 PASS / 11 FAIL。残 blocker は artifact CRC mismatch、object 型漏れ、`min` / `max` / `enumerate` の plain builtin drift。`run_selfhost_parity.py --selfhost-lang python --emit-target cpp --dry-run` は cpp row `fixture_pass=1 fixture_fail=0 sample_pass=7 sample_fail=11`。

## 分類ルール

- `backend`: Pytra target として emit でき、progress matrix へ接続する。
- `host`: Pytra toolchain / emitter の host として扱う。
- `interop`: 既存 runtime / ABI / query engine との接続対象にする。
- `syntax`: backend 化判断に必要な構文・型・module 調査を先に行う。
- `defer`: Scratch / Ladder Logic / LabVIEW など、通常の text backend として扱う前に別設計が必要なため、解除条件を待つ。

## 集計

- backend: 18
- host: 1
- interop: 6
- syntax: 43
- defer: 32

## Matrix

| rank | language | category | current status | last blocker | next action |
|---:|---|---|---|---|---|
| 1 | Python | host | reference parser/resolver/toolchain source | selfhost matrix は full pass ではない | selfhost rows を段階的に埋める |
| 2 | C | interop | C ABI / C-family runtime adjacency | native C backend は未定義 | C++ runtime との境界を棚卸しする |
| 3 | C++ | backend | primary backend; representative fixture/sample/stdlib PASS; sample 7/18 | full sample sweep 11 fail（artifact CRC / object 型漏れ / min・max・enumerate） | C++ sample blockers を型推定と builtin fallback で縮退する |
| 4 | Java | backend | target registered | host/parity は未完 | Java host parity を進める |
| 5 | C# | backend | target registered | host/parity は未完 | C# host parity を進める |
| 6 | JavaScript | backend | target registered | host/parity は未完 | JavaScript host parity を進める |
| 7 | Visual Basic | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 8 | SQL | interop | interop lane | native backend は未定義 | external runtime / ABI interop plan を作る |
| 9 | R | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 10 | Delphi/Object Pascal | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 11 | Scratch | defer | non-standard backend lane | 通常 text backend ではない | defer 理由と解除条件を固定する |
| 12 | Perl | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 13 | Fortran | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 14 | PHP | backend | target registered | host/parity は未完 | PHP host parity を進める |
| 15 | Go | backend | target registered; emitter-host PASS row あり | full selfhost 未完 | host parity JSON を増やす |
| 16 | Rust | backend | target registered | host/parity は未完 | Rust host parity を進める |
| 17 | MATLAB | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 18 | Assembly language | defer | non-standard backend lane | 通常 text backend ではない | defer 理由と解除条件を固定する |
| 19 | Swift | backend | target registered | Linux devcontainer では Swift 未導入 | optional Swift image/gate を検討する |
| 20 | Ada | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 21 | PL/SQL | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 22 | Prolog | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 23 | COBOL | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 24 | Kotlin | backend | target registered | host/parity は未完 | Kotlin host parity を進める |
| 25 | SAS | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 26 | Classic Visual Basic | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 27 | Objective-C | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 28 | Dart | backend | target registered; C++ emitter host 生成 PASS | devcontainer に `dart` CLI が無い | Dart CLI を隔離環境へ追加して compile/parity |
| 29 | Ruby | backend | target registered | host/parity は未完 | Ruby host parity を進める |
| 30 | Lua | backend | target registered | host/parity は未完 | Lua host parity を進める |
| 31 | Lisp | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 32 | Julia | backend | target registered | host/parity は未完 | Julia host parity を進める |
| 33 | ML | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 34 | TypeScript | backend | target registered; emitter-host PASS row あり | full selfhost 未完 | TS host parity を拡張する |
| 35 | Haskell | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 36 | VBScript | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 37 | ABAP | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 38 | OCaml | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 39 | Zig | backend | target registered; C++ emitter host 生成 PASS | devcontainer に `zig` CLI が無い | Zig CLI を隔離環境へ追加して compile/parity |
| 40 | Caml | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 41 | Erlang | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 42 | X++ | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 43 | Scala | backend | target registered | host/parity は未完 | Scala host parity を進める |
| 44 | Transact-SQL | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 45 | PowerShell | backend | target registered; devcontainer `pwsh` あり | host parity は未完 | PowerShell host parity を再実行する |
| 46 | GML | defer | non-standard backend lane | 通常 text backend ではない | defer 理由と解除条件を固定する |
| 47 | LabVIEW | defer | non-standard backend lane | 通常 text backend ではない | defer 理由と解除条件を固定する |
| 48 | Ladder Logic | defer | non-standard backend lane | 通常 text backend ではない | defer 理由と解除条件を固定する |
| 49 | Solidity | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 50 | (Visual) FoxPro | defer | non-standard backend lane | 通常 text backend ではない | defer 理由と解除条件を固定する |
| 51-100 | ActionScript | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 51-100 | Algol | defer | non-standard backend lane | 通常 text backend ではない | defer 理由と解除条件を固定する |
| 51-100 | Apex | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 51-100 | Applescript | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 51-100 | Awk | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 51-100 | Bash | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 51-100 | bc | defer | non-standard backend lane | 通常 text backend ではない | defer 理由と解除条件を固定する |
| 51-100 | BCPL | defer | non-standard backend lane | 通常 text backend ではない | defer 理由と解除条件を固定する |
| 51-100 | Bourne shell | interop | interop lane | native backend は未定義 | external runtime / ABI interop plan を作る |
| 51-100 | CFML | defer | non-standard backend lane | 通常 text backend ではない | defer 理由と解除条件を固定する |
| 51-100 | CL (OS/400) | defer | non-standard backend lane | 通常 text backend ではない | defer 理由と解除条件を固定する |
| 51-100 | Clojure | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 51-100 | CoffeeScript | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 51-100 | Curl | defer | non-standard backend lane | 通常 text backend ではない | defer 理由と解除条件を固定する |
| 51-100 | D | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 51-100 | Elixir | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 51-100 | F# | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 51-100 | GAMS | defer | non-standard backend lane | 通常 text backend ではない | defer 理由と解除条件を固定する |
| 51-100 | Groovy | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 51-100 | Icon | defer | non-standard backend lane | 通常 text backend ではない | defer 理由と解除条件を固定する |
| 51-100 | Inform | defer | non-standard backend lane | 通常 text backend ではない | defer 理由と解除条件を固定する |
| 51-100 | Io | defer | non-standard backend lane | 通常 text backend ではない | defer 理由と解除条件を固定する |
| 51-100 | J | defer | non-standard backend lane | 通常 text backend ではない | defer 理由と解除条件を固定する |
| 51-100 | J# | defer | non-standard backend lane | 通常 text backend ではない | defer 理由と解除条件を固定する |
| 51-100 | JScript | interop | interop lane | native backend は未定義 | external runtime / ABI interop plan を作る |
| 51-100 | JScript.NET | defer | non-standard backend lane | 通常 text backend ではない | defer 理由と解除条件を固定する |
| 51-100 | Logo | defer | non-standard backend lane | 通常 text backend ではない | defer 理由と解除条件を固定する |
| 51-100 | LotusScript | defer | non-standard backend lane | 通常 text backend ではない | defer 理由と解除条件を固定する |
| 51-100 | LPC | defer | non-standard backend lane | 通常 text backend ではない | defer 理由と解除条件を固定する |
| 51-100 | Mojo | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 51-100 | MQL5 | interop | interop lane | native backend は未定義 | external runtime / ABI interop plan を作る |
| 51-100 | NetLogo | defer | non-standard backend lane | 通常 text backend ではない | defer 理由と解除条件を固定する |
| 51-100 | Nim | backend | target registered | host/parity は未完 | Nim host parity を進める |
| 51-100 | OpenCL | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 51-100 | PL/I | defer | non-standard backend lane | 通常 text backend ではない | defer 理由と解除条件を固定する |
| 51-100 | Pure Data | defer | non-standard backend lane | 通常 text backend ではない | defer 理由と解除条件を固定する |
| 51-100 | Q | defer | non-standard backend lane | 通常 text backend ではない | defer 理由と解除条件を固定する |
| 51-100 | REBOL | defer | non-standard backend lane | 通常 text backend ではない | defer 理由と解除条件を固定する |
| 51-100 | Ring | defer | non-standard backend lane | 通常 text backend ではない | defer 理由と解除条件を固定する |
| 51-100 | RPG | defer | non-standard backend lane | 通常 text backend ではない | defer 理由と解除条件を固定する |
| 51-100 | RPL | defer | non-standard backend lane | 通常 text backend ではない | defer 理由と解除条件を固定する |
| 51-100 | S | interop | interop lane | native backend は未定義 | external runtime / ABI interop plan を作る |
| 51-100 | Small Basic | defer | non-standard backend lane | 通常 text backend ではない | defer 理由と解除条件を固定する |
| 51-100 | Smalltalk | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 51-100 | Tcl | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 51-100 | V | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 51-100 | Vala/Genie | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 51-100 | VHDL | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 51-100 | Wolfram | syntax | backend candidate | runtime / type / module semantics 未調査 | syntax smoke と最小 compile/run gate を調査する |
| 51-100 | Xojo | defer | non-standard backend lane | 通常 text backend ではない | defer 理由と解除条件を固定する |

## Top50 未対応候補 backend plan

T1 は次回以降の syntax smoke / profile 調査を優先する候補、T2 は toolchain 入手性や runtime 形状を先に見る候補、T3 は proprietary / DSL / semantics 差分が大きく通常 backend 化の前に境界判断が必要な候補です。

| tier | language | plan | blocker |
|---|---|---|---|
| T1 | Visual Basic | VB.NET を .NET backend family として扱い、Classic VB は別行で保留条件を持たせる | runtime / type / module semantics 未調査 |
| T1 | R | numeric/vector semantics を syntax smoke として固定し、Python numeric subset との距離を測る | runtime / type / module semantics 未調査 |
| T2 | Delphi/Object Pascal | Pascal family profile と Free Pascal toolchain smoke を先に確認する | runtime / type / module semantics 未調査 |
| T1 | Perl | scalar/list/hash context の制限 subset を定め、script backend 候補にする | runtime / type / module semantics 未調査 |
| T2 | Fortran | numeric/array subset と gfortran compile smoke を確認する | runtime / type / module semantics 未調査 |
| T3 | MATLAB | Octave 互換 subset を先に調査し、proprietary runtime 依存を避ける | runtime / type / module semantics 未調査 |
| T2 | Ada | GNAT availability と strong typing mapping を確認する | runtime / type / module semantics 未調査 |
| T3 | PL/SQL | SQL interop lane と接続し、DB runtime 前提を backend 非依存に分離する | runtime / type / module semantics 未調査 |
| T3 | Prolog | unification/control model が Pytra subset と合うか syntax 調査に留める | runtime / type / module semantics 未調査 |
| T3 | COBOL | data division と compile smoke の入手性を先に確認する | runtime / type / module semantics 未調査 |
| T3 | SAS | proprietary runtime 前提のため open substitute の有無を確認する | runtime / type / module semantics 未調査 |
| T3 | Classic Visual Basic | Visual Basic から分離し、legacy runtime 入手性を blocker として固定する | runtime / type / module semantics 未調査 |
| T2 | Objective-C | C/Swift interop と ObjC runtime 方針を比較する | runtime / type / module semantics 未調査 |
| T2 | Lisp | Common Lisp / Scheme を分離し、方言選定から始める | runtime / type / module semantics 未調査 |
| T2 | ML | OCaml/SML との重複を整理する | runtime / type / module semantics 未調査 |
| T3 | Haskell | lazy semantics を避ける strict subset 可否を調査する | runtime / type / module semantics 未調査 |
| T3 | VBScript | Windows Script Host 前提を syntax/defer 境界として確認する | runtime / type / module semantics 未調査 |
| T3 | ABAP | proprietary runtime 前提のため interop/defer 降格条件を定める | runtime / type / module semantics 未調査 |
| T1 | OCaml | OCaml profile 調査を ML family の代表として先行する | runtime / type / module semantics 未調査 |
| T3 | Caml | OCaml row へ統合できるか確認する | runtime / type / module semantics 未調査 |
| T2 | Erlang | BEAM lane と actor/runtime model を調査する | runtime / type / module semantics 未調査 |
| T3 | X++ | proprietary runtime 前提を blocker として固定する | runtime / type / module semantics 未調査 |
| T3 | Transact-SQL | SQL interop lane と接続し、DB runtime 前提を分離する | runtime / type / module semantics 未調査 |
| T2 | Solidity | EVM/security semantics を通常 backend と分けて調査する | runtime / type / module semantics 未調査 |

## defer 条件

| language | defer condition | unblock condition |
|---|---|---|
| Scratch | visual/block DSL のため、text IR から block model へ変換する中間 DSL が必要 | defer 理由と解除条件を固定する |
| Assembly language | ISA 固有で一括 backend 不可。LLVM/WASM 等の低レベル lane へ分離後に再評価 | defer 理由と解除条件を固定する |
| GML | GameMaker runtime 前提。engine API interop plan ができるまで defer | defer 理由と解除条件を固定する |
| LabVIEW | visual/dataflow DSL。model exchange format の調査が先 | defer 理由と解除条件を固定する |
| Ladder Logic | PLC/safety runtime 前提。対象 PLC と検証責任範囲の定義が先 | defer 理由と解除条件を固定する |
| (Visual) FoxPro | legacy/proprietary runtime の入手性が低く、preserve/defer 理由を固定 | defer 理由と解除条件を固定する |
| Algol | historical language で実用 toolchain 目的が薄い | defer 理由と解除条件を固定する |
| bc | calculator DSL として narrow domain。通常 backend より helper/interop 扱い | defer 理由と解除条件を固定する |
| BCPL | historical language で実用 toolchain 目的が薄い | defer 理由と解除条件を固定する |
| CFML | server/runtime DSL。ColdFusion 互換 runtime 前提を分離 | defer 理由と解除条件を固定する |
| CL (OS/400) | IBM i platform-specific lane。通常 backend と別設計 | defer 理由と解除条件を固定する |
| Curl | niche/runtime 前提で toolchain 入手性が blocker | defer 理由と解除条件を固定する |
| GAMS | optimization DSL。solver/runtime interop が先 | defer 理由と解除条件を固定する |
| Icon | niche language で toolchain 入手性が blocker | defer 理由と解除条件を固定する |
| Inform | interactive fiction DSL。domain-specific transform 条件が先 | defer 理由と解除条件を固定する |
| Io | niche language で toolchain 入手性が blocker | defer 理由と解除条件を固定する |
| J | array language で semantics 差分が大きく、APL family 調査が先 | defer 理由と解除条件を固定する |
| J# | obsolete .NET language。supported runtime 不明 | defer 理由と解除条件を固定する |
| JScript.NET | obsolete .NET language。supported runtime 不明 | defer 理由と解除条件を固定する |
| Logo | education DSL。text backend 優先度が低い | defer 理由と解除条件を固定する |
| LotusScript | Domino runtime 前提の platform-specific lane | defer 理由と解除条件を固定する |
| LPC | MUD/domain runtime 前提で通常 backend と別設計 | defer 理由と解除条件を固定する |
| NetLogo | agent-based DSL。domain-specific transform 条件が先 | defer 理由と解除条件を固定する |
| PL/I | legacy language で実用 toolchain 目的が薄い | defer 理由と解除条件を固定する |
| Pure Data | visual/dataflow DSL。model exchange 条件が先 | defer 理由と解除条件を固定する |
| Q | kdb+ runtime 前提。proprietary/runtime-specific lane | defer 理由と解除条件を固定する |
| REBOL | niche language で toolchain 入手性が blocker | defer 理由と解除条件を固定する |
| Ring | niche language で toolchain 入手性が blocker | defer 理由と解除条件を固定する |
| RPG | IBM i platform-specific lane | defer 理由と解除条件を固定する |
| RPL | calculator/platform DSL。narrow runtime | defer 理由と解除条件を固定する |
| Small Basic | education/runtime-specific lane。Visual Basic family との関係整理が先 | defer 理由と解除条件を固定する |
| Xojo | proprietary IDE/runtime。text backend 優先度が低い | defer 理由と解除条件を固定する |

## Docker/devcontainer 標準ゲート

Top100 coverage を更新する run は、次の順で Docker/devcontainer gate を通す。Docker が使えない場合は coverage を完了扱いにせず、exact blocker と再開条件だけを残す。

1. `docker version` と `docker run --rm hello-world` で Engine と container start を確認する。
2. `devcontainer` 常設 CLI があれば `.devcontainer/` を起動する。無い場合は Docker Desktop 同梱 bin を PATH に足して `.devcontainer/Dockerfile` を直接 build/run する。
3. コンテナ内で `.devcontainer/scripts/verify-toolchain.sh`、`tools/gen/regenerate_runtime_east.py`、`tools/gen/gen_top100_language_coverage.py --check` を実行する。
4. 代表 fixture / sample / stdlib / emitter-host / selfhost の実測コマンドを残し、未導入 runtime は blocker として matrix に戻す。

## 次アクション

1. Dart / Zig CLI を devcontainer に追加するか、別 image として分離し、今回 PASS した host 生成物を compile/parity まで進める。
2. C++ sample の残 blocker（artifact CRC、object 型漏れ、`min` / `max` / `enumerate` fallback）を縮退し、selfhost cpp row を PASS 側へ寄せる。
3. T1 backend plan（Visual Basic / R / Perl / OCaml）から syntax smoke を作り、top100 matrix の `syntax` を実測つきに更新する。
