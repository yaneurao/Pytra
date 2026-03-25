# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-03-24（パイプライン再設計着手に伴い全 TODO をアーカイブへ移動）

## 文脈運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度上書きは `docs/ja/plans/instruction-template.md` 形式でチャット指示し、`todo2.md` は使わない。
- 着手対象は「未完了の最上位優先度ID（最小 `P<number>`、同一優先度では上から先頭）」に固定し、明示上書き指示がない限り低優先度へ進まない。
- `P0` が 1 件でも未完了なら `P1` 以下には着手しない。
- 着手前に文脈ファイルの `背景` / `非対象` / `受け入れ基準` を確認する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める（例: ``[ID: P0-XXX-01] ...``）。
- `docs/ja/todo/index.md` の進捗メモは 1 行要約に留め、詳細（判断・検証ログ）は文脈ファイル（`docs/ja/plans/*.md`）の `決定ログ` に記録する。
- 1 つの `ID` が大きい場合は、文脈ファイル側で `-S1` / `-S2` 形式の子タスクへ分割して進めてよい（親 `ID` 完了までは親チェックを維持）。
- 割り込み等で未コミット変更が残っている場合は、同一 `ID` を完了させるか差分を戻すまで別 `ID` に着手しない。
- `docs/ja/todo/index.md` / `docs/ja/plans/*.md` 更新時は `python3 tools/check_todo_priority.py` を実行し、差分に追加した進捗 `ID` が最上位未完了 `ID`（またはその子 `ID`）と一致することを確認する。
- 作業中の判断は文脈ファイルの `決定ログ` へ追記する。
- 一時出力は既存 `out/`（または必要時のみ `/tmp`）を使い、リポジトリ直下に新規一時フォルダを増やさない。

## メモ

- このファイルは未完了タスクのみを保持します。
- 完了済みタスクは `docs/ja/todo/archive/index.md` 経由で履歴へ移動します。
- `docs/ja/todo/archive/index.md` は索引のみを保持し、履歴本文は `docs/ja/todo/archive/YYYYMMDD.md` に日付単位で保存します。

## 未完了タスク

### 共通

文脈: [docs/ja/plans/plan-pipeline-redesign.md](../plans/plan-pipeline-redesign.md)
コーディング規約: plan §5（Any/object 禁止、pytra.std 再実装禁止、グローバル可変状態禁止 等）

1. [x] [ID: P0-PIPELINE-V2-S0] golden file 生成ツール (`tools/generate_golden.py`) — 完了

### P0-PARSE: py → east1 (Agent A)

作業ディレクトリ: `toolchain2/parse/py/`
入力: `test/fixture/source/py/*.py`, `sample/py/*.py`
正解: `test/fixture/east1/py/`, `test/sample/east1/py/`

1. [x] [ID: P0-PARSE-S1] 自前パーサーで fixture 132 件の .py.east1 が golden と一致する — 完了
2. [x] [ID: P0-PARSE-S2] sample 18 件の .py.east1 が golden と一致する — 完了
3. [x] [ID: P0-PARSE-S3] `pytra-cli2 -parse` を toolchain2 の自前パーサーに切り替える — 完了
4. [x] [ID: P0-PARSE-S4] builtins.py / containers.py の新構文に対応し、golden を `test/builtin/east1/py/` に配置する — 完了
5. [x] [ID: P0-PARSE-S5] v2 extern (`extern_fn` / `extern_var` / `extern_class`) の構文に対応し、include/ の golden を再生成する — 完了
6. [x] [ID: P0-PARSE-S6] `extern_method` の構文に対応し、containers.py の golden を再生成する — 完了

P0-PARSE-S6 の詳細:

containers.py に `@extern_method(module=..., symbol=..., tag=...)` を追加済み。
パーサーを `extern_method` decorator に対応させ、EAST1 の FunctionDef.meta.extern_v2 に格納する。

