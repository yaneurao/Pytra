<a href="../../en/plans/p2-top100-language-coverage.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P2: 使用上位 100 言語への適応計画

## 目的

Pytra の backend / runtime / 検証基盤を、使用上位 100 言語へ段階的に適応できる形へ広げる。
ここでの「適応」は、全言語を同じ深さで native backend 化する意味ではない。言語ごとに実用上の役割が異なるため、次のいずれかの到達状態を明示して管理する。

- `backend`: Pytra から対象言語へ emit し、compile/run/parity を確認できる。
- `host`: Pytra の emitter/toolchain の一部を対象言語で host できる。
- `interop`: 対象言語の外部関数、既存 runtime、または生成物と連携できる。
- `syntax`: 対象言語の構文・型・モジュール体系を調査し、backend 化判断に必要な仕様メモがある。
- `defer`: Scratch / Ladder Logic / LabVIEW など、通常の text backend として扱う前に別設計が必要なものとして保留理由を明記する。

## ランキング正本

- 出典: TIOBE Index for April 2026
- URL: https://www.tiobe.com/tiobe-index/
- 注意: TIOBE は「最良の言語」や「コード行数」ではなく、検索・教材・ベンダー等から算出した人気指標である。Pytra では優先度付けの外部スナップショットとして使い、技術的適性は別途判断する。

## 2026-04 スナップショット

### 1-50

1. Python
2. C
3. C++
4. Java
5. C#
6. JavaScript
7. Visual Basic
8. SQL
9. R
10. Delphi/Object Pascal
11. Scratch
12. Perl
13. Fortran
14. PHP
15. Go
16. Rust
17. MATLAB
18. Assembly language
19. Swift
20. Ada
21. PL/SQL
22. Prolog
23. COBOL
24. Kotlin
25. SAS
26. Classic Visual Basic
27. Objective-C
28. Dart
29. Ruby
30. Lua
31. Lisp
32. Julia
33. ML
34. TypeScript
35. Haskell
36. VBScript
37. ABAP
38. OCaml
39. Zig
40. Caml
41. Erlang
42. X++
43. Scala
44. Transact-SQL
45. PowerShell
46. GML
47. LabVIEW
48. Ladder Logic
49. Solidity
50. (Visual) FoxPro

### 51-100

TIOBE の 51-100 は差が小さいためアルファベット順で公表されている。Pytra 側でも順位差を細かく扱わず、同一 tier として管理する。

- ActionScript
- Algol
- Apex
- Applescript
- Awk
- Bash
- bc
- BCPL
- Bourne shell
- CFML
- CL (OS/400)
- Clojure
- CoffeeScript
- Curl
- D
- Elixir
- F#
- GAMS
- Groovy
- Icon
- Inform
- Io
- J
- J#
- JScript
- JScript.NET
- Logo
- LotusScript
- LPC
- Mojo
- MQL5
- NetLogo
- Nim
- OpenCL
- PL/I
- Pure Data
- Q
- REBOL
- Ring
- RPG
- RPL
- S
- Small Basic
- Smalltalk
- Tcl
- V
- Vala/Genie
- VHDL
- Wolfram
- Xojo

## 初期分類

### 既存 backend / target として継続強化するもの

Python, C, C++, Java, C#, JavaScript, PHP, Go, Rust, Swift, Kotlin, Dart, Ruby, Lua, Julia, TypeScript, Zig, Scala, PowerShell, Nim

### P2 で backend 候補として調査するもの

Visual Basic, R, Delphi/Object Pascal, Perl, Fortran, MATLAB, Ada, PL/SQL, Prolog, COBOL, SAS, Objective-C, Lisp, ML, Haskell, VBScript, ABAP, OCaml, Caml, Erlang, X++, Transact-SQL, Solidity, ActionScript, Apex, Applescript, Awk, Bash, Clojure, CoffeeScript, D, Elixir, F#, Groovy, Mojo, OpenCL, Tcl, V, Vala/Genie, VHDL, Wolfram

### interop / DSL / 非通常 backend として別設計にするもの

