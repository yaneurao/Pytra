# EAST3 Optimizer 仕様

<a href="../../docs/spec/spec-east3-optimizer.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

この文書は `EAST3` 最適化層（`EAST3 -> EAST3`）の責務、契約、段階導入を定義する。

## 1. 目的

- `EAST3` を emitter 直前で最適化し、生成コード品質と実行性能を改善する。
- 最適化ロジックを emitter から分離し、保守性を向上させる。
- 言語横断で再利用できる「共通最適化」と、必要な場合の「言語別最適化」を分離する。

## 2. 非目標

- `EAST2` 以前の構文/型解決ロジックの置き換え。
- backend 固有の最終コード整形や文法糖の責務代替。
- backend 文法への直接 lower（例: C++ の `for (init; cond; inc)` 構文生成）。
- 意味変化を伴う最適化（厳密互換を崩す最適化）。

## 3. パイプライン位置

標準パイプラインは次の順序を正本とする。

1. `EAST2 -> EAST3` lower（`east2_to_east3_lowering.py`）
2. `EAST3 Optimizer`（共通）
3. `EAST3 Optimizer <lang>`（任意、言語別）
4. 各 emitter

補足:

- Optimizer は `EAST3` のみを入力に取る。
- `EAST3` 生成前（`EAST2`段）に最適化ロジックを分散配置しない。

## 4. 入出力契約

### 4.1 入力

- `kind == "Module"` の `EAST3` 文書。
- `east_stage == 3` を満たすこと。

### 4.2 出力

- 返り値は同じく `EAST3` 文書（`EAST3 -> EAST3`）。
- 次の不変条件を満たすこと。
  - `east_stage` は `3` のまま。
  - `schema_version` は互換範囲内で維持。
  - `source_span` / `repr` / `resolved_type` / `borrow_kind` / `casts` を破壊しない。
  - `main_guard_body` 分離契約を維持する。

## 5. セーフティ契約（意味保存）

- 最適化は意味保存を最優先とする。
- 次を変更してはならない。
  - 評価順序
  - 例外発生タイミング
  - 副作用の有無/回数
  - 短絡評価の成立条件
- 副作用の可能性がある式をまたぐ再配置は禁止する。
- 不確実な変換は適用せずスキップする（fail-closed）。

## 6. 構成（Pass Manager）

`EAST3 Optimizer` は「Pass の列」で構成する。

- `PassContext`
  - `opt_level`
  - `target_lang`（空文字可）
  - `debug_flags`
- `PassResult`
  - `changed: bool`
  - `change_count: int`
  - `warnings: list[str]`
  - `elapsed_ms: float`

実行契約:

- Pass は決定的（deterministic）であること。
- 同一入力・同一オプションで同一出力を保証すること。
- Pass 実行順を固定し、順序依存を明示すること。

## 7. オプトレベル

- `O0`（無効）:
  - Optimizer を実行しない。
- `O1`（既定）:
  - 局所的かつ意味保存が強いパスのみ。
- `O2`:
  - `O1` に加え、ループ系の保守的最適化を許可。

## 8. v1 で盛り込む推奨パス

| Pass | 目的 | 代表変換 | ガード |
| --- | --- | --- | --- |
| `NoOpCastCleanupPass` | 無意味 cast の除去 | `static_cast(T, x)` で `x:T` を削除 | 型一致が静的に証明できる場合のみ |
| `LiteralCastFoldPass` | リテラル cast 畳み込み | `cast<int64>(42)` -> `42` | リテラル + 無損失変換のみ |
| `RedundantWrapperCtorPass` | 冗長ラッパ構築除去 | `bytes(bytes_expr)` の冗長ケース削除 | 一時値かつ alias リスクなし |
| `LoopInvariantHoistLitePass` | ループ不変式の外出し | 定数分母や不変計算を preheader へ移動 | 副作用なし式のみ |
| `StrengthReductionFloatLoopPass` | 乗除算コスト削減 | `x / C` -> `x * invC` | `C` が不変かつ浮動小数式 |
| `DeadTempCleanupPass` | 不要一時変数除去 | 未使用一時の削除 | 参照・副作用なし |
| `RangeForCanonicalizationPass` | `for ... in range(...)` 正規化 | backend 非依存のカウントループ表現へ統一 | `range` 引数の評価順序/副作用/境界条件を保存できる場合のみ |
| `UnusedLoopVarElisionPass` | 未使用ループ変数の束縛削減 | 実体未使用の反復変数バインドを省略 | 変数名ではなくデータフローで「未使用」を証明できる場合のみ |

