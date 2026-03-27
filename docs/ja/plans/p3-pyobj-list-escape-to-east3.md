<a href="../../en/plans/p3-pyobj-list-escape-to-east3.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P3: pyobj list alias escape 解析を EAST3 パスへ移行

最終更新: 2026-03-21

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P3-PYOBJ-LIST-ESCAPE`

## 背景

C++ emitter (`cpp_emitter.py`) は `_collect_pyobj_runtime_list_alias_names` で、pyobj モード（動的型）の typed list 変数が他変数にエイリアスされるか否かを独自に分析し、ハンドル経由（参照カウント付きポインタ）かスタック直置きかを判定している。

この分析は本質的に **escape 解析**（変数が定義スコープ外に漏れるか判定する）であり、以下の問題がある:

1. **emitter 内に埋め込まれている**: 言語非依存の意味論分析が C++ emitter 固有コードに閉じている
2. **EAST3 に既存の escape/lifetime パスがある**: `non_escape_interprocedural_pass.py` と `lifetime_analysis_pass.py` が `east3_opt_passes/` に存在しており、同種の分析基盤が既にある
3. **他 backend に共有されない**: Dart/Zig 等が同様の最適化を行う場合、各 emitter で再実装が必要になる

### 現行コードの所在

| ファイル | 役割 |
|---|---|
| `cpp_emitter.py:_collect_pyobj_runtime_list_alias_names` | 関数本体を走査し、`list[T]` 型の変数がエイリアスされるかを固定点反復で追跡 |
| `cpp_emitter.py:_is_pyobj_runtime_list_alias_name` | 判定結果を参照 |
| `analysis.py:_collect_assigned_name_types` | 変数の代入型を再帰収集（list alias 分析で使用） |
| `type_bridge.py:_is_pyobj_ref_first_list_type` | typed list の型判定 |

### 関連する既存 EAST3 パス

| パス | 内容 |
|---|---|
| `non_escape_call_graph.py` | 関数間の呼び出しグラフ構築 |
| `non_escape_interprocedural_pass.py` | 引数の non-escape 判定（関数間） |
| `lifetime_analysis_pass.py` | 関数内 CFG + def-use + liveness 分析 |

## 設計方針

- `lifetime_analysis_pass.py` の def-use 解析を拡張し、list 変数のエイリアス伝播を検出する
- 結果を FunctionDef の `meta` に `list_alias_escape_v1` として付与する
- C++ emitter は `meta` を参照するだけに変え、`_collect_pyobj_runtime_list_alias_names` を除去する
- `_collect_assigned_name_types` は pyobj list alias 分析でのみ使われているため、EAST3 移行後に除去可能

## 対象

- `src/toolchain/compile/east3_opt_passes/lifetime_analysis_pass.py` — list alias escape 拡張
- `src/toolchain/emit/cpp/emitter/cpp_emitter.py` — `_collect_pyobj_runtime_list_alias_names` 除去
- `src/toolchain/emit/cpp/emitter/analysis.py` — `_collect_assigned_name_types` 除去（依存消滅後）

## 非対象

- `non_escape_interprocedural_pass.py` の拡張（関数間 escape はスコープ外）
- Dart/Zig/Julia emitter への ref-first 最適化導入（別タスク）
- `_is_pyobj_ref_first_list_type` の移行（型判定は emitter 固有の C++ 表現選択なので emitter に残す）

## 受け入れ基準

- [ ] EAST3 パスが FunctionDef.meta に list alias escape 情報を付与する
- [ ] C++ emitter が EAST3 meta から escape 情報を読み取り、既存と同等の ref-first 判定を行う
- [ ] `_collect_pyobj_runtime_list_alias_names` を C++ emitter から除去する
- [ ] `_collect_assigned_name_types` を除去する（他に依存がなくなった場合）
- [ ] 既存 C++ テスト（pyobj list 関連）がリグレッションしない

## 子タスク

- [ ] [ID: P3-PYOBJ-LIST-ESCAPE-01] lifetime_analysis_pass に list alias escape 解析を追加し、FunctionDef.meta に結果を付与する
- [ ] [ID: P3-PYOBJ-LIST-ESCAPE-02] C++ emitter を meta 参照に切り替え、`_collect_pyobj_runtime_list_alias_names` を除去する
- [ ] [ID: P3-PYOBJ-LIST-ESCAPE-03] `analysis.py` の `_collect_assigned_name_types` を除去する（依存消滅確認後）
- [ ] [ID: P3-PYOBJ-LIST-ESCAPE-04] ユニットテストを追加し、既存 pyobj list テストのリグレッションがないことを検証する

## 決定ログ

- 2026-03-21: P0-19（block-scope hoist）の実装中に C++ emitter の `_collect_assigned_name_types` が hoist 以外に pyobj list alias 分析で使われていることを確認。これは escape 解析であり EAST3 パスで解決すべきと判断し、P3 として起票。