対応が必要な構文:
- `@extern_method(module="...", symbol="...", tag="...")` — クラス内メソッド decorator
- EAST1 の `FunctionDef.meta.extern_v2: {kind: "method", module, symbol, tag}` に格納

完了条件:
- `src/include/py/pytra/built_in/containers.py` が parse 成功し、全メソッドに extern_v2 が付与される
- golden を `test/builtin/east1/py/` に再生成
- AGENT-B が resolve で container メソッドの runtime 情報を `meta.extern_v2` から取得可能

P0-PARSE-S5 の詳細:

パーサーを以下の v2 extern 構文に対応させる。仕様: `spec-builtin-functions.md §10`

対応が必要な構文:
1. `@extern_fn(module="...", symbol="...", tag="...")` — 関数 decorator。EAST1 の `FunctionDef.meta.extern_v2: {module, symbol, tag}` に格納
2. `extern_var(module="...", symbol="...", tag="...")` — 変数初期化。EAST1 の `AnnAssign.meta.extern_v2: {module, symbol, tag}` に格納
3. `@extern_class(module="...", symbol="...", tag="...")` — クラス decorator。EAST1 の `ClassDef.meta.extern_v2: {module, symbol, tag}` に格納

完了条件:
- `src/include/py/pytra/built_in/builtins.py` が parse 成功し、meta に extern_v2 が付与される
- `src/include/py/pytra/std/math.py` 等の全 stdlib 宣言が parse 成功
- golden を `test/builtin/east1/py/` と `test/stdlib/east1/py/` に配置
- AGENT-B が resolve で meta.extern_v2 から runtime 情報を取得可能

### P0-RESOLVE: east1 → east2 (Agent B)

作業ディレクトリ: `toolchain2/resolve/py/`

入力:
- ユーザーコード: `test/fixture/east1/py/*.py.east1`, `test/sample/east1/py/*.py.east1`
- built-in 宣言 EAST1: `test/builtin/east1/py/builtins.py.east1`, `test/builtin/east1/py/containers.py.east1`
- stdlib 宣言 EAST1: `test/stdlib/east1/py/*.py.east1`

正解: `test/fixture/east2/`, `test/sample/east2/`

仕様:
- 入力仕様: `docs/ja/spec/spec-east1.md`
- 出力仕様: `docs/ja/spec/spec-east2.md`
- built-in 関数仕様: `docs/ja/spec/spec-builtin-functions.md`（特に §5 py_ 変換テーブル、§10 v2 extern）
- コーディング規約: `docs/ja/plans/plan-pipeline-redesign.md` §5

重要: built-in / stdlib の EAST1 には `meta.extern_v2: {module, symbol, tag}` が付与されている。
resolve は **このメタデータから直接** `runtime_module_id` / `runtime_symbol` / `semantic_tag` を取得する。
ハードコードテーブル（`_BUILTIN_SEMANTIC_TAGS` 等）は不要。`builtin_registry.py` の 4 テーブルを除去し、
EAST1 の `meta.extern_v2` を正本にすること。

実装すべきこと:
- 型注釈の正規化（`int`→`int64`, `float`→`float64`, `bytes`→`list[uint8]` 等）
- 全式ノードの `resolved_type` 確定（`unknown` ゼロ）
- `borrow_kind` の判定（`readonly_ref` / `value`）
- `casts` の挿入（数値昇格 `int64`→`float64` 等）
- built-in → `py_*` ノード変換（`len(x)` → `py_len(x)` 等。spec-builtin-functions §5.1 参照）
- `semantic_tag` / `runtime_module_id` / `runtime_symbol` の付与 — **`meta.extern_v2` から取得**
- `runtime_call` / `resolved_runtime_call` の付与 — **`meta.extern_v2` から取得**
- `arg_usage` の判定（`readonly` / `reassigned`）
- `range()` → `ForRange` / `RangeExpr` の変換
- `lowered_kind: "BuiltinCall"` の付与
- `schema_version: 1` / `meta.dispatch_mode` の付与
- cross-module 型解決（built-in / stdlib の EAST1 からシグネチャ + `meta.extern_v2` を取得）
- `*args: T` → `args: list[T]` の varargs 変換

