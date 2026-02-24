# EAST1/EAST2/EAST3 三段構成仕様（設計ドラフト）

この文書は、Pytra の中間表現を 3 段階（`EAST1` / `EAST2` / `EAST3`）へ分離する設計仕様を定義する。  
目的は、hooks の肥大化を防ぎ、`Any/object` 境界（boxing/unboxing, dispatch, iterable）の意味論を backend 非依存で確定させること。

位置づけ:
- 現行実装準拠の仕様は [spec-east.md](./spec-east.md)。
- 本書は次期構成（段階移行前提）の仕様であり、`EAST2 -> EAST3` 導入時の正本とする。
- 連結段の詳細（`type_id` 確定、manifest、中間ファイル再開）は [spec-linker.md](./spec-linker.md) に分離する。
- 実装順とファイル責務対応は [spec-east123-migration.md](./spec-east123-migration.md) を参照する。
- 仕様優先順位は `spec-east123`（上位） -> `spec-linker`（下位）とする。
- 元案は `materials/refs/spec-east123.md`。

## 1. 背景

現状は「単一 EAST + backend hooks」で運用しており、次の問題がある。

- Python 寄りの高位表現が backend 側まで流れ、hooks が意味論 lowering を抱えやすい。
- `type_id/native`、boxing/unboxing、iterable など横断ロジックが言語別分岐へ漏れる。
- hooks が「最終出力差分」ではなく「実質コンパイラ本体」の役割を持ち始める。

## 2. 目的

1. 高位正規化と core lowering を分離する。  
2. `EAST3` で意味論を確定し、backend は薄くする。  
3. hooks を「構文差分の最終調整」に限定する。  
4. `--object-dispatch-mode {type_id,native}` を全境界機能で一貫適用する。

## 3. 非目標

- 新しい最適化器の全面導入。
- 既存全ノードの一括再設計（段階移行を前提）。
- CPython AST 依存実装（selfhost 制約により前提外）。

## 4. 用語

- `EAST1`: パーサ直後 IR（構文寄り）。
- `EAST2`: 正規化 IR（高位意味を整理）。
- `EAST3`: Core IR（backend 非依存で意味論確定済み）。
- `dispatch mode`: `--object-dispatch-mode {type_id,native}` の選択結果。

## 5. ルートスキーマ（全段共通）

各段のルートは `Module` とし、最低限次を持つ。

- `kind`: `Module`
- `east_stage`: `1 | 2 | 3`
- `schema_version`: 整数（例: `1`）
- `source_path`: 入力パス
- `body`: 文配列
- `meta`: 追加メタ
- `meta.dispatch_mode`: `native | type_id`

不変条件:

1. `east_stage` とノード形状が一致する。  
2. `meta.dispatch_mode` は全段で保持し、値は段間で不変とする。  
3. dispatch mode の意味適用は `EAST2 -> EAST3` の 1 回だけで行う。  
4. backend は `EAST3` の意味論を変更しない。

## 6. 三段階の責務

### 6.1 EAST1（Parsed）

責務:

- 入力コードを loss-minimal に構造化する。
- source span / trivia（必要なら）を保持する。
- Python 構文の差異をそのまま残してよい。

許容:

- `for ... in range(...)` が call のままでもよい。
- `len`, `iter`, `isinstance` など builtins は未lower でよい。
- 型情報は未確定でよい。

不許可:

- backend 固有ノードの混入。
- runtime 関数名への直接焼き込み（例: `py_iter_or_raise` 直接埋め込み）。

### 6.2 EAST2（Normalized）

責務:

- Python 構文糖衣を backend 非依存に正規化する。
- ノード形状を安定化し、後段解析を単純化する。

最小要件:

- `for ... in range(...)` を `ForRange` / `RangeExpr` へ正規化。
- comprehension / ifexp / tuple unpack などを一貫形式へ統一。
- import / symbol 参照を canonical form へ正規化。
- `resolved_type` 等の型解決結果を可能な範囲で付与。

注記:

- 現行の「既存 EAST」は原則 `EAST2` 相当として扱う（移行起点）。

### 6.3 EAST3（Core）

責務:

- backend が追加解釈しなくてもコード生成可能な意味論へ lower する。
- `Any/object` 境界挙動を明示ノードで固定する。
- dispatch mode を反映済みの表現を持つ。

