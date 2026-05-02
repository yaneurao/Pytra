<a href="../../ja/plans/p2-top100-language-coverage.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p2-top100-language-coverage.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p2-top100-language-coverage.md`

# P2: Usage Top 100 Language Coverage Plan

## Purpose

Expand Pytra's backend / runtime / verification infrastructure so it can adapt to the top 100 programming languages by usage.
Here, "adapt" does not mean that every language must become a native backend at the same depth. Because each language has a different practical role, every language is tracked with one of the following target states.

- `backend`: Pytra can emit the target language and verify compile/run/parity.
- `host`: The target language can host part of Pytra's emitter/toolchain.
- `interop`: Pytra can interoperate with the target language's FFI, runtime, or generated artifacts.
- `syntax`: Pytra has syntax/type/module notes needed to decide whether a backend is appropriate.
- `defer`: The language requires a separate design before it can be handled as a normal text backend, such as Scratch / Ladder Logic / LabVIEW.

## Ranking Source

- Source: TIOBE Index for April 2026
- URL: https://www.tiobe.com/tiobe-index/
- Note: TIOBE is a popularity indicator based on search engines, courses, vendors, and similar signals. It is not a measure of language quality or lines of code. Pytra uses it as an external prioritization snapshot, while technical fit is evaluated separately.

## 2026-04 Snapshot

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

TIOBE publishes 51-100 alphabetically because differences in this tier are small. Pytra also treats them as a single tier instead of over-weighting exact rank order.

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

## Initial Classification

### Existing backend / target languages to strengthen

Python, C, C++, Java, C#, JavaScript, PHP, Go, Rust, Swift, Kotlin, Dart, Ruby, Lua, Julia, TypeScript, Zig, Scala, PowerShell, Nim

### P2 backend candidates to investigate

Visual Basic, R, Delphi/Object Pascal, Perl, Fortran, MATLAB, Ada, PL/SQL, Prolog, COBOL, SAS, Objective-C, Lisp, ML, Haskell, VBScript, ABAP, OCaml, Caml, Erlang, X++, Transact-SQL, Solidity, ActionScript, Apex, Applescript, Awk, Bash, Clojure, CoffeeScript, D, Elixir, F#, Groovy, Mojo, OpenCL, Tcl, V, Vala/Genie, VHDL, Wolfram

### Interop / DSL / non-standard backend design

SQL, Scratch, Assembly language, GML, LabVIEW, Ladder Logic, (Visual) FoxPro, Algol, bc, BCPL, Bourne shell, CFML, CL (OS/400), Curl, GAMS, Icon, Inform, Io, J, J#, JScript, JScript.NET, Logo, LotusScript, LPC, MQL5, NetLogo, PL/I, Pure Data, Q, REBOL, Ring, RPG, RPL, S, Small Basic, Smalltalk, Xojo

## Completion Criteria

1. `docs/ja/progress/top100-language-coverage.md` has a coverage matrix for all 100 languages.
2. Every language has a `backend` / `host` / `interop` / `syntax` / `defer` state.
3. Every `backend` language has at least one measured build/parity result.
4. Every `defer` language has a reason and unblocking condition.
5. New backends add profile / emitter / runtime mapping / smoke fixture / progress entry in the same task.

## Decision Log

- 2026-04-29: Adopted the TIOBE April 2026 top 100 as the initial snapshot. Coverage is managed by classifying all 100 languages into backend / host / interop / syntax / defer instead of making every language a native backend at once.
- 2026-05-03: Routed C++ plain builtin fallbacks back through runtime helpers and verified C++ parity for fixture `core/add`, sample `17_monte_carlo_pi`, and stdlib `math_extended` in the direct Dockerfile-run environment. A refreshed full sample sweep is now 7/18 PASS and 11 FAIL. Remaining blockers are artifact CRC drift, object type leakage, and plain `min` / `max` / `enumerate` fallback. The selfhost dry-run cpp row is `fixture_pass=1 fixture_fail=0 sample_pass=7 sample_fail=11`.
