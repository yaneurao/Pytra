# P0: linked program 導入（multi-unit optimizer + ProgramWriter 分離）

最終更新: 2026-03-07

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-LINKED-PROGRAM-OPT-01`

背景:
- 現状の `EAST3 optimizer` は入力として単一 `Module` を受ける。`rc<>` や container ownership のような「複数翻訳単位をまとめて見ないと正しく最適化できない情報」を、単一入力のまま厳密に扱うことはできない。
- 現行の `NonEscapeInterproceduralPass` は import closure を内部で追加読み込みして summary を作るが、これは whole-program optimizer ではなく、単一 module 起点の補助解析にとどまる。
- C++ の multi-file 出力は既に `CppEmitter` 本体から [multifile_writer.py](../../../src/backends/cpp/emitter/multifile_writer.py) へ分離されており、この方向は正しい。一方で、今後 multi-unit optimizer を導入するなら、各言語 emitter 本体に「複数ファイル配置」「manifest 生成」「runtime 配置」まで背負わせるのは避けるべきである。
- `spec-linker.md` には `EAST3 -> linker -> backend` の責務分離がすでに書かれているが、実装はまだその契約に追いついていない。

目的:
- `rc<>` / container ownership / escape / alias / `type_id` などの program-wide 情報を、単一 module optimizer ではなく linked program 段で決定する。
- `ModuleEmitter` は「1 module を描画するだけ」に縮退させ、複数ファイル出力・manifest 生成・runtime 配置・build metadata 生成は `ProgramWriter` に分離する。
- `EAST3 local optimizer` と `linked program global optimizer` の責務境界を明文化し、将来の backend 追加でも emitter 本体の肥大化を防ぐ。
- `py2x.py` / `ir2lang.py` / `pytra-cli.py` の導線を壊さずに、in-memory 高速経路と dump/restart/debug 経路の両方で同じ責務境界を保てるようにする。

対象:
- 追加: linked program 入出力 schema
- 追加: `EAST3` 複数翻訳単位を束ねる manifest / loader / validator
- 追加: multi-unit optimizer（初期対象は `rc<>` / non-escape / container ownership / `type_id` 関連）
- 追加: backend 共通 `ProgramWriter` 契約
- 移設: C++ multi-file 出力責務を `ProgramWriter` として再定義
- 更新: `py2x.py`, `ir2lang.py`, `pytra-cli.py`, `backend_registry.py`, `spec-linker.md`, `spec-east.md`, `spec-dev.md`, `spec-make.md`

非対象:
- register allocation / inlining / DCE などの機械語寄り最適化
- ネイティブバイナリリンカ (`ld` / `link.exe`) の代替
- すべての backend を同時に multi-file 出力へ移行すること
- `EAST1/EAST2/EAST3` の schema 名称変更（`pyast/hir/lir` への改名は本計画では扱わない）
- runtime API の全面刷新

受け入れ基準:
- global optimization の入力は単一 `Module` ではなく、複数翻訳単位を含む linked program になる。
- `rc<>` / list ownership の whole-program 判断は `EAST3 local optimizer` ではなく linked program 段で行われる。
- `NonEscapeInterproceduralPass` の import-closure 内部読込は撤去または縮退し、program loader / linker が供給する module 集合を前提に動く。
- backend の module emitter は `1 module -> source text` に限定され、複数ファイル配置・manifest・runtime 配置を直接担当しない。
- C++ multi-file 出力は `ProgramWriter` 契約へ移行し、既存の `manifest.json` / `Makefile` 導線は非退行で維持される。
- `ir2lang.py` または等価 backend-only 導線から、single-module 入力と linked-program 入力の両方を受理できる。
- `sample` / `fixture` / representative unit test において、global optimizer 有効時と debug/restart 経路で意味論差分が出ない。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 -m unittest discover -s test/unit/link -p 'test_*.py' -v`
- `python3 -m unittest discover -s test/unit/backends/cpp -p 'test_*.py' -v`
- `python3 src/py2x.py sample/py/18_mini_language_interpreter.py --target cpp --dump-east3-dir out/east3`
- `python3 src/eastlink.py out/east3/link-input.json --output-dir out/linked`
- `python3 src/ir2lang.py out/linked/link-output.json --target cpp --output-dir out/cpp`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root sample --all-samples`

## 1. 問題の本質

現状の問題は 2 つに分かれる。

1. global optimization の入力単位が間違っている  
   - `EAST3 optimizer` は単一 `Module` を入力とする。  
   - import closure を内部で追加読込しても、これは「module-rooted analysis」であり、明示的に複数翻訳単位を集めた deterministic な whole-program optimizer ではない。  
   - その結果、`rc<>` / alias / escape / ownership の決定責務が曖昧になる。

2. multi-file 出力責務の置き場所を誤ると emitter が肥大化する  
   - `ModuleEmitter` に「どのファイルへ置くか」「依存 module の forward declaration をどう置くか」「runtime をどこへコピーするか」まで持たせると、各言語 backend が肥大化する。  
   - 逆に `ProgramWriter` を別層に置けば、`ModuleEmitter` は 1 module を描画するだけで済む。  
   - C++ の現行 `multifile_writer.py` は、この方向へ半歩進んでいるが、まだ C++ 専用 utility のままで backend 共通契約になっていない。

この 2 つは別問題に見えるが、実際には連動している。  
global optimizer が複数翻訳単位をまとめるなら、その結果をどの backend がどの単位で受けるかも定義しないといけない。  
したがって本計画では `linked program` を中心概念として、optimizer と writer を同時に再設計する。

## 2. 目標アーキテクチャ

### 2.1 目標パイプライン

```text
Source(.py)
  -> EAST1 (per translation unit)
  -> EAST2 (per translation unit)
  -> EAST3 Module (per translation unit)
  -> LinkedProgramLoader (collect modules)
  -> LinkedProgramOptimizer / Linker (whole program)
  -> BackendLower/Optimize (per module, target-specific)
  -> ModuleEmitter (per module)
  -> ProgramWriter (per target/program)
  -> build manifest / runtime / output tree
