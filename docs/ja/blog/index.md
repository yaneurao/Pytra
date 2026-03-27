<a href="../../en/blog/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# Pytra 開発ブログ

Pytra の設計判断や開発の裏話を書いていきます。

---

## 2026-03-26 | なぜパイプラインを 6 段に分けたのか

Python → C++ の変換器を作っていたら、いつの間にか 17 言語に対応していた。でも内部は 1 パスで全部やる巨大なモノリスだった。型解決も構文正規化も emit も全部 1 つのファイルに混在していて、新しい言語を追加するたびに同じバグを踏む。

そこで parse / resolve / compile / optimize / link / emit の 6 段に分離した。各段の入出力は JSON で、golden file テストで段ごとに検証できる。おかげで「どの段でバグが入ったか」が一目で分かるようになった。

[→ 詳しくはアーキテクチャガイド](../tutorial/architecture.md)

---

## 2026-03-25 | signature_registry を殺した話

以前は `math.sqrt` の戻り値型が `float64` であることを、Python コード内のハードコードテーブルで管理していた。stdlib が増えるたびにテーブルに手動で追加する。当然、追加を忘れると `unknown` 型になって emitter が壊れる。

「`math.py` の関数宣言を読めば戻り値型は分かるじゃないか」と気づいて、built-in / stdlib の型情報を `.py` ファイルの宣言から自動取得する仕組みに作り替えた。`@extern_fn(module=..., symbol=..., tag=...)` で runtime 情報まで宣言に載せたので、ハードコードテーブルは完全に不要になった。

---

## 2026-03-24 | selfhost を見据えた設計制約

Pytra のトランスパイラ自身を Pytra で変換したい（selfhost）。そのためには、トランスパイラのコードが Pytra の変換可能なサブセットで書かれている必要がある。

`Any` 禁止、`object` 禁止、Python 標準モジュール禁止（`pytra.std.*` のみ）、グローバル可変状態禁止、動的 import 禁止。厳しい制約だが、これを守ることで C++ にも Go にも Rust にも変換できるコードになる。

実際に `toolchain2/` の 37/46 ファイルが parse → resolve → compile → optimize まで通った。残り 9 ファイルは parser が未対応の構文（walrus operator 等）があるだけで、対応すれば全件通る見込み。
