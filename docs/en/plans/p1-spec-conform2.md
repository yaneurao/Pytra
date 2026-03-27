<a href="../../ja/plans/p1-spec-conform2.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p1-spec-conform2.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p1-spec-conform2.md`

# P1-SPEC-CONFORM2: 仕様整合（compile / link / optimize / emit）

最終更新: 2026-03-26
ステータス: 着手中

## 背景

Codex-review により、compile / link / optimize / emit が spec-linker.md / spec-emitter-guide.md の契約から逸脱している箇所が 13 件特定された。

根本原因は EAST（resolve/compile）が型情報を十分に提供していないため、後段（emit）が workaround としてハードコードや型推論を入れていること。修正は「正本を先に直し、workaround を後で剥がす」の順で行う。

## 修正順序

### フェーズ1: link（canonical source を正す）

| # | ファイル | 問題 | 修正内容 |
|---|---|---|---|
| S1 | `type_id.py` | `bases` ではなく `base` 単数を見ている。未定義基底を object にフォールバック | `bases[0]` を正本にする。未定義基底・循環継承を fail-fast にする（spec-linker §6.3） |
| S2 | `runtime_discovery.py` | .east 読込失敗を `except: pass` で握り潰す | 例外をエラーとして伝播する |
| S3 | `manifest_loader.py` | 不正 entry・欠損ファイル・不正 JSON を `continue` で黙殺 | エラーにする |
| S4 | `linker.py` | manifest `modules[*].input` が raw EAST3 パスではなく source_path | input に linked 前 module の入力パスを設定する |
| S5 | `normalize_runtime_calls.py` | 旧 emitter 互換のために BuiltinCall を de-lower / re-lower | 暫定互換レイヤを除去。toolchain2 emitter が canonical EAST3 を直接消費する |
| S6 | `expand_defaults.py` | bare name / attr 名だけでシンボル解決。同名メソッドが複数あると誤展開 | module_id::name ベースに限定。曖昧な Attribute call では補完しない |

### フェーズ2: emit（workaround を剥がす）

link 修正後に着手。EAST が正しい型情報を持つようになれば、emitter の workaround は不要になる。

| # | ファイル | 問題 | 修正内容 |
|---|---|---|---|
| S7 | `emit/go/emitter.py` | `_coerce_to_type()` で cast 追加。unknown 変数を後から具体型に昇格。for-range ループ変数の型変更。`math` / `pytra.` ハードコード | cast 追加を除去（spec §1.1 禁止事項）。型変更を除去。ハードコードを `mapping.json` に移行。EAST の型情報が不足する場合は resolve/compile を修正 |
| S8 | `emit/cpp/emitter.py` | unknown を int64 に潰す。decl_type なしの代入で target/value から型推論。`pytra.` prefix でモジュール判定 | 型推論を除去。unknown は `auto` でレンダリング。ハードコードを `mapping.json` に移行 |
| S9 | `emit/common/code_emitter.py` | — | mapping.json のみで分岐するように整理 |

### フェーズ3: optimize / compile（型責務を前段に戻す）

emit の workaround が消えた後、optimizer/compile が型を後付けしている箇所を resolve に寄せる。

| # | ファイル | 問題 | 修正内容 |
|---|---|---|---|
| S10 | `optimize/passes/typed_repeat_materialization.py` | resolved_type を後付け補完 | 型決定は resolve に寄せる。optimizer は metadata/hint 追加に限定 |
| S11 | `optimize/passes/typed_enumerate_normalization.py` | 同上 | 同上 |
| S12 | `compile/passes.py` | bytes/bytearray subscript を int32 に決め打ち。P4-INT32 未着手なのに int32 が混入 | 現仕様（int64）に合わせて戻す |
| S13 | — | golden 再生成 + parity 維持確認 | `regenerate_golden.py` で全段再生成。Go 18/18 parity 維持 |

## 受け入れ基準

1. emitter から型推論・cast 追加・型変更のコードが除去されている
2. emitter のモジュール判定が `mapping.json` + `runtime_call_adapter_kind` のみで行われている
3. linker の fail-open が全て fail-fast に変更されている
4. `normalize_runtime_calls.py` が除去されている
5. Go 18/18 + C++ emit 成功の parity が維持されている

## 参照仕様

- [spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1.1 禁止事項、§12.4 cast 出力判定
- [spec-linker.md](../spec/spec-linker.md) §6.3 type_id 契約
- [spec-runtime-mapping.md](../spec/spec-runtime-mapping.md) §7 implicit_promotions
