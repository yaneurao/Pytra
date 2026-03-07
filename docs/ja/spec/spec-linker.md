# Linker 仕様（EAST1/EAST2/EAST3 連結）

<a href="../../en/spec/spec-linker.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

この文書は、`EAST1` / `EAST2` / `EAST3` を中間ファイルとして扱う場合の
`linker`（連結段）仕様を定義する。

主目的は次の 2 点:

1. 変換パイプラインの各段を独立に検証できるようにする。
2. `type_id` など「全モジュールを見ないと確定できない情報」を 1 箇所で確定する。

位置づけ:
- 上位仕様は [spec-east.md](./spec-east.md) とし、本書はその連結段詳細を定義する下位仕様とする。
- 仕様衝突時は `spec-east` を優先し、本書はそれに従って更新する。

## 1. 背景

- `EAST3` 導入後、backend は原則「命令写像」に専念する。
- 一方、`type_id` の割り当てはモジュール横断情報を必要とする。
- 単発変換では実行順依存 ID が発生しやすく、再現性と多段変換に不利。

そのため、`EAST3 -> linker -> backend` の責務分離を定義する。

## 2. 非目標

- ネイティブバイナリのリンカ（`ld`, `link.exe`）代替。
- 最適化器（DCE, inlining, register allocation）の全面実装。
- 既存の高速経路（メモリ内一気通貫）を廃止すること。

## 3. 用語

- `EAST1`: parser 直後の loss-minimal IR。
- `EAST2`: normalize 専任 IR。
- `EAST3`: backend 入力の意味論 IR。
- `link unit`: link 前の 1 モジュール分 `EAST3` 文書。
- `LinkedProgram`: 複数 `link unit` と program-wide option を束ねた検証済み in-memory モデル。
- `link-input.v1`: `LinkedProgram` を構築するための入力 manifest。
- `link-output.v1`: global summary と linked module 出力先を記録する出力 manifest。
- `linked module`: linker / linked-program optimizer 後の `EAST3` 文書。`kind=Module` と `east_stage=3` は維持しつつ、`meta.linked_program_v1` を持つ。

## 4. 基本パイプライン

### 4.1 既定（高速）

- 既定は従来どおりメモリ内で処理する。
- `parser -> EAST1 -> EAST2 -> EAST3(raw module) -> LinkedProgramLoader -> LinkedProgramOptimizer -> linked module(EAST3) -> backend`

### 4.2 デバッグ/再現モード

- 必要時のみ raw `EAST3` 群と `link-input.v1` / `link-output.v1` を保存する。
- 推奨導線は次のとおり。
  1. `py2x.py` で raw `EAST3` 群と `link-input.json` を出力する。
  2. `eastlink.py` で `link-input.json` を読み、`link-output.json` と linked module 群を出力する。
  3. `ir2lang.py` で `link-output.json` を読んで backend emit する。

推奨拡張子 / ファイル名:
- `*.east1.json`
- `*.east2.json`
- `*.east3.json`
- `link-input.json`
- `link-output.json`

## 5. linker の責務

linker / linked-program optimizer は raw `EAST3` 群を受け取り、次を確定する。

1. module 集合の検証
- `kind=Module`
- `east_stage=3`
- `schema_version`
- `meta.dispatch_mode`
を検証し、program-wide 一貫性違反を fail-fast する。

2. モジュール ID 正規化と決定的順序
- `module_id` の揺れを正規化し、重複定義を検出する。
- 同一入力集合では常に同じ順序で `LinkedProgram` を構築する。

3. global summary 構築
- program-wide call graph
- SCC
- `type_id_table`
- non-escape summary
- container ownership hints
を 1 箇所で確定する。

4. linked module への materialize
- backend が module 単位で読めるよう、global summary の必要 slice を各 module `meta.linked_program_v1` へ materialize する。
- function/call 単位の summary（例: `FunctionDef.meta.escape_summary`, `Call.meta.non_escape_callsite`）もこの段で最終化してよい。

