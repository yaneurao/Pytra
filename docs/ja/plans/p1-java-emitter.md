<a href="../../en/plans/p1-java-emitter.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1-JAVA-EMITTER: Java emitter を toolchain2 に新規実装する

最終更新: 2026-03-30
ステータス: 未着手

## 背景

Java は Android 開発やサーバーサイドで広く使われており、Pytra のターゲット言語としてユーザー需要が高い。旧 toolchain1 に Java emitter（`src/toolchain/emit/java/`）と runtime（`src/runtime/java/`）が存在するが、toolchain2 の新パイプラインに移行する必要がある。

Java が通れば Kotlin（JVM ベース）への展開も近くなる。

## 設計

### emitter 構成

- `src/toolchain2/emit/java/` に CommonRenderer + override 構成で実装
- 旧 `src/toolchain/emit/java/` と TS emitter（`src/toolchain2/emit/ts/`）を参考にする
- Java 固有のノード（class 必須構造、package、static method、checked exception、型消去等）だけ override

### mapping.json

`src/runtime/java/mapping.json` に以下を定義:
- `calls`: runtime_call の写像
- `types`: EAST3 型名 → Java 型名（`int64` → `long`, `float64` → `double`, `str` → `String`, `bool` → `boolean`, `Exception` → `Exception` 等）
- `env.target`: `"\"java\""`
- `builtin_prefix`: `"py_"`
- `implicit_promotions`: Java の暗黙昇格ペア（C++ とほぼ同じ）

### Java 固有の考慮事項

- Java はトップレベル関数がないため、全てのコードが class 内に配置される
- `main_guard_body` は `public static void main(String[] args)` に写像
- ジェネリクスはプリミティブ型を直接使えない（`List<int>` は不可、`List<Long>` が必要）
- checked exception の扱い（`throws` 宣言）

### parity check

- `pytra-cli2 -build --target java` の対応が必要（インフラ担当に依頼）
- `runtime_parity_check_fast.py --targets java` で検証
- fixture + sample + stdlib の3段階

## 決定ログ

- 2026-03-30: Java backend 担当を新設。emitter guide に従い toolchain2 emitter を実装する方針。Java が通れば Kotlin への展開が近くなる。
