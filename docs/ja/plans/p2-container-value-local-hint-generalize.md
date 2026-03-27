<a href="../../en/plans/p2-container-value-local-hint-generalize.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P2: ContainerValueLocalHintPass 汎化（全 backend 共通化）

最終更新: 2026-03-23

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P2-CONTAINER-HINT-GENERALIZE-01`

## 背景

- C++ backend は `CppListValueLocalHintPass` で「この list ローカルは値型で持てる」ヒントを生成し、linker 経由で `container_ownership_hints_v1` に格納している。
- しかしこのパスは `target_lang != "cpp"` で即時 return し、linker の `_materialize_container_hints` も `target != "cpp"` で空 dict を返す。
- 結果として非 C++ backend は escape 解析結果を利用できず、emitter 内の局所 `ref_vars` 追跡に頼っている。
- パス内部のロジック（ローカル list の escape 判定）は言語非依存であり、C++ 固有の制約はない。

## 目的

- `CppListValueLocalHintPass` を言語非依存の `ContainerValueLocalHintPass` に汎化する。
- 全 backend が linker 経由で `container_ownership_hints_v1` を受け取れるようにする。
- C++ の既存動作に回帰を起こさない。

## 対象

- `src/toolchain/compile/east3_opt_passes/cpp_list_value_local_hint_pass.py` → リネーム + 汎化
- `src/toolchain/compile/east3_opt_passes/__init__.py` — 登録変更
- `src/toolchain/link/global_optimizer.py` — target フィルタ除去 + ヒントキー汎化
- テスト

## 非対象

- dict/set の値型縮退ヒント追加（list のみで開始、将来拡張）
- 各 backend emitter のヒント利用側変更（本タスクはヒント供給側のみ）
- escape 解析パス自体の改善

## 受け入れ基準

1. `ContainerValueLocalHintPass` が全 target_lang で実行される。
2. linker の `container_ownership_hints_v1` が全 backend で populated される。
3. C++ の既存ヒント出力に差分がない。
4. 既存テスト（unit + selfhost）に回帰がない。

## 変更計画

### S1: パス汎化

1. `cpp_list_value_local_hint_pass.py` をコピーして `container_value_local_hint_pass.py` を作成。
2. クラス名を `ContainerValueLocalHintPass` に変更。
3. `target_lang != "cpp"` ガードを除去。
4. ヒントキーを `cpp_value_list_locals_v1` → `container_value_locals_v1` に変更。
5. `__init__.py` で旧パスを新パスに置換。

### S2: linker 汎化

1. `_materialize_container_hints` の `target != "cpp"` ガードを除去。
2. `CppListValueLocalHintPass` → `ContainerValueLocalHintPass` に変更。
3. `_extract_cpp_container_hints` → `_extract_container_hints` に改名。
4. `global_optimizer.py` のヒントキーを `container_value_locals_v1` に統一。
5. C++ 互換: `cpp_value_list_locals_v1` を `container_value_locals_v1` の alias として残す。

### S3: テスト・検証

1. 既存 C++ テストの回帰確認。
2. 非 C++ target でヒントが populated されることの unit test 追加。

## 決定ログ

- 2026-03-23: `mutates_params` 提案を「runtime が値型であることの IR ワークアラウンド」として却下。代わりに runtime 参照ラッパー導入 + optimizer ヒント汎化を採用。
- 2026-03-23: S1-S3 完了。`ContainerValueLocalHintPass` が全 target で実行される。linker の `_materialize_container_hints` から target ガード除去済み。非 C++ target（go/swift/rs/java/kotlin）でヒント生成を unit test で固定。
- 2026-03-23: 互換 alias（`CppListValueLocalHintPass` クラス alias、`cpp_value_list_locals_v1` ヒントキー）を全箇所から除去。C++ emitter・linker・テストすべて新キー `container_value_locals_v1` に統一。