5. program manifest 出力
- `link-output.v1` を正本として出力し、global table の canonical source とする。
- backend / `ProgramWriter` は `link-output.v1` と linked module を入力に動作する。

backend 側の禁止事項:
- `type_id` を再計算しない。
- module 集合を勝手に再読込して whole-program summary を再構築しない。
- raw `EAST3` に不足する global 情報を emitter / hook で補完しない。

## 6. `type_id` 割り当て規則

### 6.1 基本

- built-in:
  - runtime 既存値を固定採用する（例: `NONE=0`, `OBJECT=8`, `USER_BASE=1000`）。
- user class:
  - `USER_BASE` 以上を linker が割り当てる。

### 6.2 決定性（必須）

- 同一入力集合・同一オプションなら常に同一 `type_id` になること。
- 割り当て順は次の優先順を推奨:
1. 継承依存を満たすトポロジカル順
2. 同順位は FQCN 辞書順

### 6.3 検証

- 未定義基底型、継承循環、同名衝突を検出したら `input_invalid` で停止する。

## 7. 入出力契約

### 7.1 raw `EAST3` document の前提

linker が受理する raw `EAST3` 文書は少なくとも次を持つ。

- `kind = "Module"`
- `east_stage = 3`（整数）
- `schema_version`（整数）
- `meta.dispatch_mode = "native" | "type_id"`
- `meta.transpiler_version`（推奨）
- `meta.input_hash`（任意だが推奨）

### 7.2 `link-input.v1`

`link-input.v1` は `LinkedProgram` 構築前の入力 manifest である。

必須トップレベルキー:

- `schema`
  - 固定値: `pytra.link_input.v1`
- `target`
  - 例: `cpp`, `rs`, `js`
- `dispatch_mode`
  - `native | type_id`
- `entry_modules`
  - entry module の `module_id` 配列
- `modules`
  - module entry 配列

任意トップレベルキー:

- `options`
  - target / optimizer 固有 option を保持する object。未知キーは validator が fail-closed せず透過保持してよい。

`modules[*]` の必須キー:

- `module_id`
- `path`
- `source_path`
- `is_entry`

`link-input.v1` の path 契約:

- `path` と `source_path` は manifest 配置ディレクトリからの POSIX 相対パスを正本とする。
- loader 実装が互換のため絶対パスを受理してもよいが、生成器が出力する canonical form は相対パスとする。

`link-input.v1` の検証規則:

1. `module_id` は一意でなければならない。
2. `entry_modules` は `modules[*].module_id` の部分集合でなければならない。
3. 各 `path` は `kind=Module` / `east_stage=3` の raw `EAST3` 文書を指さなければならない。
4. raw `EAST3.meta.dispatch_mode` は manifest `dispatch_mode` と一致しなければならない。
5. `modules` の走査順は validator 内部で `module_id` 辞書順へ正規化し、決定性を保証する。

### 7.3 `link-output.v1`

`link-output.v1` は linker / linked-program optimizer の canonical 出力 manifest である。

必須トップレベルキー:

- `schema`
  - 固定値: `pytra.link_output.v1`
- `target`
- `dispatch_mode`
- `entry_modules`
- `modules`
- `global`
- `diagnostics`

`modules[*]` の必須キー:

- `module_id`
- `input`
- `output`
- `source_path`
- `is_entry`

`global` の必須キー:

- `type_id_table`
  - `FQCN -> int`
- `call_graph`
  - `caller -> callee[]`
- `sccs`
  - `string[][]`
- `non_escape_summary`
  - program-wide summary object
- `container_ownership_hints_v1`
  - program-wide ownership hint object

`diagnostics` の必須キー:

- `warnings`
  - string 配列
- `errors`
  - string 配列

`link-output.v1` の規則:

1. `modules[*].output` は linked module（後述）の出力先を指す。
2. `global` の各 table は空でもキー自体は必須とする。
3. backend / `ProgramWriter` が参照する global table の canonical source は常に `link-output.v1` とする。