```

### 2.2 責務境界

| 層 | 入力 | 出力 | 責務 | 禁止事項 |
| --- | --- | --- | --- | --- |
| `EAST3 local optimizer` | 単一 `Module` | 単一 `Module` | 局所 canonicalization、局所 simplification、式/loop 正規化 | whole-program alias/escape 決定、他 module 読込 |
| `LinkedProgramLoader` | 複数 `Module` path / manifest | `LinkedProgram` | module 集合の読込・検証・正規化 | 最適化判断、target 固有描画 |
| `LinkedProgramOptimizer` | `LinkedProgram` | 注釈付き `LinkedProgram` | whole-program summary、`type_id`、global escape/ownership | source text 生成、runtime 配置 |
| `ModuleEmitter` | 1 module + global annotation view | source text / module artifact | module 単位の target code 描画 | 複数ファイル配置、runtime copy、build manifest 生成 |
| `ProgramWriter` | program 内 module artifact 群 | 出力 tree / manifest | path layout、manifest、runtime、build metadata | module-level 意味論再判断 |

### 2.3 基本方針

- correctness を決める global 判定は `LinkedProgramOptimizer` へ寄せる。
- `ModuleEmitter` は global summary を読むことは許可するが、再計算はしない。
- `ProgramWriter` は layout / packaging / manifest のみを担当し、意味論は扱わない。
- single-file backend でも `ProgramWriter` は存在する。ただしデフォルト実装は trivial でよい。

## 3. 入力仕様（linked program）

### 3.1 入力の最小単位

global optimizer の最小入力は「複数翻訳単位を束ねた manifest」であり、単一 `Module` ではない。

この manifest を仮に `link-input.json` と呼ぶ。

### 3.2 `link-input.json` v1（案）

```json
{
  "schema": "pytra.link_input.v1",
  "target": "cpp",
  "dispatch_mode": "native",
  "entry_modules": ["app.main"],
  "modules": [
    {
      "module_id": "app.main",
      "path": "build/east3/app.main.east3.json",
      "source_path": "sample/py/18_mini_language_interpreter.py",
      "is_entry": true
    },
    {
      "module_id": "pytra.std.json",
      "path": "build/east3/pytra.std.json.east3.json",
      "source_path": "src/pytra/std/json.py",
      "is_entry": false
    }
  ],
  "options": {
    "cpp_list_model": "pyobj",
    "east3_opt_level": 1
  }
}
```

### 3.3 必須項目

- `schema`
  - 文字列。`pytra.link_input.v1` 固定。
- `target`
  - backend target。`cpp`, `rs`, `js` など。
- `dispatch_mode`
  - `native | type_id`
  - 全 module で一致していなければ fail-fast。
- `entry_modules`
  - program の entry module 一覧。
- `modules`
  - 各 module の `module_id`, `path`, `source_path`, `is_entry`。

### 3.4 バリデーション

- 同一 `module_id` 重複禁止。
- `path` 未存在は `input_invalid(stage=link, kind=invalid_link_input)`。
- `east_stage != 3` は fail-fast。
- `target` と `dispatch_mode` の program-wide 一貫性を検証する。
- module の読み込み順は `module_id` 辞書順に固定し、決定性を保つ。
- manifest 内の path 文字列は manifest 配置ディレクトリ基準の POSIX 相対パスを canonical form とする。

## 4. 出力仕様（linked program result）

### 4.1 出力は 1 本の巨大 IR ではなく「program manifest + module ごとの最適化済み IR」

本計画では、global optimizer の出力を 1 本の mega-IR にはしない。  
理由は次のとおり。

- backend / emitter は翻訳単位単位で描画した方が自然。
- sample / debug / diff が見やすい。
- 既存の C++ multi-file / manifest / build 導線と整合する。

### 4.2 `link-output.json` v1（案）

```json
{
  "schema": "pytra.link_output.v1",
  "target": "cpp",
  "dispatch_mode": "native",
  "entry_modules": ["app.main"],
  "modules": [
    {
      "module_id": "app.main",
      "input": "build/east3/app.main.east3.json",
      "output": "build/linked/app.main.east3.json"
    },
    {
      "module_id": "pytra.std.json",
      "input": "build/east3/pytra.std.json.east3.json",
      "output": "build/linked/pytra.std.json.east3.json"
    }
  ],
  "global": {
    "type_id_table": {
      "app.ExprNode": 1000,
      "app.StmtNode": 1001
    },
    "call_graph": {
      "app.main::parse_program": ["app.main::parse_stmt"]
    },
    "sccs": [
      ["app.main::parse_stmt"]
    ],
    "non_escape_summary": {},
    "container_ownership_hints_v1": {}
  },
  "diagnostics": {
    "warnings": [],
    "errors": []
  }
}
```

### 4.3 module ごとの linked IR

各 output module は引き続き `kind=Module` の `EAST3` を保つ。  
ただし `meta.linked_program_v1` に global optimizer の結果を注釈として埋め込む。

最低限の必須キー:
- `meta.linked_program_v1.program_id`
- `meta.linked_program_v1.module_id`
- `meta.linked_program_v1.entry_modules`
- `meta.linked_program_v1.type_id_resolved_v1`
- `meta.linked_program_v1.non_escape_summary`
- `meta.linked_program_v1.container_ownership_hints_v1`
- `FunctionDef.meta.escape_summary`
- `Call.meta.non_escape_callsite`

### 4.4 重要方針

- `link-output.json` は backend が読む program manifest。
- `*.linked.east3.json` は backend / emitter が読む module 実体。
- global table の正本は `link-output.json`。
- module 側 `meta.*` は emitter のための materialized cache として扱う。

## 5. `rc<>` / container ownership に関する責務再配置

### 5.1 現状

現状の `rc<>` / list value lowering は以下のように分散している。

- `EAST3 optimizer`
  - `NonEscapeInterproceduralPass`
  - `CppListValueLocalHintPass`
  - `LifetimeAnalysisPass`
- `CppEmitter`
  - 上記注釈を読みつつ、C++ 表現へ落とす

この構造だと、`NonEscapeInterproceduralPass` が import closure を内部で辿るため、単一 module optimizer と whole-program optimizer の境界が曖昧になる。

### 5.2 目標

`rc<>` / ownership 系の global 判断は linked program 段へ移す。

具体的には:
- program-wide call graph 構築
- SCC fixed point
- module-cross non-escape summary
- container ownership hint
- `type_id` 決定

を `LinkedProgramOptimizer` で実施する。

### 5.3 local optimizer に残すもの

`EAST3 local optimizer` に残すのは、program-wide 文脈を必要としない処理に限る。

例:
- `NoOpCastCleanupPass`
- `LiteralCastFoldPass`
- `RangeForCanonicalizationPass`
- `ExpressionNormalizationPass`
- `TypedEnumerateNormalizationPass`
- `EmptyInitShorthandPass`

### 5.4 linked program optimizer に移すもの

初期移設対象:
- `NonEscapeInterproceduralPass`
  - import closure 自前読込を禁止
  - 入力 `LinkedProgram.modules` 全体から call graph を構築
- `CppListValueLocalHintPass`
  - linked summary を前提に module ごとへ hint を materialize
- `type_id` 確定
  - `spec-linker` の実体化

### 5.5 emitter の立場

`CppEmitter` は、linked module に付いた注釈を読むだけにする。

禁止事項:
- import closure の追加読込
- call graph の再構築
- `rc<>` / alias / non-escape の再推論
- `type_id` の再割当

## 6. ProgramWriter 契約

### 6.1 なぜ必要か

各言語 emitter に複数ファイル配置を背負わせると、次が emitter 内へ流れ込む。

- 出力 path 決定
- import graph ごとの file layout
- runtime copy
- manifest 生成
- build metadata
- packaging 差分

これは「コード生成」ではなく「program packaging」であり、責務が違う。

### 6.2 共通インターフェース（案）

```python
class ModuleArtifact(TypedDict):
    module_id: str
    primary_path: str
    outputs: list[dict[str, str]]
    text: str
    meta: dict[str, object]

