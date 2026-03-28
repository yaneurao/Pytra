<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

最終更新: 2026-03-27

## 文脈運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 着手対象は「未完了の最上位優先度ID（最小 `P<number>`、同一優先度では上から先頭）」に固定し、明示上書き指示がない限り低優先度へ進まない。
- `P0` が 1 件でも未完了なら `P1` 以下には着手しない。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモ（件数等）を追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。
- **emitter の parity テストは「emit 成功」ではなく「emit + compile + run + stdout 一致」を完了条件とする。** emit だけ成功してもプレースホルダーコードが混入している可能性がある。

## 未完了タスク

### P0-EXCEPTION-GO: Go backend の例外処理実装

文脈: [docs/ja/plans/p0-exception-go.md](../plans/p0-exception-go.md)
仕様: [docs/ja/spec/spec-exception.md](../spec/spec-exception.md)

1. [ ] [ID: P0-EXCEPTION-GO-S1] Go runtime に `PytraError` / `PytraValueError` / `PytraRuntimeError` クラス階層を実装する — struct embedding + `pytraErrorIsInstance(err, tidMin, tidMax)` 関数
2. [ ] [ID: P0-EXCEPTION-GO-S2] linker に `can_raise_v1` マーカーの推移的付与を実装する — call graph 走査で raise を含む関数を特定
3. [ ] [ID: P0-EXCEPTION-GO-S3] EAST3 言語別 lowering で `Raise` → `ErrorReturn`、`ErrorCheck`、`ErrorCatch` ノードを生成する
4. [ ] [ID: P0-EXCEPTION-GO-S4] Go emitter で `ErrorReturn` / `ErrorCheck` / `ErrorCatch` を写像する — `(T, *PytraError)` 戻り値、type_id range check isinstance、defer finally
5. [ ] [ID: P0-EXCEPTION-GO-S5] fixture 追加（raise/try/except/finally、ユーザー定義例外、複数 handler）+ Go parity 確認

### P0-EXCEPTION-CPP: C++ backend の例外処理実装（CommonRenderer 連携）

文脈: [docs/ja/plans/p0-exception-cpp.md](../plans/p0-exception-cpp.md)
仕様: [docs/ja/spec/spec-exception.md](../spec/spec-exception.md)

1. [ ] [ID: P0-EXCEPTION-CPP-S1] CommonRenderer に `emit_raise` / `emit_try` の共通骨格を実装する
2. [ ] [ID: P0-EXCEPTION-CPP-S2] C++ emitter で `Raise` → `throw ExceptionType("msg")` の写像を override する
3. [ ] [ID: P0-EXCEPTION-CPP-S3] C++ emitter で `Try` → `try { } catch (ExceptionType& e) { }` の写像を override する
4. [ ] [ID: P0-EXCEPTION-CPP-S4] C++ emitter で `finally` を RAII スコープガードに写像する
5. [ ] [ID: P0-EXCEPTION-CPP-S5] fixture 追加（raise/try/except/finally、ユーザー定義例外、複数 handler）+ C++ parity 確認

### P2-SELFHOST: toolchain2 自身の変換テスト

文脈: `docs/ja/plans/plan-pipeline-redesign.md` §3.5

1. [x] [ID: P2-SELFHOST-S1] `src/toolchain2/` の全 .py が parse 成功 — 37/46（9件は ParseContext再帰/Union forward ref/walrus等の parser未対応構文）
2. [x] [ID: P2-SELFHOST-S2] parse → resolve → compile → optimize まで通す — 37/37 全段通過
3. [x] [ID: P2-SELFHOST-S3] golden を `test/selfhost/` に配置し、回帰テストとして維持 — east1/east2/east3/east3-opt 各 37 件
4. [ ] [ID: P2-SELFHOST-S4] Go emitter で toolchain2 を Go に変換し、`go build` が通る — emit 25/25 成功、`go build` は docstring/構文問題で未達
5. [ ] [ID: P2-SELFHOST-S5] Go emitter の unsupported expr/stmt を fail-fast に変更し、プレースホルダ出力を禁止する — `nil /* unsupported */` / `// unsupported stmt` を廃止し、spec-emitter-guide.md の fail-closed 契約に合わせる
6. [ ] [ID: P2-SELFHOST-S6] Go emitter が `yields_dynamic` を正本として container getter/pop の型アサーションを判断するよう修正する — `resolved_type` / owner 文字列ベースの分岐をやめ、`Call.yields_dynamic` を使用
7. [ ] [ID: P2-SELFHOST-S7] Go emitter の container 既定表現を spec 準拠に修正する — list/dict/set を既定で参照型ラッパーにし、`meta.linked_program_v1.container_ownership_hints_v1.container_value_locals_v1` がある局所のみ値型縮退を許可する
8. [ ] [ID: P2-SELFHOST-S8] Go emitter の runtime call 名解決を mapping.json に一本化する — emitter が mapping.json を迂回して `list_ctor` / `list.append` / `dict.get` / `set_ctor` / `sorted` などを個別 lower している箇所を mapping.json 経由へ寄せ、backend 内の runtime call 意味論の二重管理を解消する