### 7.4 linked module schema

linked module は raw `EAST3` と同じく `kind=Module` / `east_stage=3` を維持する。  
追加される canonical meta は `meta.linked_program_v1` である。

`meta.linked_program_v1` の必須キー:

- `program_id`
  - linked program の決定的 ID。生成規則は実装依存だが、同一入力集合では同一値でなければならない。
- `module_id`
  - 現在 module の `module_id`
- `entry_modules`
  - program entry module の `module_id` 配列
- `type_id_resolved_v1`
  - 現在 module が必要とする `FQCN -> int` slice
- `non_escape_summary`
  - 現在 module が必要とする escape summary slice
- `container_ownership_hints_v1`
  - 現在 module が必要とする ownership hint slice

linked module の補足規則:

1. `meta.dispatch_mode` は raw `EAST3` と同じく必須であり、`meta.linked_program_v1` と矛盾してはならない。
2. function / call 単位の materialized summary は、既存 `meta` 契約を使って保持してよい。
3. `meta.linked_program_v1` は linked module では必須、raw `EAST3` では存在してはならない。

## 8. CLI / 導線仕様（方針）

正規導線は次を前提とする。

- `py2x.py`
  - raw `EAST3` 群と `link-input.json` を出力できる。
- `eastlink.py`
  - `link-input.json` を読み、`link-output.json` と linked module 群を出力する。
- `ir2lang.py`
  - raw 単一 `Module` または `link-output.json` を受理し、backend へ渡す。

最小挙動規則:

1. `--link-only` は backend 生成を行わず、`link-output.json` と linked module 群のみ出力する。
2. `--object-dispatch-mode` は raw `EAST3` 構築前に確定し、linker は整合性検査だけを行う。
3. debug / restart 経路でも `link-input.v1` / `link-output.v1` を canonical source とする。
4. global pass は `link-input.v1` / `link-output.v1` が列挙した module 群だけを入力として扱う。`source_path` を辿った追加読込や import 文の再解析で closure を拡張してはならない。
5. `NonEscapeInterproceduralPass` が linked-program 経路で参照してよい closure は linker/materializer が埋めた `meta.non_escape_import_closure` のみであり、存在しない場合は fail-closed で unresolved 扱いにする。

## 9. 実装モード指針

### 9.1 日常運用

- 既定は in-memory `LinkedProgramLoader + LinkedProgramOptimizer`。
- raw `EAST3` / linked module / manifest を毎回書かない（速度優先）。

### 9.2 デバッグ/CI

- 失敗再現時のみ raw `EAST3` dump と `link-input.v1` / `link-output.v1` を保存する。
- 回帰テストでは `link-input.v1 -> eastlink.py -> link-output.v1` を独立に検証できるようにする。

## 10. エラー契約

linker 失敗は `input_invalid(kind=..., stage=link, ...)` で統一する。

推奨 `kind`:
- `type_cycle`
- `unknown_base_type`
- `duplicate_type_symbol`
- `duplicate_module_id`
- `missing_entry_module`
- `dispatch_mode_mismatch`
- `invalid_link_input`
- `invalid_link_output`
- `invalid_linked_module_meta`

## 11. 受け入れ基準

1. 同一入力で `type_id` 割り当てが決定的である。
2. 同一入力集合・同一 option で `link-input.v1` / `link-output.v1` / linked module の内容が決定的である。
3. raw `EAST3` をファイル経由で再開しても、in-memory 直列変換と同一結果になる。
4. `dispatch_mode` 混在入力を linker が検出して停止する。
5. backend は `type_id` や non-escape summary を再計算せず、linker 確定値のみ参照する。

## 12. 関連

- `docs/ja/spec/spec-east.md`
- `docs/ja/spec/spec-type_id.md`
- `docs/ja/spec/spec-boxing.md`
- `docs/ja/spec/spec-iterable.md`