class ProgramArtifact(TypedDict):
    target: str
    entry_modules: list[str]
    modules: list[ModuleArtifact]
    global_manifest: dict[str, object]

class ProgramWriter:
    def write(self, artifact: ProgramArtifact, output_root: Path, options: dict[str, object]) -> dict[str, object]:
        ...
```

### 6.3 backend 側の分離

- `ModuleEmitter`
  - `emit_module(...) -> ModuleArtifact`
- `ProgramWriter`
  - `write(...) -> output manifest`

backend registry もこれに合わせて分ける。

現状:
- `emit(ir, output_path) -> str`

目標:
- `emit_module(ir_module, emit_context) -> ModuleArtifact`
- `program_writer.write(program_artifact, output_root, options) -> manifest`

### 6.4 default 実装

全 backend がすぐ multi-file writer を持つ必要はない。

最低限:
- `DefaultSingleFileWriter`
  - entry module の primary output を所定 path へ書く
  - 単一ファイル言語向けの trivial 実装
- `CppProgramWriter`
  - 既存 `multifile_writer.py` の責務を再編して実装

### 6.5 C++ での具体化

`backends/cpp/emitter/multifile_writer.py` は次のように分解する。

- `CppEmitter`
  - module の `.cpp/.h` text を生成
- `CppProgramWriter`
  - `include/`, `src/`, `manifest.json`, prelude header, forward decl injection, runtime/include layout を管理
- `pytra-cli.py`
  - `CppProgramWriter` が出した manifest を `gen_makefile_from_manifest.py` へ渡す

## 7. CLI / 導線設計

### 7.1 新しい正規導線

本計画では CLI を無制限に増やさない。  
基本は既存 CLI を拡張し、global optimizer 専用に 1 本だけ新規導線を足す。

候補:
- `src/eastlink.py`
  - `link-input.json` を受けて `link-output.json` + linked modules を生成
- `src/ir2lang.py`
  - `Module EAST3 JSON` または `link-output.json` を受ける
- `src/py2x.py`
  - `.py -> linked program -> ProgramWriter` の end-to-end 高速導線を持つ

### 7.2 `py2x.py` の役割

`py2x.py` は既定では従来どおり end-to-end の高速経路を提供する。  
ただし内部構成は次へ変更する。

```text
py2x.py
  -> build all module EAST3 docs
  -> build link-input (in-memory)
  -> run LinkedProgramOptimizer
  -> backend lower/opt/emit per module
  -> ProgramWriter
