# P5 PowerShell Host Profile For C# Backend

最終更新: 2026-03-12

目的:
- PowerShell を新しい backend として実装する代わりに、既存の C# backend を PowerShell から起動する host profile を定義する。
- `py2cs` が生成する `.cs` と runtime 同梱物を、`pwsh` から build / run できる representative 導線にまとめる。
- Windows / PowerShell 7 / .NET 系 toolchain を前提に、`pure PowerShell backend` より低コストな実行経路を確立する。

背景:
- 現在の C# backend は [CSharpEmitter](/workspace/Pytra/src/backends/cs/emitter/cs_emitter.py) と smoke / selfhost 導線を見る限り、Mono `mcs` 互換を強く意識した保守的な C# surface を出力している。
- そのため、PowerShell backend をゼロから実装するより、PowerShell から C# を compile / load / run する host profile を整えるほうが現実的である。
- Pytra-NES のような bit 演算・class・bytes・file I/O を含むコードは pure PowerShell より C# と相性が良く、`pwsh launcher + cs backend` の方が実用性が高い。
- 一方で、runtime 同梱、複数 `.cs` ファイルの compile 導線、`dotnet` / `csc` / `Add-Type` fallback、`Main` entrypoint 契約は未整備である。

非対象:
- PowerShell を target language とする pure backend 実装。
- C# backend 自体の全面 rewrite。
- PowerShell 5.1 と 7.x の完全互換保証。
- 非 Windows 環境での PowerShell host 動作保証。

受け入れ基準:
- `pwsh + cs backend` の代表構成と前提 toolchain（`pwsh`, `dotnet` or `csc`）が plan で固定されている。
- runtime 同梱物、generated `.cs`、entrypoint `Main`、launcher `.ps1` の責務分担が明文化されている。
- build driver 候補（`dotnet build/run`, `csc`, `Add-Type`）の優先順と fail-closed 条件が決まっている。
- smoke / parity / docs の representative regression 点が決まっている。
- `docs/en/` mirror が日本語版と同じ計画内容に追従している。

確認コマンド:
- `python3 tools/check_powershell_cs_host_contract.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_powershell_cs_host_contract.py'`
- `python3 tools/check_todo_priority.py`
- `git diff --check`

## 子タスク

- [x] [ID: P5-POWERSHELL-CS-HOST-01-S1-01] `pwsh + cs backend` representative lane の前提（Windows / PowerShell 7 / `dotnet` or `csc`）と非対象を固定する。
- [ ] [ID: P5-POWERSHELL-CS-HOST-01-S2-01] launcher `.ps1` の責務を定義し、generated `.cs` / runtime `.cs` / output layout / `Main` entrypoint 契約を決める。
- [ ] [ID: P5-POWERSHELL-CS-HOST-01-S2-02] build driver の優先順（`dotnet`, `csc`, `Add-Type`）と fail-closed 条件を整理する。
- [ ] [ID: P5-POWERSHELL-CS-HOST-01-S3-01] representative smoke / sample parity / CLI profile の導線を設計し、既存 `py2cs` smoke との差分を明示する。
- [ ] [ID: P5-POWERSHELL-CS-HOST-01-S4-01] docs / how-to-use / user caveat を整理し、PowerShell host profile を後段 TODO へ積める状態にする。

## 決定ログ

- 2026-03-12: `pure PowerShell backend` は bit 演算、bytes、class、module/runtime packaging の言語相性が悪くコストが高いため、この plan は `PowerShell host for C# backend` に限定する。
- 2026-03-12: 優先度は低く、実験用 host profile の性格が強いため `P5` とする。
- 2026-03-12: `S1-01` として `pwsh / Windows / PowerShell 7 / dotnet-or-csc required / Add-Type optional` を canonical baseline に固定し、docs drift は `check_powershell_cs_host_contract.py` で落とす。
