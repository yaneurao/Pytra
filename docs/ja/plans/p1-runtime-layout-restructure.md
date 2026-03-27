<a href="../../en/plans/p1-runtime-layout-restructure.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1: runtime ディレクトリ構造変更（.east 統一 + 手書き分離）

最終更新: 2026-03-19

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-RUNTIME-LAYOUT-RESTRUCTURE-01`

## 背景

現状の `src/runtime/` は言語ごとに `generated/` と `native/` が混在している。
`generated/` には事前に C++ 等に変換した言語固有コードが配置されているが、
compile → link パイプライン（P2）では `.east`（EAST3 JSON）を link 時に一括変換する設計となる。

## 現状

```
src/runtime/cpp/generated/std/pathlib.h      ← 自動生成 C++
src/runtime/cpp/generated/std/pathlib.cpp
src/runtime/cpp/native/core/py_runtime.h     ← 手書き C++
src/runtime/rs/generated/std/collections.rs  ← 自動生成 Rust
...（言語ごとに重複）
```

## 新設計

```
src/runtime/east/std/pathlib.east       ← 言語非依存、自動生成
src/runtime/east/std/json.east
src/runtime/east/built_in/predicates.east
src/runtime/cpp/py_runtime.h                 ← 手書き C++ のみ
src/runtime/cpp/gc.h
src/runtime/cpp/list.h
```

## メリット

- `.east` は言語非依存で 1 箇所にまとまる（言語ごとの重複なし）
- `runtime/cpp/` には C++ 固有の手書きコードだけ配置
- link 時に `.east` + 手書きヘッダから各ターゲット言語のコードを生成
- 新しい言語バックエンドを追加しても `.east` は共有

## 対象

- `src/runtime/east/` — 新設（`.east` ファイル配置）
- `src/runtime/cpp/generated/` — 削除（`.east` に移行）
- `src/runtime/cpp/native/` — `src/runtime/cpp/` に直接配置に変更
- `src/runtime/{rs,cs,js,...}/generated/` — 削除（`.east` に移行）
- 各バックエンドの include パス・ヘッダ参照の修正

## 依存関係

- P2（compile / link パイプライン分離）の前提タスク

## 受け入れ基準

- `src/runtime/east/` に `.east` ファイルが配置されている。
- `src/runtime/cpp/` に手書き C++ ヘッダのみが配置されている。
- 言語ごとの `generated/` ディレクトリが不要になっている。
- fixture / sample pass。

## 決定ログ

- 2026-03-19: ユーザー提案。generated/ に事前変換した C++ を置くモデルが compile → link パイプラインと矛盾するため、.east を言語非依存で配置する設計に変更。P2 の前提タスクとして P1 で起票。