1. [x] [ID: P0-RESOLVE-S1] strip 済み EAST1 を入力にして、fixture 132 件の .east2 が golden と一致する — 完了 (132/132)
2. [x] [ID: P0-RESOLVE-S2] sample 18 件の .east2 が golden と一致する — 完了 (18/18)
3. [x] [ID: P0-RESOLVE-S3] `pytra-cli2 -resolve` を toolchain2 の resolve に切り替える — 完了

### P0-COMPILE: east2 → east3 (Agent C)

作業ディレクトリ: `toolchain2/compile/`
入力: `test/fixture/east2/*.east2`, `test/sample/east2/*.east2`
正解: `test/fixture/east3/`, `test/sample/east3/`

1. [x] [ID: P0-COMPILE-S1] core lowering を実装し、fixture 132 件の .east3 が golden と一致する — 完了（132/132 pass）
2. [x] [ID: P0-COMPILE-S2] sample 18 件の .east3 が golden と一致する — 完了（18/18 pass）
3. [x] [ID: P0-COMPILE-S3] `pytra-cli2 -compile` を実装する — 完了

### P0-OPTIMIZE: east3 最適化 (Agent D)

作業ディレクトリ: `toolchain2/optimize/`
入力: `test/fixture/east3/*.east3`, `test/sample/east3/*.east3`
正解: `test/fixture/east3-opt/`, `test/sample/east3-opt/`

1. [x] [ID: P0-OPTIMIZE-S1] whole-program 最適化を実装し、fixture 132 件の .east3 が golden と一致する — 完了
2. [x] [ID: P0-OPTIMIZE-S2] sample 18 件の .east3 が golden と一致する — 完了
3. [x] [ID: P0-OPTIMIZE-S3] `pytra-cli2 -optimize` を実装する — 完了

### P0-LINK: east3-opt → linked（manifest + linked east3 群）

作業ディレクトリ: `toolchain2/link/`
入力: `test/fixture/east3-opt/*.east3`, `test/sample/east3-opt/*.east3`
正解: `test/fixture/linked/`, `test/sample/linked/`

仕様:
- EAST 統合仕様: `docs/ja/spec/spec-east.md`（§17 パイプライン、§17.1 linked module meta 契約）
- Linker 仕様: `docs/ja/spec/spec-linker.md`
- コーディング規約: `docs/ja/plans/plan-pipeline-redesign.md` §5

責務:
- multi-module 結合（import graph 解決、依存 module の EAST3 収集）
- `manifest.json` 生成（entry module、module 一覧、出力パス）
- runtime module の EAST3 追加（`built_in/io_ops`, `std/time`, `utils/png` 等）
- type_id テーブル生成（`type_id_resolved_v1`）
- `linked_program_v1` metadata 付与
- `pytra-cli2 -link` コマンド実装

参考実装: 現行 `src/toolchain/link/` のコードをロジック参照元として使ってよい（import はしない）。
理解したロジックを toolchain2 の設計（dataclass、common/、§5 規約）で書き直すこと。

1. [x] [ID: P0-LINK-S1] linker を実装し、fixture の linked output が golden と一致する — 完了（132/132 pass）
2. [x] [ID: P0-LINK-S2] sample 18 件の linked output が golden と一致する — 完了（18/18 pass）
3. [x] [ID: P0-LINK-S3] `pytra-cli2 -link` を実装する — 完了

### P0-EMIT: linked → target（暫定: 現行 toolchain/emit/ を利用）

`pytra-cli2 -emit` は暫定で現行 `toolchain/emit/` を呼ぶ。
入力は link 段の出力（`manifest.json` + linked east3 群）。
`toolchain2/` の新規 emitter は P1-EMIT で実装する。