最小要件:

- boxing/unboxing を明示命令化（例: `Box`, `Unbox`, `CastOrRaise`）。
- bool/len/str の動的経路を明示命令化（例: `ObjBool`, `ObjLen`, `ObjStr`）。
- iterable を明示命令化（例: `ObjIterInit`, `ObjIterNext`）。
- `type_id` 判定（`isinstance` / `issubclass` / subtype）を明示命令化し、backend は命令写像のみを行う。
- 可能な限り言語非依存意味論（主要 built-in lower 含む）を EAST3 命令へ寄せ、backend/hook に意味論実装を残さない。
- `ForCore` は `iter_mode` を必ず保持（`static_fastpath` or `runtime_protocol`）。
- `runtime_protocol` の場合、`iter_plan.dispatch_mode` を必須化する。

不変条件:

1. backend は `EAST3` の意味論を再判断しない。  
2. hooks はノードの意味を変更しない。  
3. `Any/object` 境界に暗黙フォールバック（`0` / `false` / 空反復）を持ち込まない。

## 7. パイプライン仕様

1. `Source -> EAST1`
   - selfhost parser で構文木を生成。
2. `EAST1 -> EAST2`（Normalize pass）
   - 構文糖衣とバリエーションを整理。
3. `EAST2 -> EAST3`（Core Lowering pass）
   - dispatch mode と runtime 契約を反映して core 命令へ変換。
4. `EAST3 -> TargetEmitter`
   - 言語構文へ写像。意味論変更は禁止。

## 8. dispatch mode の適用点

`--object-dispatch-mode` はコンパイル開始時に確定し、`EAST1`/`EAST2`/`EAST3` の `meta.dispatch_mode` へ同値を保持する。  
意味論としての適用は `EAST2 -> EAST3` で 1 回だけ行い、`RuntimeIterForPlan.dispatch_mode` へ埋め込む。  
この段階より後では、モード切替の意味論判断を行わない。

### 8.1 `type_id` モード

- `Any/object` 境界の boxing/unboxing/bool/len/str/iter を type_id dispatch 命令へ lower。
- 同一入力で決定的な dispatch を保証する。

### 8.2 `native` モード（既定）

- 同境界機能で type_id dispatch を生成しない。
- C++ は virtual/hook、JS/TS は native 機構（`Symbol.iterator` 等）を利用する命令へ lower。

禁止:

- 機能ごとの混在（例: iterable だけ type_id）。
- backend 側で mode 再判定して命令を差し替えること。

## 9. ノード契約（抜粋）

### 9.1 For / ForCore

- `EAST2`: `For(iter_expr, target, body, orelse, ...)`
- `EAST3`: `ForCore(iter_mode, iter_plan, target_plan, body, orelse, ...)`

`iter_plan` 形状:

- `StaticRangeForPlan`
  - `kind`: `StaticRangeForPlan`
  - `start`, `stop`, `step`: 式
- `RuntimeIterForPlan`
  - `kind`: `RuntimeIterForPlan`
  - `iter_expr`: 式
  - `dispatch_mode`: `native | type_id`
  - `init_op`: `ObjIterInit`
  - `next_op`: `ObjIterNext`

### 9.2 Any/object 境界（Core 命令）

`EAST3` では、次の命令ノードで境界挙動を明示する。

- `Box(value, target=object)`
- `Unbox(value, target=T, on_fail=raise)`
- `CastOrRaise(value, target=T)`
- `ObjBool(value)`
- `ObjLen(value)`
- `ObjStr(value)`
- `ObjIterInit(value)`
- `ObjIterNext(iter)`

### 9.3 type_id 判定（Core 命令）

`EAST3` では `type_id` 判定も命令ノードとして扱う。

- `ObjTypeId(value)`
- `IsSubtype(actual_type_id, expected_type_id)`
- `IsInstance(value, expected_type_id)`
- `IsSubclass(actual_type_id, expected_type_id)`

規約:
- `type_id` 判定は `EAST3` で確定し、backend 側で意味論再判断しない。
- C++ など backend は runtime API への写像のみを担当する。
- backend による判定ロジックの直接実装（文字列比較や個別分岐の再実装）は禁止する。

