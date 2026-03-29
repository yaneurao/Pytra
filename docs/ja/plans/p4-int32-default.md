<a href="../../en/plans/p4-int32-default.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P20-INT32: int のデフォルトサイズを int64 → int32 に変更

最終更新: 2026-03-29
ステータス: 未着手（P4 → P20 に降格。影響範囲が大きいため優先度を下げた）

## 背景

現在 Pytra は Python の `int` を EAST2 の型正規化で `int64` にマッピングしている。しかし、主要ターゲット言語（C++, Go, Java, C#, Kotlin）の `int` は 32bit であり、通常利用には 32bit で十分である。64bit はメモリ・キャッシュ効率が悪く、不必要なオーバーヘッドを生む。

`int` → `int32` に変更し、64bit が必要な場合はユーザーが `int64` と明示する運用とする。

## 設計判断

### `int` → `int32` の根拠

- C++/Go/Java/C#/Kotlin の `int` は 32bit（言語標準）
- `int32` の最大値は約 21 億（2,147,483,647）であり、通常のループカウンタ・配列インデックス・演算には十分
- Java/C# が int32 のまま長年運用されており、実用上問題がないことが実証済み
- 64bit 整数はメモリ帯域・キャッシュライン占有で不利（特にコンテナ要素として大量に保持する場合）

### `len()` の戻り値型: `int32`

- 大半のターゲット言語で `len`/`size`/`count` は signed int32 を返す（Java, C#, Kotlin）
- C++ の `size_t`（uint64）は設計上の失敗と広く認識されており（C++20 で `std::ssize()` が追加された経緯）、追従しない
- unsigned にすると `len(x) - 1` の underflow、signed との混合演算 cast ノイズなど実害が大きい
- 単一配列で 21 億要素を超えるケースは通常想定外

### 64bit が必要な場合

ユーザーが `int64` と明示する。これは他言語（Java の `long`、C# の `long`、Go の `int64`）と同じ運用モデルである。

## 影響範囲

### 仕様

- `spec-east.md` §6.2: `int` の正規化先を `int64` → `int32` に変更
- `spec-east2.md` §2.2: 同上
- `spec-east1.md`: 影響なし（EAST1 は型正規化しない）

### 実装

- `src/toolchain/compile/east2.py`（または resolve 関連）: 型正規化ルールの変更
- `Constant` の整数リテラル型: `int64` → `int32`
- `len()` の戻り値型: `int64` → `int32`
- `range()` の引数・ループ変数型への波及
- cast 挿入ルール: `int32` ↔ `int64` 間の昇格ルール追加が必要か検討

### テスト・検証

- golden ファイル全再生成（fixture + sample + selfhost）
- 全 emitter の型マッピング修正（mapping.json 等）
- sample 18 件のオーバーフロー確認: 中間計算が 32bit を超えないか精査し、必要な箇所は `int64` に明示修正
- parity テスト全言語通過

## リスク

- sample の一部（マンデルブロ集合等）で中間計算が int32 を超える可能性がある → S3 で精査
- `int32 * int32` の結果が int32 に収まらない場合の昇格ルールの設計が必要
- 既存ユーザーコード（`materials/` 配下等）への影響確認

## 前提条件

Go selfhost（P2-SELFHOST）完了後に着手する。

## サブタスク

1. [ID: P20-INT32-S1] spec-east.md / spec-east2.md の `int` → `int32` 正規化ルール変更
2. [ID: P20-INT32-S2] resolve の型正規化を修正
3. [ID: P20-INT32-S3] sample 18 件のオーバーフロー確認 + 必要な箇所を `int64` に明示
4. [ID: P20-INT32-S4] golden 再生成 + 全 emitter parity 確認

## 受け入れ基準

1. `int` が `int32` に正規化されること（spec + 実装一致）
2. `len()` の戻り値型が `int32` であること
3. fixture 全件 + sample 18 件で全言語 parity 通過（emit + compile + run + stdout 一致）
4. sample でオーバーフローが発生しないこと（必要箇所は `int64` 明示済み）
5. selfhost の golden が再生成済みであること

## 決定ログ

- 2026-03-26: `len()` の戻り値型について議論。C++ の `size_t`（uint64）に倣うのではなく `int32`（signed）を採用する方針を確認。理由: unsigned は算術 underflow の罠があり、大半のターゲット言語（Java/C#/Kotlin/Go/Swift）が signed を採用している。