SQL, Scratch, Assembly language, GML, LabVIEW, Ladder Logic, (Visual) FoxPro, Algol, bc, BCPL, Bourne shell, CFML, CL (OS/400), Curl, GAMS, Icon, Inform, Io, J, J#, JScript, JScript.NET, Logo, LotusScript, LPC, MQL5, NetLogo, PL/I, Pure Data, Q, REBOL, Ring, RPG, RPL, S, Small Basic, Smalltalk, Xojo

## 完了条件

1. `docs/ja/progress/top100-language-coverage.md` に 100 言語分の coverage matrix がある。
2. 各言語に `backend` / `host` / `interop` / `syntax` / `defer` の状態が付いている。
3. `backend` 状態の言語には最低 1 件の build/parity 実測がある。
4. `defer` 状態の言語には保留理由と、解除条件がある。
5. 新規 backend を増やす場合は、profile / emitter / runtime mapping / smoke fixture / progress entry を同一タスクで追加する。
6. coverage 更新は `tools/gen/gen_top100_language_coverage.py --check` を Docker/devcontainer 内で通し、machine-readable JSON と Markdown が同期していることを確認する。

## 決定ログ

- 2026-04-29: TIOBE April 2026 top 100 を初期スナップショットとして採用。全 100 言語を一律 backend 化するのではなく、backend / host / interop / syntax / defer に分類して coverage を管理する。
- 2026-04-29: `.devcontainer/` と Dockerfile が未統合だった run では、Docker Desktop CLI (`/Applications/Docker.app/Contents/Resources/bin/docker`) と `python:3.12-slim` を使い、`tools.unittest.tooling.test_pytra_cli2`、`core/add.py --target dart/lua/php/zig/powershell`、Ruby focused fixture/stdlib/sample smoke を隔離実行した。devcontainer 追加後は `.devcontainer/scripts/verify-toolchain.sh` を優先する。
- 2026-04-30: 公式 TIOBE April 2026 を再確認し、`docs/ja/progress/top100-language-coverage.md` に 100 言語分の coverage matrix を追加した。Docker Desktop CLI で `.devcontainer/Dockerfile` を直接 build し、`verify-toolchain.sh`、runtime east 生成、Dart/Zig host emitter 生成、progress-preview 生成を実測した。Dart/Zig native CLI は devcontainer 未導入のため compile/parity の blocker として残す。
- 2026-04-30: [ID: P2-TOP100-LANG-S3/S4/S5/S6] `tools/gen/gen_top100_language_coverage.py` を追加し、Top100 coverage を Markdown と machine-readable JSON へ生成する導線にした。Top50 の未対応 syntax 候補には T1/T2/T3 の backend plan を付け、defer 言語には解除条件を付けた。Docker Desktop CLI は Engine / `hello-world` / `.devcontainer/Dockerfile` build / `verify-toolchain.sh` まで PASS。常設 `devcontainer` CLI は PATH に無かったため、Dockerfile 直接 run を標準 fallback とし、`--check` を coverage 更新ゲートに固定した。
- 2026-04-30: 同じ Dockerfile 直接 run で runtime east 32/32、Top100 generator + tuple host unit 10 tests、tools ledger、Dart/Zig C++ emitter host build smoke を確認した。代表 fixture/sample/stdlib は C++ runtime symbol drift で fail: `fixture add` は `::print` と `str(optional<variant...>)`、`sample 17_monte_carlo_pi` は `::print`、`stdlib math_extended` は `::int_` / `::print` / `str(optional<variant...>)`。`run_selfhost_parity.py --selfhost-lang python --emit-target cpp --dry-run` は cpp row `fixture_fail=1 sample_fail=18` を示したため、Top100 そのものは生成ゲート完了、次段 blocker は C++ runtime symbol drift として残す。
- 2026-05-03: C++ emitter の plain builtin fallback を runtime helper 経路へ戻し、Dockerfile 直接 run で `fixture core/add`、`sample 17_monte_carlo_pi`、`stdlib math_extended` の C++ parity PASS を確認した。続けて sample full sweep を再計測し、18件中 7 PASS / 11 FAIL を確認した。残 blocker は artifact CRC mismatch、object 型漏れ、`min` / `max` / `enumerate` の plain builtin drift。selfhost dry-run は cpp row `fixture_pass=1 fixture_fail=0 sample_pass=7 sample_fail=11`。