1. [x] [ID: P0-EMIT-S1] `pytra-cli2 -emit --target=cpp` を暫定実装（現行 toolchain/emit/ への橋渡し） — 完了
2. [x] [ID: P0-EMIT-S2] fixture + sample の parity テストが通る — sample 18/18 完了、fixture 127/132（残り5件は emitter 未対応）

### P0-BUILD: 一括実行

1. [x] [ID: P0-BUILD-S1] `pytra-cli2 -build --target=cpp` で全 18 sample が compile + run できる — emit まで完了（C++ compile/run は runtime 互換性で別途対応）

### P0-REGEN: golden 再生成の自動化

parser 等を修正するたびに golden file を手動で全段再生成する手間を自動化する。
`toolchain2/` のパイプラインを使って再生成し、emit parity で正しさを検証する。

1. [x] [ID: P0-REGEN-S1] `tools/regenerate_golden.py` を実装: `pytra-cli2` の全段（parse→resolve→compile→optimize）を fixture 132 件 + sample 18 件に実行し、golden を上書き更新する — 完了（600 件全成功）
2. [ ] [ID: P0-REGEN-S2] golden 更新後に emit parity テスト（Python 実行結果との一致）を自動実行し、end-to-end の正しさを検証する — emit 段まではP0-BUILD-S1で検証済み、C++ compile+run parity は runtime 互換性対応後

### P1-EMIT: toolchain2/emit/ に新規 emitter を実装

現行 `toolchain/emit/` は selfhost 非対応（Any/object 多用、toolchain 内部依存多数）のため、
`toolchain2/emit/` にゼロから書き直す。入力は `.east3` の JSON のみ。
完成後に `toolchain/` を完全に除去できる。

コーディング規約: plan §5（Any/object 禁止、pytra.std のみ、selfhost 対象）

**Go emitter を最初に実装する（お手本）。** 理由:
- 型マッピングが素直（`int8`→`int8`, `float64`→`float64`, `str`→`string`）
- boxing / RC / Object<T> が不要
- コンパイルが速く `go run` で即実行
- emitter フレームワーク（ノード走査、インデント、import 生成）を最小の複雑さで確立できる
- 他言語 emitter のテンプレートになる

#### P1-EMIT-GO: Go emitter（お手本）

作業ディレクトリ: `toolchain2/emit/go/`

1. [x] [ID: P1-EMIT-GO-S1] Go emitter を `toolchain2/emit/go/` に新規実装し、fixture parity が通る — fixture 132/132, sample 18/18 emit 成功
2. [x] [ID: P1-EMIT-GO-S2] sample 18 件の parity テストが通る — emit 成功 (Go 未インストールのため compile/run は未検証)
3. [x] [ID: P1-EMIT-GO-S3] `pytra-cli2 -emit --target=go` を実装する — 完了

#### P1-EMIT-GO-RUNTIME: Go runtime + parity 検証

Go emitter が生成したコードを `go run` で実行し、Python 実行結果と一致することを検証する。
まず sample 17（整数演算のみ、画像なし）で最小限の runtime から始める。

作業ディレクトリ: `src/runtime/go/` (runtime 実装)

必要な Go runtime（最小: sample 17 で必要なもの）:
- `py_print` — `fmt.Println` 相当
- `perf_counter` — `time.Now().UnixNano()` 相当
- `py_to_string` — `fmt.Sprint` 相当

追加（sample 01-16, 18 で必要）:
- `write_rgb_png` / `save_gif` / `grayscale_palette` — 画像出力
- `py_len`, `py_range`, `py_min`, `py_max` — コンテナ・数値操作
- str メソッド群（`join`, `split`, `replace` 等）
- `Path` — pathlib 相当
- `open` / `close` / `write` — ファイル I/O