### 8.1 `for ... in range(...)` 最適化の責務境界

- 共通 Optimizer は `for ... in range(...)` を backend 非依存の正規化表現に変換してよい。
- `for _ in range(5)` 形式は、`_` という識別子名を根拠にせず、実使用解析で未使用が証明された場合のみ最適化対象とする。
- 次のケースを静的に安全と証明できない場合は変換を適用しない。
  - ループ変数が本体・`else`・ループ後で参照される。
  - クロージャ捕捉で観測される可能性がある。
  - 動的名前解決（`locals`/`globals`/`vars`/`eval` 等）で観測される可能性がある。
- C++ の `for (i = 0; i < n; ++i)` のような言語構文化は、共通 Optimizer ではなく `EAST3 -> <lang>` lower / emitter の責務とする。

## 9. 言語別最適化層

- 共通層の後段に `east3_optimizer_<lang>.py` を任意で追加できる。
- 言語別層は次を守る。
  - 共通層と同じ意味保存契約。
  - 言語固有の codegen 都合に限定する。
  - 言語構文化（例: C++ の古典 for 構文）は、この層または emitter 側で扱う。
  - 共通で表現可能な最適化を言語別層へ重複実装しない。

推奨ファイル配置:

- `src/pytra/compiler/east_parts/east3_optimizer.py`
- `src/pytra/compiler/east_parts/east3_optimizer_cpp.py`
- `src/pytra/compiler/east_parts/east3_opt_passes/*.py`

## 10. CLI / デバッグ契約

推奨オプション:

- `--east3-opt-level {0,1,2}`（既定 `1`）
- `--east3-opt-pass +PASS,-PASS`（個別 on/off）
- `--dump-east3-before-opt <path>`
- `--dump-east3-after-opt <path>`
- `--dump-east3-opt-trace <path>`

推奨トレース内容:

- 実行した pass 順序
- pass ごとの `changed/change_count/elapsed_ms`
- 最終集計（総変更数、総時間）

## 11. テスト契約

最小要件:

- pass 単体テスト（入力 EAST3 / 出力 EAST3 の差分検証）
- 構文・型不変条件テスト（`east_stage`, `schema_version`, `resolved_type` など）
- 回帰テスト（`sample/` 主要ケース）
- 既存 parity テストでの出力整合（stdout/成果物）

特に確認すべき観点:

- O0 と O1/O2 の切替で挙動が安定すること。
- 「未適用にすべきケース」で変換が抑止されること。

## 12. 導入フェーズ

### Phase 1

- Pass Manager の骨格実装
- `O0/O1` とトレース出力
- `NoOpCastCleanup` / `LiteralCastFold` の導入

### Phase 2

- ループ系最適化（`LoopInvariantHoistLite`, `StrengthReductionFloatLoop`）
- language-specific optimizer の入口追加

### Phase 3

- プロファイル駆動の pass 有効化方針
- 長期運用のベースライン計測と自動回帰検知

## 13. 互換性方針

- 既存 emitter API は維持する。
- 既定は `O1` とするが、問題切り分けのため常に `O0` を提供する。
- Optimizer 追加時は、既存 fixture / sample の出力一致を破らないことを必須条件とする。
