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
- `link unit`: 1 モジュール分の `EAST3`。
- `link manifest`: link 入力集合・設定・割当結果を保持するメタ情報。

## 4. 基本パイプライン

### 4.1 既定（高速）

- 既定は従来どおりメモリ内で処理する。
- `parser -> EAST1 -> EAST2 -> EAST3 -> linker(in-memory) -> backend`

### 4.2 デバッグ/再現モード

- 必要時のみ中間ファイルを保存する。
- 例: `test1.east1`, `test1.east2`, `test1.east3`（実体は JSON）

推奨拡張子:
- `*.east1.json`
- `*.east2.json`
- `*.east3.json`

## 5. linker の責務

linker は `EAST3` 群を受け取り、次を確定する。

1. モジュール ID 正規化
- パス/モジュール名の揺れを正規化し、重複定義を検出する。

2. グローバル型表の構築
- FQCN（module + class）をキーに型定義を一意化する。
- 継承グラフ（単一継承想定）を構築し、循環を検出する。

3. `type_id` の確定
- built-in は固定 ID を維持する（`spec-type_id`/runtime 契約）。
- user class は linker が決定的規則で割り当てる。
- backend は linker 確定値を使うだけにする。

4. dispatch 契約固定
- `meta.dispatch_mode` を link 単位で整合チェックする。
- 混在（hybrid）を禁止し、違反時は fail-fast。

5. 連結済み IR 出力
- backend が直接利用可能な linked `EAST3`（または等価 manifest）を出力する。

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

各 `EAST*` 文書は少なくとも次を持つ。

- `east_stage`: `east1 | east2 | east3`
- `schema_version`
- `meta.dispatch_mode`: `native | type_id`
- `meta.transpiler_version`
- `meta.input_hash`（任意だが推奨）

linker 出力は次のいずれか:

1. `linked.east3.json`
- `EAST3` 本体 + `type_table` + `module_table`

2. `link-manifest.json`
- 入力 `EAST3` 一覧
- 確定 `type_id` マップ（`FQCN -> int`）
- 検証結果メタ（warnings/errors）

## 8. CLI 仕様（追加方針）

最低限次を定義する。

- `--dump-east1 PATH`
- `--dump-east2 PATH`
- `--dump-east3 PATH`
- `--from-east1 PATH`
- `--from-east2 PATH`
- `--from-east3 PATH`
- `--link-manifest PATH`
- `--link-only`

挙動規則:

1. `--from-east3` 指定時は parser/normalize/lower をスキップして link 段から開始。
2. `--link-only` は backend 生成を行わず、manifest/linked IR のみ出力。
3. `--object-dispatch-mode` は linker 前段で確定済みであることを要求。

## 9. 実装モード指針

### 9.1 日常運用

- 既定は in-memory linker。
- 中間ファイルを毎回書かない（速度優先）。

### 9.2 デバッグ/CI

- 失敗再現時のみ `--dump-east*` を使う。
- 回帰テストでは `--from-east3` + `--link-only` を使い、link 規約だけを独立検証できるようにする。

## 10. エラー契約

linker 失敗は `input_invalid(kind=..., stage=link, ...)` で統一する。

推奨 `kind`:
- `type_cycle`
- `unknown_base_type`
- `duplicate_type_symbol`
- `dispatch_mode_mismatch`
- `invalid_link_input`

## 11. 受け入れ基準

1. 同一入力で `type_id` 割り当てが決定的である。
2. `EAST3` をファイル経由で再開しても、直列変換と同一結果になる。
3. `dispatch_mode` 混在入力を linker が検出して停止する。
4. backend は `type_id` を再計算せず、linker 確定値のみ参照する。

## 12. 関連

- `docs/ja/spec/spec-east.md`
- `docs/ja/spec/spec-type_id.md`
- `docs/ja/spec/spec-boxing.md`
- `docs/ja/spec/spec-iterable.md`