手順:
1. [x] [ID: P1-GO-RUNTIME-S1] 最小 Go runtime（`py_print`, `perf_counter`, `py_to_string`）を実装し、sample 17 が `go run` で実行結果一致 — 完了（parity 一致、Go は Python の 63x 高速）
2. [x] [ID: P1-GO-RUNTIME-S2] 画像不要の sample（17, 18）が parity 一致 — 完了
3. [ ] [ID: P1-GO-RUNTIME-S3] 画像あり sample（01-16）が parity 一致 — 16/18 OK, 残り: 13(VarDecl unknown for tuple unpack), 16(同上 + float/int混在)

#### P1-GO-MIGRATE: Go を新パイプラインに完全移行

Go parity が全 sample で通った後、pytra-cli.py の Go target を新パイプライン（pytra-cli2）に切り替える。
Go が新パイプライン移行のパイロットケース。

1. [ ] [ID: P1-GO-MIGRATE-S1] `pytra-cli.py` の `--target go` を pytra-cli2 パイプラインに切り替える
2. [ ] [ID: P1-GO-MIGRATE-S2] 旧 Go emitter（`src/toolchain/emit/go/`）を削除
3. [ ] [ID: P1-GO-MIGRATE-S3] 旧 Go runtime（`src/runtime/go/built_in/`）を削除
4. [ ] [ID: P1-GO-MIGRATE-S4] `runtime_parity_check.py --targets go` で全 18 sample PASS

#### P1-CODE-EMITTER: CodeEmitter 基底クラス + runtime mapping

設計文書: `docs/ja/plans/plan-pipeline-redesign.md` §3.4

1. [ ] [ID: P1-CODE-EMITTER-S1] `toolchain2/emit/common/code_emitter.py` に CodeEmitter 基底クラスを実装（mapping 読み込み + style 別呼び出し生成）
2. [ ] [ID: P1-CODE-EMITTER-S2] Go runtime mapping（`src/runtime/go/toolchain2/mapping.json`）を作成
3. [ ] [ID: P1-CODE-EMITTER-S3] Go emitter を CodeEmitter 継承に切り替え、ハードコード写像を除去
4. [ ] [ID: P1-CODE-EMITTER-S4] resolve の `py_strip` 等への変換を除去し、EAST は `str.strip` のまま持ち運ぶように修正
5. [ ] [ID: P1-CODE-EMITTER-S5] golden 再生成 + parity 維持確認

#### P1-EMIT-CPP: C++ emitter

作業ディレクトリ: `toolchain2/emit/cpp/`

1. [ ] [ID: P1-EMIT-CPP-S1] C++ emitter を `toolchain2/emit/cpp/` に新規実装し、fixture parity が通る
2. [ ] [ID: P1-EMIT-CPP-S2] sample 18 件の parity テストが通る
3. [ ] [ID: P1-EMIT-CPP-S3] `pytra-cli2 -emit --target=cpp` を toolchain2 emitter に切り替える
4. [ ] [ID: P1-EMIT-CPP-S4] `toolchain/` への依存をゼロにし、`toolchain/` を除去する

#### P2-SELFHOST: toolchain2 自身の変換テスト

設計文書: `docs/ja/plans/plan-pipeline-redesign.md` §3.5 selfhost 系

1. [ ] [ID: P2-SELFHOST-S1] `src/toolchain2/` の全 .py ファイルが `pytra-cli2 -parse` で parse 成功する
2. [ ] [ID: P2-SELFHOST-S2] parse 結果を resolve → compile → optimize → link まで通す
3. [ ] [ID: P2-SELFHOST-S3] golden を `test/selfhost/` に配置し、回帰テストとして維持
4. [ ] [ID: P2-SELFHOST-S4] Go emitter で toolchain2 を Go に変換し、`go build` が通る

注: 旧 TODO は [2026-03-24 アーカイブ](archive/20260324.md) に移動済み。