### 9.4 例外契約

- non-iterable の `for` は `TypeError` 相当。
- `len` 未対応は `TypeError` 相当。
- `CastOrRaise` は型不一致で失敗を隠蔽しない。

実装側は上記失敗を既存エラー契約へマッピングして返す（`kind`, `message`, `source_span`, `hint`）。

## 10. hooks の責務境界

許可:

- 文法差分（`for (...)` vs `for ... of ...`）。
- include/import、namespace/package 構文差分。
- 表記最適化（括弧、省略可能な型注釈）。

禁止:

- dispatch mode の再判断。
- boxing/unboxing の意味論変更。
- iterable 判定ロジックの再実装。
- 言語非依存意味論を backend/hook 側へ新規実装すること（IR-first 原則に反する追加）。

## 11. 具体例

入力:

```python
def f(x: object, xs: list[int]) -> int:
    s: int = 0
    for a in xs:
        s += a
    for b in x:
        s += b
    return s
```

EAST2（概略）:

```json
{
  "kind": "FunctionDef",
  "name": "f",
  "body": [
    {"kind": "For", "iter": {"kind": "Name", "id": "xs"}, "target": {"kind": "Name", "id": "a"}},
    {"kind": "For", "iter": {"kind": "Name", "id": "x"}, "target": {"kind": "Name", "id": "b"}}
  ]
}
```

EAST3（概略）:

```json
{
  "kind": "FunctionCore",
  "name": "f",
  "body": [
    {
      "kind": "ForCore",
      "iter_mode": "static_fastpath",
      "iter_plan": {
        "kind": "StaticRangeForPlan",
        "start": {"kind": "Const", "value": 0},
        "stop": {"kind": "Len", "arg": {"kind": "Name", "id": "xs"}},
        "step": {"kind": "Const", "value": 1}
      },
      "target_plan": {"kind": "NameTarget", "id": "a"}
    },
    {
      "kind": "ForCore",
      "iter_mode": "runtime_protocol",
      "iter_plan": {
        "kind": "RuntimeIterForPlan",
        "iter_expr": {"kind": "Name", "id": "x"},
        "dispatch_mode": "native",
        "init_op": "ObjIterInit",
        "next_op": "ObjIterNext"
      },
      "target_plan": {"kind": "NameTarget", "id": "b"}
    }
  ]
}
```

## 12. 移行方針

1. 既存 EAST を `EAST2` として別名導入（挙動維持）。  
2. `EAST2 -> EAST3` pass を最小ノードから導入（For/Any境界優先）。  
3. backend を `EAST3` 入力へ段階移行。  
4. hooks から意味論 lowering を削除。  
5. 最終的に `EAST2` と `EAST3` の責務境界をテストで固定。

移行期 API:

- `load_east(...)` は当面 `EAST2` を返す。
- 新 API `load_east3(...)` を追加する。
- 最終的に emitter 入力を `EAST3` へ一本化する。

## 13. テスト戦略

- unit:
  - `EAST1 -> EAST2` 正規化差分テスト
  - `EAST2 -> EAST3` lowering 契約テスト
  - dispatch mode（`type_id` / `native`）で EAST3 が全面切替されること
- schema:
  - `east_stage` / `schema_version` / `meta.dispatch_mode` の必須項目検証
  - `ForCore.iter_plan.kind` ごとの必須キー検証
- codegen:
  - backend が EAST3 を再解釈せず出力できること
  - hooks 無効時でも core 意味論が崩れないこと
- e2e:
  - 既存 fixture の出力一致（許容差分を明示）
  - selfhost build/transpile の回帰

## 14. 受け入れ基準（計測可能）

1. `EAST3` 単独で backend 生成が可能。  
2. hooks から意味論 lowering 分岐が段階的に減少する。  
3. `--object-dispatch-mode` が境界機能全体を一括切替できる。  
4. `native` 既定で既存導線を維持しつつ、`type_id` モードでも同一失敗契約を満たす。  
5. `ForCore.iter_mode` と `RuntimeIterForPlan.dispatch_mode` が全ケースで存在する。  

確認コマンド（最低）:

- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/check_py2js_transpile.py`
- `python3 tools/check_py2ts_transpile.py`
- `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`
