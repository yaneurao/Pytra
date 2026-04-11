<a href="../../en/todo/cpp.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — C++ backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-04-11

## 運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。
- **parity テストは「emit + compile + run + stdout 一致」を完了条件とする。**
- **[emitter 実装ガイドライン](../spec/spec-emitter-guide.md)を必ず読むこと。** parity check ツール、禁止事項、mapping.json の使い方が書いてある。

## selfhost 作業の運用ルール（C++ を先行させる方針）

1. **C++ を 1 言語先行させる**。他言語の selfhost は C++ で判断基準が固まってから着手する。
2. **backend 側で対処できる問題は自律的に修正してよい**。具体的には:
   - C++ emitter の generator ロジックの修正
   - C++ runtime（`src/runtime/cpp/`）の補完
   - C++ mapping.json の追加・修正
   - 既存の EAST3 metadata を見落としていた場合のハンドリング追加
3. **「EAST 側の修正が必要かも」と思ったら作業を停止して報告する**。該当するのは:
   - EAST3 に必要な情報がそもそも無い（metadata 欠落、kind 不足）
   - resolver / compiler / optimizer が情報を正しく付けていない
   - 修正が他言語（Rust, TS, Go, Java 等）にも影響する可能性がある
   - どちらで直すべきか判断に迷う
4. **判断は 1 件ずつ人間（PM）が行う**。バッチ報告ではなく、発生した時点で即停止・即報告・即判断。

### 問題報告フォーマット

```
## 問題: <短い要約>

**症状**: selfhost emit → build で何が失敗するか（エラーメッセージの原文）
**場所**:
  - source（selfhost 対象の Python）: src/toolchain/... : line
  - emit 結果の該当 C++: <抜粋>
  - 該当 EAST3 ノード: <kind, 主要 field の抜粋>
**backend 側で対処する案**: どう修正するか、副作用
**EAST 側で対処する案**: どう修正するか、他言語への影響
**担当の見立て**: どちらが妥当か（理由）
```

## 未完了タスク

### P20-CPP-SELFHOST: C++ emitter で toolchain を C++ に変換し g++ build を通す

文脈: [docs/ja/plans/p4-cpp-selfhost.md](../plans/p4-cpp-selfhost.md)

S0〜S4 完了済み（[archive/20260402.md](archive/20260402.md) 参照）。

1. [ ] [ID: P20-CPP-SELFHOST-S5] selfhost C++ バイナリを g++ でビルドし、リンクが通ることを確認する
   - build 失敗の都度、backend で直るか EAST 修正が必要か判断する
   - EAST 修正が必要と思われる場合は **作業を停止し、問題報告フォーマットで報告する**
2. [ ] [ID: P20-CPP-SELFHOST-S6] `run_selfhost_parity.py --selfhost-lang cpp --emit-target cpp --case-root fixture` で fixture parity が PASS することを確認する
3. [ ] [ID: P20-CPP-SELFHOST-S7] `run_selfhost_parity.py --selfhost-lang cpp --emit-target cpp --case-root sample` で sample parity が PASS することを確認する