### P2-LOWERING-PROFILE: Lowering プロファイル + CommonRenderer 導入

文脈: [docs/ja/plans/p2-lowering-profile-common-renderer.md](../plans/p2-lowering-profile-common-renderer.md)
仕様: [docs/ja/spec/spec-language-profile.md](../spec/spec-language-profile.md) §7〜§8

1. [x] [ID: P2-LOWERING-PROFILE-S1] lowering プロファイルのスキーマを確定し、C++ / Go のプロファイル JSON を作成する — `src/toolchain2/emit/profiles/core.json`, `src/toolchain2/emit/profiles/cpp.json`, `src/toolchain2/emit/profiles/go.json` を正本とし、`toolchain2.emit.common.profile_loader` と focused unittest で schema validation / core merge / C++ / Go profile 読込を確認
2. [x] [ID: P2-LOWERING-PROFILE-S2] EAST3 lowering が lowering プロファイルを読み、`tuple_unpack_style` に従って tuple unpack を展開するようにする — `lower_east2_to_east3(..., target_language=...)` で profile を読み、`core=individual_temps`, `cpp=TupleUnpack`, `go=MultiAssign` へ分岐し、Go は `multi_return[...]` の関数署名/return/multi-assign を consume できるところまで接続する
3. [x] [ID: P2-LOWERING-PROFILE-S3] `container_covariance` / `with_style` / `property_style` を lowering に反映する — `container_covariance=false` では `list[T] -> list[U]` を `CovariantCopy` に lower し、`with_style=try_finally` では `With` を bind+`Try(finally close)` に lower、`property_style=field_access` では `property_getter` を field access へ正規化する。C++ / Go emitter には `CovariantCopy` 消費を追加
— S4〜S7（CommonRenderer 実装 + emitter 移行 + parity）は P3-COMMON-RENDERER に統合済み

### P3-COMMON-RENDERER: CommonRenderer 導入 + C++/Go emitter 移行 + fixture parity

文脈: [docs/ja/plans/p2-lowering-profile-common-renderer.md](../plans/p2-lowering-profile-common-renderer.md)
仕様: [docs/ja/spec/spec-language-profile.md](../spec/spec-language-profile.md) §8

1. [x] [ID: P3-COMMON-RENDERER-S1] CommonRenderer 基底クラスを実装する — If/While/BinOp/Call/Return/Assign/Constant/Compare/UnaryOp/BoolOp 等の共通ノード走査を、プロファイル JSON（type_map, operator_map, syntax, lowering）を参照して生成する共通基底。言語固有ノード（FunctionDef, ClassDef, ForCore 等）は abstract override として残す
2. [ ] [ID: P3-COMMON-RENDERER-S2] C++ emitter を CommonRenderer + override 構成に移行する — `src/toolchain2/emit/profiles/cpp.json` のプロファイルに従い、CommonRenderer の共通ノード走査を使う構成にする。C++ 固有のノード（ClassDef, FunctionDef, ForCore, With 等）だけ override として残す
3. [ ] [ID: P3-COMMON-RENDERER-S3] Go emitter を CommonRenderer + override 構成に移行する — `src/toolchain2/emit/profiles/go.json` のプロファイルに従い同様に移行する
4. [ ] [ID: P3-COMMON-RENDERER-S4] fixture 132 件 + sample 18 件の C++/Go compile + run parity を通す — CommonRenderer 移行後に **emit + compile + run + stdout 一致** を全件確認する

### P4-INT32: int のデフォルトサイズを int64 → int32 に変更

文脈: [docs/ja/plans/p4-int32-default.md](../plans/p4-int32-default.md)

前提: Go selfhost 完了後に着手。

1. [ ] [ID: P4-INT32-S1] spec-east.md / spec-east2.md の `int` → `int32` 正規化ルール変更
2. [ ] [ID: P4-INT32-S2] resolve の型正規化を修正
3. [ ] [ID: P4-INT32-S3] sample 18 件のオーバーフロー確認 + 必要な箇所を `int64` に明示
4. [ ] [ID: P4-INT32-S4] golden 再生成 + 全 emitter parity 確認

注: 完了済みタスクは [アーカイブ](archive/index.md) に移動済み。
