<a href="../../ja/plans/p1-pipeline-stage-separation.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p1-pipeline-stage-separation.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p1-pipeline-stage-separation.md`

# P1: パイプライン段分離 — compile / link / emit の独立化

最終更新: 2026-03-21

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-PIPELINE-STAGE-SEPARATION-01`

## 背景

現在の `pytra-cli.py` は compile → link → optimize → emit を 1 プロセスで実行し、モジュールレベルで全 backend emitter を import する。このため：

1. **EAST3 生成に emitter が不要なのに、emitter が import グラフに入る。** compile/link/optimize はターゲット言語に依存しないにもかかわらず、`backend_registry_static.py` が全 emitter を静的 import している。
2. **selfhost multi-module transpile で 151 モジュールの emit に 45 分以上かかる。** 本来 selfhost に不要な Rust/C#/Go 等の emitter が import グラフに含まれ、全て emit 対象になる。
3. **gcc/ld のような段分離がない。** gcc は `cc1`（コンパイラ）と `ld`（リンカ）が独立プロセスであり、`ld` は `cc1` に依存しない。Pytra も同様の責務分離が必要。

## 設計

### あるべきパイプライン構造

```
コンパイラ (backend 非依存)
  pytra compile  : .py → .east         ← emitter に一切依存しない
  pytra link     : .east* → linked.east ← emitter に一切依存しない

Backend (言語ごとに独立した実行単位)
  east2cpp       : linked.east → .cpp   ← CppEmitter のみ import
  east2rs        : linked.east → .rs    ← RsEmitter のみ import
  east2cs        : linked.east → .cs    ← CsEmitter のみ import
  ...

ビルドオーケストレータ
  pytra build    : .py → .exe          ← compile + link + east2cpp + g++ をサブプロセスで連鎖
```

### 実装方針

1. `src/east2cpp.py` を新設: linked EAST JSON を入力として C++ multi-file 出力を生成する。CppEmitter 関連のみ import する。
2. `pytra-cli.py --build` を `east2cpp.py` をサブプロセスで呼ぶ形に変更。
3. `build_selfhost.py --multi-module` を 3 段パイプラインに分離:
   - `pytra-cli.py compile` → `.east` 群を生成
   - `pytra-cli.py link` → `linked.east` を生成（`--link-only`）
   - `east2cpp.py` → C++ 出力を生成
4. `pytra-cli.py` の一気通貫パスは当面残すが、`east2cpp.py` が正規パスになった後に段階廃止を検討。

### east2cpp.py の入力/出力

- **入力**: `link-output.json`（linked program manifest）または linked EAST3 JSON
- **出力**: `--output-dir` で指定したディレクトリに multi-file C++ を生成
- **依存**: `toolchain.emit.cpp.emitter` + `toolchain.emit.cpp.optimizer` + `toolchain.emit.cpp.program_writer` のみ。`toolchain.frontends` / `toolchain.compile` / 他言語 backend は import しない。

## 対象

- `src/east2cpp.py`（新設）
- `src/pytra-cli.py`（east2cpp.py をサブプロセスで呼ぶ形に変更）
- `tools/build_selfhost.py`（3 段パイプラインに分離）
- `src/pytra-cli.py`（`--link-only` 出力を east2cpp 入力に接続する導線追加）

## 非対象

- `pytra-cli.py` の廃止（本タスクでは残存を許容、段階廃止は後続タスク）
- 非 C++ backend の `east2xxx.py` 作成（C++ が安定した後に個別対応）
- `east2x.py` のリファクタ（本タスクでは変更しない）

## 受け入れ基準

- [ ] `east2cpp.py` が linked EAST JSON を入力として C++ multi-file 出力を生成できる。
- [ ] `east2cpp.py` の import グラフに非 C++ backend emitter が含まれない。
- [ ] `pytra build main.py -o app.out` が compile → link → east2cpp → g++ で実行ファイルを生成できる。
- [ ] `build_selfhost.py --multi-module` が 3 段パイプライン（compile → link → east2cpp）で動作し、emit 段階のモジュール数が大幅に削減される。
- [ ] 既存の `python3 src/pytra-cli.py` 一気通貫パスが壊れない（後方互換）。

## 子タスク

- [ ] [ID: P1-PIPELINE-STAGE-SEPARATION-01-S1] `east2cpp.py` を新設し、linked EAST JSON → C++ multi-file emit を実装する。
- [ ] [ID: P1-PIPELINE-STAGE-SEPARATION-01-S2] `pytra-cli.py` に `--link-only` 出力と `east2cpp.py` 入力を接続する導線を整備する。
- [ ] [ID: P1-PIPELINE-STAGE-SEPARATION-01-S3] `pytra-cli.py --build` を east2cpp.py サブプロセス呼び出しに変更する。
- [ ] [ID: P1-PIPELINE-STAGE-SEPARATION-01-S4] `build_selfhost.py --multi-module` を 3 段パイプラインに分離し、emit 段階のモジュール数削減を検証する。

## 決定ログ

- 2026-03-21: EAST3 生成に emitter が不要であるにもかかわらず `pytra-cli.py` が全 emitter を import している設計問題を特定。gcc/ld のアナロジーに基づき、compile/link/emit を独立した実行単位に分離する方針を決定。各言語 backend は `east2xxx.py` として独立させ、`pytra build` がオーケストレータとしてサブプロセスで連鎖する構造を採用。