```

### 7.3 `ir2lang.py` の役割

`ir2lang.py` は backend-only 導線として次を受理する。

1. 既存どおり単一 `Module` EAST3 JSON
2. 新規に `link-output.json`

挙動:
- 単一 module 入力
  - 既存挙動を維持
- linked program 入力
  - module 群を読み、backend へ module 単位に渡し、最後に `ProgramWriter` を呼ぶ

### 7.4 `eastlink.py` の役割

`eastlink.py` は次だけを行う。

- `link-input.json` を読む
- validate する
- global optimizer を走らせる
- `link-output.json` と linked modules を吐く

つまり:
- parser はしない
- backend emit もしない
- runtime copy もしない

## 8. 具体的な実装ステップ

### Phase 1: 契約と schema を固定する

- [ ] `spec-linker.md` を更新し、`linker == multi-unit optimizer + link manifest producer` を明記する。
- [ ] `spec-east.md` に `local optimizer` と `linked program optimizer` の段階境界を追記する。
- [ ] `spec-dev.md` / `spec-make.md` に `ProgramWriter` 境界を追記する。
- [ ] `link-input.v1` / `link-output.v1` の JSON schema を文書化する。
- [ ] `ModuleEmitter` / `ProgramWriter` 契約を backend 共通 API として定義する。

詳細タスク:
- [x] `S1-01` `link-input.v1` の必須キー、エラー契約、決定性要件を書く。
- [x] `S1-02` `link-output.v1` の必須キー、global table、diagnostics を書く。
- [x] `S1-03` linked module `meta` に materialize する注釈一覧を固定する。
- [x] `S1-04` `ModuleArtifact` / `ProgramArtifact` / `ProgramWriter` API を文書で固定する。

### Phase 2: loader / validator / in-memory program builder を実装する

- [ ] `src/toolchain/link/` を新設する。
- [ ] `schema.py`, `loader.py`, `validator.py`, `program_model.py` を追加する。
- [ ] `link-input.json` 読込と in-memory `LinkedProgram` 構築を実装する。
- [ ] `py2x.py` から単一 module ではなく module map を `LinkedProgram` 化する。

推奨ファイル:
- `src/toolchain/link/program_model.py`
- `src/toolchain/link/program_loader.py`
- `src/toolchain/link/program_validator.py`
- `src/toolchain/link/link_manifest_io.py`

詳細タスク:
- [x] `S2-01` `LinkedProgram` データモデルを追加する。
- [x] `S2-02` `link-input.json` loader を追加する。
- [x] `S2-03` module 順序・entry・dispatch 一貫性 validator を追加する。
- [ ] `S2-04` `py2x.py` の in-memory build 導線から `LinkedProgram` を組み立てる。

### Phase 3: global optimizer を linker 段へ実装する

- [ ] `NonEscapeInterproceduralPass` を program input 前提へ移す。
- [ ] import closure の内部読込を撤去する。
- [ ] module-cross call graph / SCC / summary を `LinkedProgram` ベースで計算する。
- [ ] `type_id` 決定を同じ段で materialize する。

推奨ファイル:
- `src/toolchain/link/global_optimizer.py`
- `src/toolchain/link/global_passes/non_escape_program_pass.py`
- `src/toolchain/link/global_passes/type_id_assignment_pass.py`
- `src/toolchain/link/global_passes/container_ownership_pass.py`

詳細タスク:
- [ ] `S3-01` program-wide call graph builder を追加する。
- [ ] `S3-02` SCC deterministic order を固定する。
- [ ] `S3-03` non-escape summary を global pass として移植する。
- [ ] `S3-04` `type_id` 決定を global pass として実装する。
- [ ] `S3-05` global summary を linked modules へ materialize する。
- [ ] `S3-06` `EAST3 local optimizer` から import-closure 依存を撤去する。

### Phase 4: local optimizer を再定義する

- [x] `EAST3 local optimizer` から whole-program 依存 pass を外す。
- [x] `CppListValueLocalHintPass` の位置を見直す。
- [x] local optimizer は「単一 module で閉じるものだけ」と明確にする。

詳細タスク:
- [x] `S4-01` default pass list を local-only / global-only に分ける。
- [x] `S4-02` `NonEscapeInterproceduralPass` を local pass 列から外す。
- [x] `S4-03` `CppListValueLocalHintPass` を post-link module rewrite へ移すか、global summary 前提の local post-pass へ縮退する。
- [x] `S4-04` `LifetimeAnalysisPass` の位置づけを「local analysis only」として固定する。

### Phase 5: backend registry を `ModuleEmitter + ProgramWriter` 構成へ移行する

- [x] `backend_registry.py` の `emit` 契約を分割する。
- [x] 各 backend spec に `emit_module` と `program_writer` を導入する。
- [x] 旧 `emit -> str` 契約は互換層へ縮退する。

詳細タスク:
- [x] `S5-01` backend spec schema を更新する。
- [x] `S5-02` default `SingleFileProgramWriter` を追加する。
- [x] `S5-03` `ir2lang.py` を new registry 契約へ対応させる。
- [x] `S5-04` 旧 unary emit API を wrapper 経由へ縮退する。

### Phase 6: C++ を先行移行する

- [x] C++ の `multifile_writer.py` を `CppProgramWriter` として再編する。
- [ ] `CppEmitter` は 1 module artifact を返すだけにする。
- [x] `pytra-cli.py` は `CppProgramWriter` の manifest を受けて build を行う。

詳細タスク:
- [x] `S6-01` `multifile_writer.py` の path/layout/manifest ロジックを `backends/cpp/program_writer.py` へ移す。
- [ ] `S6-02` `CppEmitter` から multi-file 固有分岐を外す。
- [x] `S6-03` `pytra-cli.py` を `ProgramWriter` 返却 manifest 前提へ更新する。
- [ ] `S6-04` C++ sample/fixture parity を再固定する。

### Phase 7: `ir2lang.py` と debug/restart 導線をつなぐ

- [ ] `ir2lang.py` に `link-output.json` 受理を追加する。
- [x] `eastlink.py` を追加する。
- [ ] `--dump-east3-dir`, `--link-only`, `--from-link-output` 系の導線を整理する。

詳細タスク:
- [x] `S7-01` `eastlink.py` の CLI 仕様を実装する。
- [ ] `S7-02` `ir2lang.py` の linked-program 入力を実装する。
- [ ] `S7-03` `py2x.py` から `--dump-east3-dir` / `--link-only` を追加する。
- [ ] `S7-04` backend-only 回帰と debug 手順を docs に追記する。

### Phase 8: 回帰・移行完了

- [ ] unit / tooling / sample parity を通す。
- [ ] 旧 import-closure 内部読込経路を削除する。
- [ ] `ProgramWriter` を使わない multi-file 直書き経路を削除する。

詳細タスク:
- [ ] `S8-01` `test/unit/link/*` を追加し schema / validator / determinism を固定する。
- [ ] `S8-02` C++ backend regression を再実行する。
- [ ] `S8-03` `sample` / `fixture` parity を再実行する。
- [ ] `S8-04` docs / spec / how-to-use を同期する。
- [ ] `S8-05` 旧経路削除後の clean-room 回帰を実施する。

## 9. 推奨ディレクトリ構成

```text
src/
  toolchain/
    ir/
      east3_optimizer.py              # local optimizer のみ
    link/
      program_model.py
      program_loader.py
      program_validator.py
      global_optimizer.py
      link_manifest_io.py
      global_passes/
        non_escape_program_pass.py
        type_id_assignment_pass.py
        container_ownership_pass.py
  backends/
    common/
      program_writer.py
    cpp/
      program_writer.py
      emitter/
        cpp_emitter.py                # module emitter
```

## 10. テスト計画

### 10.1 新規 unit

- `test/unit/link/test_link_input_schema.py`
- `test/unit/link/test_link_output_schema.py`
- `test/unit/link/test_program_loader.py`
- `test/unit/link/test_program_validator.py`
- `test/unit/link/test_program_call_graph.py`
- `test/unit/link/test_program_non_escape_pass.py`
- `test/unit/link/test_program_type_id_assignment.py`
- `test/unit/link/test_program_writer_contract.py`

### 10.2 既存回帰の更新

- `test/unit/backends/cpp/test_cpp_runtime_symbol_index_integration.py`
- `test/unit/backends/cpp/test_py2cpp_codegen_issues.py`
- `test/unit/backends/cpp/test_py2cpp_list_pyobj_model.py`
- `test/unit/tooling/test_cpp_runtime_build_graph.py`
- `test/unit/tooling/test_runtime_symbol_index.py`

### 10.3 sample / fixture

- `runtime_parity_check.py --targets cpp --case-root fixture`
- `runtime_parity_check.py --targets cpp --case-root sample --all-samples`
- `sample/18` を重点監視ケースにする
- `sample/05` を module-cross non-escape 監視ケースにする

## 11. リスクと対策

### 11.1 リスク: `EAST3 optimizer` と linker の責務が二重化する

対策:
- local pass / global pass を別 package に分ける。
- import closure 読込を local optimizer から禁止する。
- `check_east_stage_boundary.py` 相当の guard を linker / optimizer 境界にも追加する。

### 11.2 リスク: backend registry の破壊的変更が広範囲へ波及する

対策:
- `emit -> str` の旧 API を compatibility wrapper として一時保持する。
- 先行移行は C++ のみに限定する。
- 他言語は `DefaultSingleFileWriter` で追随できるようにする。

### 11.3 リスク: C++ `ProgramWriter` への移行で build 導線が壊れる

対策:
- 既存 `manifest.json` schema を極力保持する。
- `pytra-cli.py --build` の acceptance test を追加する。
- `multifile_writer.py` を一気に削除せず、最初は façade にする。

### 11.4 リスク: `rc<>` の global 最適化が過剰に aggressive になる

対策:
- fail-closed を既定にする。
- `global summary missing == optimize しない` を徹底する。
- correctness は ref-first 正本で成立させ、value 化は purely optimization とする。

## 12. 実施順の推奨

最初に着手すべき順番は次のとおり。

1. 契約文書を固定する  
   - `spec-linker` / `spec-east` / `ProgramWriter` 契約を書き切る。

2. linked program schema と loader を作る  
   - ここがないと optimizer の入力単位が固定できない。

3. global non-escape / `type_id` を linker 段へ移す  
   - `rc<>` 最適化の正しい置き場所を確定する。

4. backend registry を `emit_module + program_writer` に分離する  
   - emitter 肥大化を防ぐ。

5. C++ を先行移行する  
   - 現在 multi-file を持っているため、最も効果が出る。

6. `ir2lang.py` / debug/restart 導線をつなぐ  
   - 運用可能性を確保する。

## 13. 分解

- [ ] [ID: P0-LINKED-PROGRAM-OPT-01] linked program を導入し、global optimizer の入力単位を複数翻訳単位へ拡張しつつ、backend を `ModuleEmitter + ProgramWriter` 構成へ再編する。
- [x] [ID: P0-LINKED-PROGRAM-OPT-01-S1-01] `link-input.v1` / `link-output.v1` と linked module `meta` の schema、ならびに `spec-linker` / `spec-east` の責務境界を固定する。
- [x] [ID: P0-LINKED-PROGRAM-OPT-01-S1-02] `ModuleArtifact` / `ProgramArtifact` / `ProgramWriter` の backend 共通契約を定義し、`spec-dev` / `spec-make` へ反映する。
- [x] [ID: P0-LINKED-PROGRAM-OPT-01-S2-01] `src/toolchain/link/` に `LinkedProgram` loader / validator / manifest I/O を追加し、複数 `EAST3` を deterministic に読めるようにする。
- [x] [ID: P0-LINKED-PROGRAM-OPT-01-S2-02] `py2x.py` の in-memory 導線を module map から `LinkedProgram` 構築へ切り替え、single-module 前提を外す。
- [x] [ID: P0-LINKED-PROGRAM-OPT-01-S3-01] program-wide call graph / SCC fixed point を linker 段へ実装し、import-closure 内部読込に依存しない global 解析基盤を作る。
- [x] [ID: P0-LINKED-PROGRAM-OPT-01-S3-02] global non-escape / container ownership / `type_id` 決定を linker 段へ実装し、linked module と `link-output.json` へ materialize する。
- [x] [ID: P0-LINKED-PROGRAM-OPT-01-S4-01] `EAST3 local optimizer` と `LinkedProgramOptimizer` の pass 責務を再分割し、whole-program 依存 pass を local optimizer から撤去する。
- [x] [ID: P0-LINKED-PROGRAM-OPT-01-S5-01] `backend_registry.py` を `emit_module + program_writer` 契約へ拡張し、旧 `emit -> str` API を互換 wrapper 化する。
- [x] [ID: P0-LINKED-PROGRAM-OPT-01-S5-02] backend 共通 `SingleFileProgramWriter` を追加し、`ir2lang.py` を new registry 契約へ追従させる。
- [x] [ID: P0-LINKED-PROGRAM-OPT-01-S6-01] C++ を先行移行し、`multifile_writer.py` を `CppProgramWriter` へ再編して `CppEmitter` を module emit 専任にする。
- [x] [ID: P0-LINKED-PROGRAM-OPT-01-S6-02] `pytra-cli.py` / C++ build manifest / Makefile 生成導線を `ProgramWriter` 返却 manifest 正本へ更新する。
- [x] [ID: P0-LINKED-PROGRAM-OPT-01-S7-01] `eastlink.py` を追加し、`link-input.json -> link-output.json + linked modules` の debug/restart 導線を実装する。
- [x] [ID: P0-LINKED-PROGRAM-OPT-01-S7-02] `ir2lang.py` と `py2x.py` に linked-program 入出力（`--link-only`, dump/restart）を追加し、backend-only 導線を完成させる。
- [ ] [ID: P0-LINKED-PROGRAM-OPT-01-S8-01] `test/unit/link/*` と representative backend/tooling 回帰を追加し、schema / determinism / program writer 契約を固定する。
- [ ] [ID: P0-LINKED-PROGRAM-OPT-01-S8-02] C++ unit / fixture / sample parity、docs 同期、旧 import-closure 依存経路の撤去まで完了し、本計画を閉じる。

## 14. 決定ログ

- 2026-03-07: `rc<>` に関する whole-program optimization は単一 `Module` 入力の `EAST3 optimizer` では成立しない、という認識を前提に本計画を起票した。
- 2026-03-07: `NonEscapeInterproceduralPass` の import-closure 追加読込は temporary bridge と位置づけ、最終的には linked program optimizer へ移す方針を採用した。
- 2026-03-07: 各言語 emitter を肥大化させないため、`ModuleEmitter` と `ProgramWriter` を分離する方針を採用した。
- 2026-03-07: CLI は無制限に増やさず、global optimizer 専用に `eastlink.py` を追加し、backend-only 側は `ir2lang.py` 拡張で受ける方針を採用した。
- 2026-03-07: linked program の出力は「1 本の巨大 IR」ではなく「program manifest + module ごとの linked IR」とする方針を採用した。
- 2026-03-07: [ID: P0-LINKED-PROGRAM-OPT-01-S1-01] `spec-linker.md` で `pytra.link_input.v1` / `pytra.link_output.v1` と `meta.linked_program_v1` を canonical schema として固定し、`spec-east.md` では `Link` を `east_stage` を増やさない責務境界として定義した。
- 2026-03-07: [ID: P0-LINKED-PROGRAM-OPT-01-S1-02] `spec-dev.md` で `ModuleEmitter -> ModuleArtifact -> ProgramWriter` の backend 共通境界を固定し、`spec-make.md` では `manifest.json` を `CppProgramWriter` が出力する `ProgramArtifact` の concrete build manifest として位置づけた。
- 2026-03-07: [ID: P0-LINKED-PROGRAM-OPT-01-S2-01] `src/toolchain/link/` に `program_model.py` / `program_validator.py` / `link_manifest_io.py` / `program_loader.py` を追加し、`pytra.link_input.v1` から raw `EAST3` 群を決定的順序で読む `LinkedProgram` loader を実装した。`test/unit/link/test_program_loader.py` で entry/dispatch/raw-meta 契約を固定した。
- 2026-03-07: [ID: P0-LINKED-PROGRAM-OPT-01-S2-02] `LinkedProgram` を manifest-backed / in-memory の両方で扱えるよう `manifest_path=None` / `artifact_path=None` を許す model に拡張し、`py2x.py` は `.py` 入力時に `build_module_east_map(...) -> build_linked_program_from_module_map(...)` を通るよう更新した。`dump-east3-*` は entry module のみへ出す挙動に絞り、`test/unit/tooling/test_py2x_cli.py` と `test/unit/link/test_program_loader.py` で entry selection / JSON fallback / in-memory serialization guard を固定した。
- 2026-03-07: [ID: P0-LINKED-PROGRAM-OPT-01-S3-01] `src/toolchain/link/program_call_graph.py` を追加し、`LinkedProgram.modules` だけを入力に使う program-wide call graph / SCC builder を実装した。既存 `non_escape_call_graph` utility は再利用するが、欠けた callee を追加読込せず unresolved count に落とす方針を固定し、`test/unit/link/test_program_call_graph.py` で cross-module edge / mutual recursion SCC / missing module non-load を回帰化した。
- 2026-03-07: [ID: P0-LINKED-PROGRAM-OPT-01-S3-02] `src/toolchain/link/global_optimizer.py` を追加し、`optimize_linked_program(...)` で global non-escape summary、C++ list ownership hint、deterministic `type_id_table`、`meta.linked_program_v1`、`link-output.v1` を in-memory materialize する導線を実装した。non-escape は program 内 module 群だけを closure に入れた `NonEscapeInterproceduralPass` 再利用で賄い、fallback source load は `source_path=""` で封じた。`test/unit/link/test_global_optimizer.py` で cross-module summary、type_id 決定、C++ value-list hint を固定した。
- 2026-03-07: [ID: P0-LINKED-PROGRAM-OPT-01-S4-01] `src/toolchain/ir/east3_opt_passes/__init__.py` に `build_local_only_passes()` / `build_global_post_link_passes()` を追加し、local default pass から `NonEscapeInterproceduralPass` / `CppListValueLocalHintPass` を外した。`optimize_linked_program(...)` は `east3_opt_level` / `east3_opt_pass` を尊重して global pass を有効化し、`py2x.py` と `backends/cpp/cli.py` の `.py -> EAST3` 導線は linked optimizer 後の entry/module map を backend へ渡すよう更新した。`test/unit/ir/test_east3_optimizer.py`、`test/unit/link/test_global_optimizer.py`、`test/unit/backends/cpp/test_east3_cpp_bridge.py` で split 契約と `opt_level=0` の非退行を固定した。
- 2026-03-07: [ID: P0-LINKED-PROGRAM-OPT-01-S5-01] `backend_registry.py` / `backend_registry_static.py` に `emit_module(...)` / `build_program_artifact(...)` / `get_program_writer(...)` を追加し、backend spec 正規化時に `emit_module` と `program_writer` を必ず持つよう更新した。既存 `emit_source()` は `ModuleArtifact.text` を返す互換 wrapper へ縮退した。`test/unit/common/test_py2x_entrypoints_contract.py` で host/selfhost spec 契約と wrapper 動作を固定した。
- 2026-03-07: [ID: P0-LINKED-PROGRAM-OPT-01-S5-02] `src/backends/common/program_writer.py` に default `SingleFileProgramWriter` を追加し、`ir2lang.py` の single-module backend-only 経路を `emit_module -> ProgramArtifact -> ProgramWriter` へ切り替えた。`test/unit/tooling/test_ir2lang_cli.py` と `test/unit/common/test_py2x_smoke_common.py` で writer 導線の非退行を固定した。
- 2026-03-07: [ID: P0-LINKED-PROGRAM-OPT-01-S6-01] `src/backends/cpp/program_writer.py` を追加し、prelude/include/src/manifest の layout 書き出しを `write_cpp_rendered_program(...)` / `write_cpp_program(...)` へ移した。`backends/cpp/emitter/multifile_writer.py` は module text を組み立てて新 writer へ渡す façade に縮退し、host/selfhost の C++ backend spec も explicit `program_writer` を持つよう更新した。`test/unit/backends/cpp/test_cpp_program_writer.py`、`test_py2cpp_features.py` の multi-file regression、`test_py2x_entrypoints_contract.py` を通して非退行を固定した。
- 2026-03-07: [ID: P0-LINKED-PROGRAM-OPT-01-S6-02] `backends/cpp/cli.py` は multi-file 完了メッセージで `ProgramWriter` の `manifest` / `primary_output` を正本に使うよう更新し、`src/pytra-cli.py` は py2x stdout の `manifest:` 行を解析して reported manifest path をそのまま `gen_makefile_from_manifest.py` へ渡すようにした。reported path がない場合のみ `output_dir/manifest.json` fallback を許し、`test/unit/tooling/test_pytra_cli.py` と `test_py2cpp_features.py` の multi-file build/run 回帰で非退行を固定した。
- 2026-03-07: [ID: P0-LINKED-PROGRAM-OPT-01-S7-01] `src/eastlink.py` を追加し、`link-input.json` を `load_linked_program(...)` で読み、`optimize_linked_program(...)` の結果を `link-output.json` と `linked/<module>.east3.json` 群として materialize する最小 CLI を実装した。parser/backend/runtime copy は持たず、`test/unit/link/test_eastlink_cli.py` と `test/unit/link/*` の discover 回帰で schema/loader/global optimizer との接続を固定した。
- 2026-03-07: [ID: P0-LINKED-PROGRAM-OPT-01-S7-02] `src/toolchain/link/materializer.py` を追加し、in-memory `LinkedProgram` から `link-input.json + raw/<module>.east3.json`、および linked optimizer 結果から `link-output.json + linked/<module>.east3.json` を共通 materialize できるようにした。`py2x.py` は C++ target でも `--dump-east3-dir` / `--link-only` / `--from-link-output` 指定時は legacy `py2cpp` compat を迂回し、dump/link-only は backend dispatch を呼ばず、restart は `ir2lang.py` へ委譲する方針を採用した。
- 2026-03-07: [ID: P0-LINKED-PROGRAM-OPT-01-S7-02] `ir2lang.py` は `link-output.json` を受理できるようにし、non-C++ は entry linked module の single-file 再開、C++ は linked module 群を `write_multi_file_cpp(...)` へ流す backend-only restart 導線を実装した。`test/unit/tooling/test_py2x_cli.py` と `test/unit/tooling/test_ir2lang_cli.py` で dump/link-only/restart/cpp multi-file restart を固定した。
