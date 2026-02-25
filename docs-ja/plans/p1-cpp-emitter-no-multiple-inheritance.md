# P1: CppEmitter の多重継承廃止

## 目的
`CppEmitter` での多重継承を廃止し、単一継承構成へ移行する。  
これにより emitter 側での型の階層的な判定依存を減らし、`isinstance()` 相当の分岐を単純化する。

## 背景
- 現在の `CppEmitter` は `CppCallEmitter` / `CppStatementEmitter` / `CppExpressionEmitter` / `CppBinaryOperatorEmitter` / `CppTriviaEmitter` / `CppTemporaryEmitter` / `CodeEmitter` を多重継承している。
- これは責務分割の便益はある一方、`isinstance` ベースの実行時判定や呼び出し解決の経路を複雑化しやすい。
- 今後の `hooks` 低減と `CppEmitter` 体積縮小を安全に進めるため、クラス設計を単一継承 + 明示的委譲（または関数注入）へ統一する。

## 方針
1. `CppEmitter` は最終的に `CodeEmitter` の単一継承に収束する。
2. 追加責務は以下いずれかへ移す。
   - `self._call_emitter`, `self._statement_emitter`, `self._expression_emitter` などの専用ヘルパインスタンス化
   - 現在のクラス群を「状態を持たないヘルパ関数群」に寄せる
3. 既存の外部 API (`cpp_emitter.py` 以外からの直接参照) への影響を最小化するため、`CppEmitter` は軽量なデリゲーション API を維持する。
4. `isinstance` 相当の判定は型ヒントやフラグより、処理種別の明示的識別子へ寄せる。

## 受け入れ条件
- `CppEmitter` が多重継承をしていないこと。
- `docs-ja/plans/p1-cpp-emitter-reduce.md` の既存責務分離進度と整合すること。
- `python3 test/unit/test_py2cpp_smoke.py` と `python3 tools/check_py2cpp_transpile.py` が通過すること。
- 既存生成物の可読性・回帰が壊れていないこと。

## 参照・補助
- `docs-ja/plans/p1-cpp-emitter-reduce.md`
- `src/hooks/cpp/emitter/cpp_emitter.py`

## Todo の粒度分割（提案）
- `P1-CPP-EMIT-NOMI-01` 親タスク
  - `P1-CPP-EMIT-NOMI-01-S1`: 多重継承を解くためのデータ/ライフサイクル設計を決める
  - `P1-CPP-EMIT-NOMI-01-S2`: `CppEmitter` の初期化経路の委譲移行
  - `P1-CPP-EMIT-NOMI-01-S3`: `call/expr/stmt` 系メソッド呼び出しのデリゲーション導線を切り出し
  - `P1-CPP-EMIT-NOMI-01-S4`: 既存テストの回帰と性能劣化の確認

## 決定ログ

- [2026-02-25] [ID: P1-CPP-EMIT-NOMI-01-S1]
  - 実施内容: `src/hooks/cpp/emitter/cpp_emitter.py` を単一継承 (`CodeEmitter` のみ) に変更。
  - 実装手段: `CppCallEmitter`/`CppStatementEmitter`/`CppExpressionEmitter`/`CppBinaryOperatorEmitter`/`CppTriviaEmitter`/`CppTemporaryEmitter` の各メソッドを、クラス定義外のアタッチ処理で `CppEmitter` に委譲注入。
  - 追加した検証: `PYTHONPATH=src python3 tools/check_py2cpp_transpile.py` で `checked=132 ok=132 fail=0 skipped=6` を確認。

- [2026-02-25] [ID: P1-CPP-EMIT-NOMI-01-S2]
  - 実施内容: `isinstance`/型チェック系の type-id Name-call 分岐を `_type_id_name_call_kind` で明示分類し、`_build_type_id_expr_from_call_name` / `render_call` / `_render_repr_expr` 側の分岐を簡素化。
  - 対応内容: `isinstance/issubclass`/`py_*` 系 type_id 呼び出しを一元化フラグで判定し、未loweringケースの判定ルートとエラー生成を明確化。
  - 追加した検証: `PYTHONPATH=src python3 tools/check_py2cpp_transpile.py` で `checked=131 ok=131 fail=0 skipped=6` を確認。
