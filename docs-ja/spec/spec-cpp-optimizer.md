# C++ Optimizer 仕様

<a href="../../docs/spec/spec-cpp-optimizer.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

この文書は、`EAST3` から C++ backend へ lower した後段で適用する `CppOptimizer` 層の責務と契約を定義する。

## 1. 目的

- C++ backend 固有の最適化を emitter から分離し、`CppEmitter` の責務を縮小する。
- 生成前（構造化 IR 段）で意味保存最適化を行い、可読性/性能/保守性を改善する。
- 文字列出力後の壊れやすい最適化（正規表現置換）を避ける。

## 2. 非目標

- `EAST3` 共通最適化層（`EAST3 -> EAST3`）の置き換え。
- C++ コンパイラ（`g++/clang++`）が担当すべき機械最適化の代替。
- 文字列化済み `.cpp` へのテキストベース rewrite。

## 3. パイプライン位置

標準順序:

1. `EAST2 -> EAST3` lowering
2. `EAST3 Optimizer`（共通）
3. `EAST3 Optimizer cpp`（任意）
4. `EAST3 -> C++` lowering（backend IR 化）
5. `CppOptimizer`（C++ IR -> C++ IR）
6. `CppEmitter`（C++ IR -> C++ source text）
7. C++ compiler optimization（`-O2/-O3` など）

補足:

- `CppOptimizer` は text ではなく構造化表現（C++ IR/AST）を入力に取る。
- 現行実装で C++ IR が未分離でも、責務上は optimizer モジュールを分け、段階的に独立させる。

## 4. `CppOptimizer` と `CppEmitter` の責務境界

`CppOptimizer` の責務:

- C++ backend 固有の意味保存最適化。
- lowering で導入された冗長テンポラリ/冗長 cast の削減。
- C++ 側の構文化に寄せるための IR 正規化（例: counted loop の for-loop 形状確定）。
- 以後の emitter が単純な「構文出力器」として動ける形への整理。

`CppEmitter` の責務:

- IR ノードを C++ 構文へ決定的に出力する。
- インデント、改行、トリビア、include 整形などの表現責務。
- 最小限の局所分岐（構文都合）を除き、データフロー解析や最適化ロジックを持たない。

境界ルール:

- 意味保存のために解析が必要な変換は `CppOptimizer` 側に置く。
- 「同じ入力 IR から同じ文字列を生成する」責務を `CppEmitter` へ集中させる。

## 5. 入出力契約

入力:

- `EAST3 -> C++ lowering` 後の C++ backend IR（モジュール単位）。
- 型情報、借用/所有情報、副作用判定用メタ情報を参照可能であること。

出力:

- 同じ C++ backend IR（`Cpp IR -> Cpp IR`）。
- 次を維持すること。
  - 評価順序
  - 例外発生タイミング
  - 副作用の有無/回数
  - RC/所有権意味論（`rc<T>`、`py_*` runtime API 契約）

禁止事項:

- runtime API 契約を暗黙変更する rewrite。
- 証明不十分な最適化の適用（fail-open）。

## 6. Pass Manager 契約

- `CppOptimizer` は順序付き pass 列で構成する。
- pass は deterministic であること。
- 同一入力/同一設定で同一出力を保証する。

`PassContext`（推奨）:

- `opt_level`
- `target_cpp_std`（例: c++17）
- `debug_flags`
- `runtime_mode`（bounds/div/mod/negative-index 等の変換モード）

`PassResult`（推奨）:

- `changed: bool`
- `change_count: int`
- `warnings: list[str]`
- `elapsed_ms: float`

## 7. 最適化レベル

- `O0`:
  - `CppOptimizer` 無効（pass 0本）。
- `O1`（既定）:
  - 局所的で安全証明しやすい変換のみ。
- `O2`:
  - `O1` + ループ/テンポラリ整理など中程度の変換。

注記:

- ここでの `O*` は「生成前最適化レベル」。
- C++ コンパイラの `-O*` とは別レイヤであり、混同しない。

## 8. v1 推奨 pass

| Pass | 目的 | 代表変換 | ガード |
| --- | --- | --- | --- |
| `CppDeadTempPass` | 冗長一時変数削減 | 1回しか使わない純粋 tmp をインライン化 | 副作用なし/評価順序維持 |
| `CppNoOpCastPass` | 無意味 cast 削除 | 実型一致 cast の除去 | 型一致を静的証明 |
| `CppConstConditionPass` | 定数条件分岐整理 | `if (true) A else B` -> `A` | 片枝削除で副作用変化なし |
| `CppRangeForShapePass` | counted-loop の for 形状確定 | C++ for node への正規化 | 反復境界・増分・評価順序を保持 |
| `CppRuntimeFastPathPass` | runtime 呼び出し簡約 | 型確定時のみ軽量 helper へ | 既存 runtime 契約と完全同値 |

## 9. CLI / デバッグ契約

推奨オプション:

- `--cpp-opt-level {0,1,2}`
- `--cpp-opt-pass +PASS,-PASS`
- `--dump-cpp-ir-before-opt <path>`
- `--dump-cpp-ir-after-opt <path>`
- `--dump-cpp-opt-trace <path>`

互換運用:

- 既存 `-O*` オプションがある場合、移行期間は `--cpp-opt-level` とマッピングし、将来分離を許容する。

## 10. テスト契約

最小要件:

- pass 単体テスト（IR in/out 差分検証）
- パイプライン統合テスト（optimizer 有無で生成 C++ がコンパイル可能）
- parity テスト（Python 実行結果と一致）
- `sample/` 回帰（性能劣化監視を含む）

必須観点:

- `O0` と `O1/O2` で意味論が一致すること。
- 「適用すべきでないケース」で pass が抑止されること。

## 11. 推奨ファイル配置

- `src/hooks/cpp/optimizer/cpp_optimizer.py`
- `src/hooks/cpp/optimizer/passes/*.py`
- `src/hooks/cpp/optimizer/context.py`
- `src/hooks/cpp/optimizer/trace.py`

## 12. 導入フェーズ

### Phase 1

- optimizer エントリ追加（実質 no-op）
- `O0/O1`、trace、2 pass（`CppDeadTempPass`, `CppNoOpCastPass`）導入
- emitter 内の同等ロジックを移設

### Phase 2

- ループ系 pass（`CppRangeForShapePass`）導入
- runtime 呼び出し簡約 pass の限定導入
- `CppEmitter` の分岐/解析ロジックを更に削減

### Phase 3

- 指標ベース最適化（pass 有効化方針の固定）
- 回帰検知の自動化（速度・サイズ・互換）

## 13. 互換性方針

- 既存 `py2cpp.py` CLI の互換を優先する。
- 切り分け可能性のため `O0` を常に提供する。
- 既存 fixture/sample の stdout/成果物一致を破る変更は受け入れない。
