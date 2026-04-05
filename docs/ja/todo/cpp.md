<a href="../../en/todo/cpp.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — C++ backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-04-02

## 運用ルール

- **旧 toolchain1（`src/toolchain/emit/cpp/`）は変更不可。** 新規開発・修正は全て `src/toolchain2/emit/cpp/` で行う（[spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1）。
- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。
- **parity テストは「emit + compile + run + stdout 一致」を完了条件とする。**
- **[emitter 実装ガイドライン](../spec/spec-emitter-guide.md)を必ず読むこと。** parity check ツール、禁止事項、mapping.json の使い方が書いてある。

## 未完了タスク

### P0-CPP-MAPPING-CLEANUP: C++ mapping.json の死んだエントリを掃除する

`check_emitter_hardcode_lint.py --lang cpp` の `rt:call_cov` で 14 件の mapping.json エントリが EAST3 golden に出現しない。以下の 3 種類に分類して対処する。

**A. 旧キー名（完全修飾化漏れ or 死んだエントリ）— 削除 or FQCN 化:**
- `py_len` — EAST3 は `runtime_call: "len"` を使う。FQCN 化済みなら旧キーを削除
- `py_dumps` / `py_dumps_jv` / `py_loads` / `py_loads_arr` / `py_loads_obj` — JSON 系。FQCN キーが別途あるなら旧キーを削除
- `py_float_from_str` — `float()` コンストラクタ。FQCN キーがあるか確認して統合
- `py_floordiv` — `//` 演算子。EAST3 で `runtime_call` として使われているか確認
- `py_write_text` — pathlib 系。FQCN キーがあるか確認

**B. EAST3 が別経路で解決するエントリ — 削除:**
- `bytearray_ctor` / `bytes_ctor` — コンストラクタは EAST3 で `runtime_call` を経由しない
- `open` — ファイルオープンは `@extern` 経由
- `std::runtime_error` — C++ 固有のシンボル。EAST3 の `runtime_call` ではない

**C. fixture カバレッジ不足 — fixture 追加済み or 追加予定:**
- `str.index` — `str_find_index` fixture 追加済み（golden 再生成で解消見込み）

1. [ ] [ID: P0-CPP-MAPCLN-S1] 上記 A の旧キーを削除 or FQCN キーに統合する
2. [ ] [ID: P0-CPP-MAPCLN-S2] 上記 B の不要エントリを mapping.json から削除する
3. [ ] [ID: P0-CPP-MAPCLN-S3] `check_emitter_hardcode_lint.py --lang cpp --category rt:call_coverage` が 0 件になることを確認する

### P0-CPP-RUNTIME-SYMBOL: C++ emitter のメソッド名ハードコードを解消する

`emitter.py` と `header_gen.py` に `"append"`, `"clear"`, `"discard"` 等の Python メソッド名をリストで持っている箇所がある（lint `runtime_symbol` 違反 5 件）。container の mutable/immutable 判定に使用。

emitter が `runtime_call == "list.append"` のような文字列で判定するのも同じ違反。EAST3 の resolve/compile 段で `Call.meta.mutates_receiver: true` を付与し、emitter はそのフラグだけを見るべき。

前提: EAST3 に `mutates_receiver` メタデータを追加する（infra 担当の EAST 変更）

1. [ ] [ID: P0-CPP-RTSYM-S1] EAST3 の Call ノードに `meta.mutates_receiver` を追加する spec を定義する（infra 担当に依頼）
2. [ ] [ID: P0-CPP-RTSYM-S2] C++ emitter の mutable メソッド名リストを `meta.mutates_receiver` ベースの判定に置き換える
3. [ ] [ID: P0-CPP-RTSYM-S3] `check_emitter_hardcode_lint.py --lang cpp --category runtime_symbol` が 0 件になることを確認する

### P20-CPP-SELFHOST: C++ emitter で toolchain2 を C++ に変換し g++ build を通す

文脈: [docs/ja/plans/p4-cpp-selfhost.md](../plans/p4-cpp-selfhost.md)

S0〜S4 完了済み（[archive/20260402.md](archive/20260402.md) 参照）。

1. [ ] [ID: P20-CPP-SELFHOST-S5] selfhost C++ バイナリを g++ でビルドし、リンクが通ることを確認する
2. [ ] [ID: P20-CPP-SELFHOST-S6] `run_selfhost_parity.py --selfhost-lang cpp --emit-target cpp --case-root fixture` で fixture parity が PASS することを確認する
3. [ ] [ID: P20-CPP-SELFHOST-S7] `run_selfhost_parity.py --selfhost-lang cpp --emit-target cpp --case-root sample` で sample parity が PASS することを確認する
