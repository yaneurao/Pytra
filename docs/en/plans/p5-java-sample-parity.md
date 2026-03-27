<a href="../../ja/plans/p5-java-sample-parity.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p5-java-sample-parity.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p5-java-sample-parity.md`

# P5: Java sample parity

最終更新: 2026-03-21

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P5-JAVA-PARITY-*`

## 背景

pytra-cli の compile → link → emit パイプライン統一後、Java backend の sample parity check を実施したところ 0/18 PASS。

`java_native_emitter.py` に `UnboundLocalError`（`_java_ref_type` / `_java_type` の `tn: str = tn`）があり修正済み。runtime コピー（`sample/java/*.java` 全体）を `java.py` に追加し、`pytra-cli.py` に `javac` + `java Main` の build/run を追加済み。

ただし `sample/java/` の runtime ファイル群に 228 件のコンパイルエラーが残っている。旧 single-file emit 用に作られた runtime と multi-module emit の衝突（クラス名重複、import 不整合等）が原因。

## 対象

- `src/toolchain/emit/java/emitter/java_native_emitter.py` — emitter バグ修正
- `src/toolchain/emit/java.py` — runtime 生成（C# 方式: native コピー + .east → .java 変換）
- `sample/java/*.java` — runtime 整合
- `src/pytra-cli.py` — Java build/run

## 非対象

- Java emitter の新規構文サポート追加（既存 sample で使われる範囲のみ）

## 受け入れ基準

- [ ] `runtime_parity_check.py --targets java` で sample/py の全 18 ケースが PASS する。

## 決定ログ

- 2026-03-21: parity check 実施、0/18 PASS で起票。`_java_type` の UnboundLocalError 2件を修正済み。runtime コンパイルエラー 228 件は未解決。
- 2026-03-21: VarDecl 対応、runtime を `src/runtime/java/built_in/PyRuntime.java`（正本）からコピーに変更、entry module を `Main.java` で出力、runtime コピーを必要ファイルのみに限定。0/18 PASS のまま。残り: emitter が `_impl.perf_counter()` のような不正な runtime 呼び出しを生成する問題が未解決。
