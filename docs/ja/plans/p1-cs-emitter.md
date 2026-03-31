<a href="../../en/plans/p1-cs-emitter.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1-CS-EMITTER: C# emitter を toolchain2 に新規実装する

最終更新: 2026-03-31
ステータス: 進行中（S3/S4/S5 完了、S6 未着手）

## 背景

C# は Unity や .NET エコシステムで広く使われており、Pytra のターゲット言語としてユーザー需要が高い。旧 toolchain1 に C# emitter（`src/toolchain/emit/cs/`）と runtime（`src/runtime/cs/`）が存在するが、toolchain2 の新パイプラインに移行する必要がある。

## 設計

### emitter 構成

- `src/toolchain2/emit/cs/` に CommonRenderer + override 構成で実装
- 旧 `src/toolchain/emit/cs/` と TS emitter（`src/toolchain2/emit/ts/`）を参考にする
- C# 固有のノード（namespace、using、property、LINQ、nullable 型等）だけ override

### mapping.json

`src/runtime/cs/mapping.json` に以下を定義:
- `calls`: runtime_call の写像
- `types`: EAST3 型名 → C# 型名（`int64` → `long`, `float64` → `double`, `str` → `string`, `Exception` → `Exception` 等）
- `env.target`: `"\"cs\""`
- `builtin_prefix`: `"py_"`
- `implicit_promotions`: C# の暗黙昇格ペア（C++ とほぼ同じ）

### parity check

- `pytra-cli2 -build --target cs` の emit 経路まで対応済み。compile + run parity は未着手。
- `runtime_parity_check_fast.py --targets cs` で検証
- fixture + sample + stdlib の3段階

## 決定ログ

- 2026-03-30: C# backend 担当を新設。emitter guide に従い toolchain2 emitter を実装する方針。
- 2026-03-30: `src/toolchain2/emit/cs/` を新設し、`emit_cs_module()` / `types.py` / `toolchain2/emit/profiles/cs.json` を追加。`src/runtime/cs/mapping.json` を作成し、`pytra-cli2 --target cs` の emit/build 経路を toolchain2 emitter へ接続した。
- 2026-03-30: emitter guide §13 に合わせ、C# 独自 checker は撤回し `tools/check/runtime_parity_check_fast.py` を正本経路として採用した。`PYTHONPATH=src:tools/check python3 tools/check/runtime_parity_check_fast.py --targets cs --category core` は 22/22 pass。
- 2026-03-30: C# emitter/runtime を `collections` / `control` 向けに拡張した。container method lowering、Python 互換の `and` / `or`、membership、slice、list repeat、comprehension、try/finally、nested closure、exception 表示を実装し、`PYTHONPATH=src:tools/check python3 tools/check/runtime_parity_check_fast.py --targets cs --category collections` は 20/20 pass、`--category control` は 16/16 pass。
- 2026-03-30: C# emitter を `imports` / `oop` 向けに拡張した。runtime import binding の C# 専用解決、module attr lowering、`bytes` / `bytearray` ctor・mutation、trait → interface 出力、`@staticmethod`、dataclass ctor 生成、linked EAST3 の `pytra_isinstance` / `ObjTypeId` 呼び出し描画、`super().method()`、`virtual` / `override` を実装し、`PYTHONPATH=src:tools/check python3 tools/check/runtime_parity_check_fast.py --targets cs --category imports` は 7/7 pass、`--category oop` は 18/18 pass を確認した。一方で fixture 全件は未達で、同日確認時点の残差は `--category signature` 5/13 pass、`--category strings` 6/12 pass、`--category typing` 8/23 pass。
- 2026-03-30: C# emitter/runtime を `strings` / `signature` 向けに追加修正した。`VarDecl`、hoisted loop target、tuple target comprehension、list concat、mixed-type equality、`yields_dynamic` / `Unbox` の cast、`type(v).__name__`、string iteration、`sum` / `zip` / `enumerate` / `reversed` / `index` / `strip` / `rstrip` / `startswith` / `endswith` / `replace` helper、sequence 表示を追加し、`PYTHONPATH=src:tools/check python3 tools/check/runtime_parity_check_fast.py --targets cs --category strings` は 12/12 pass まで改善した。残差は `--category signature` 8/13 pass、`--category typing` 8/23 pass。
- 2026-03-30: C# emitter/runtime を `signature` / `typing` / remaining fixture 向けに追加修正した。format spec f-string、`Swap`、typed varargs、linked EAST3 `pytra_isinstance` の素直な描画、`JsonVal` narrowing cast、type-id constant 解決、user-defined class type registration、POD exact `isinstance`、`Any` dict boxing、subscript assignment、small integer promotion cast、`deque` runtime を追加し、`PYTHONPATH=src:tools/check python3 tools/check/runtime_parity_check_fast.py --targets cs --category signature` は 13/13 pass、`--category typing` は 23/23 pass を確認した。full fixture sweep は 131 cases 中 130 pass + `import_time_from` の runtime copy 一時エラー 1 件で、同ケース単体再実行と `--category imports` は pass した。
- 2026-03-31: stash 退行で失われた C# 修正を `src/toolchain2/emit/cs/emitter.py` / `src/runtime/cs/` に再適用した。linked EAST3 の `pytra_isinstance`、`type_id_resolved_v1`、`yields_dynamic`、enum 定数群、Python `/` と `//`、sample 向け `min` / `max`、range 負 step、subscript swap を復旧し、`PYTHONPATH=src:tools/check python3 tools/check/runtime_parity_check_fast.py --targets cs` は fixture 131/131 pass まで到達した。
- 2026-03-31: sample parity を継続し、`pytra.std.pathlib` の `typing.cast` が `build_import_alias_map()` 経由で `Typing.cast(...)` に誤 lower される経路を修正した。C# emitter で Name call の `cast` を import alias 判定より先に no-op cast として描画するようにし、sample 18 件を個別 sweep して 18/18 pass を確認した。
- 2026-04-01: `P2-CS-LINT-S1` と並行して C# parity checker の実行経路を見直し、`tools/check/runtime_parity_check_fast.py` に `dotnet` fallback、`tools/check/runtime_parity_check.py` に C# 用 `can_run()` fallback を追加した。これにより `--case-root stdlib --targets cs` が `missing toolchain` ではなく実行され、16 cases 中 10 pass / 6 fail（`json_indent_optional`, `math_extended`, `math_path_runtime_ir`, `path_stringify`, `pathlib_extended`, `re_extended`）まで前進した。
