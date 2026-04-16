<a href="../../en/todo/julia.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — Julia backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-04-16

## 運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。
- **parity テストは「emit + compile + run + stdout 一致」を完了条件とする。**
- **[emitter 実装ガイドライン](../spec/spec-emitter-guide.md)を必ず読むこと。** parity check ツール、禁止事項、mapping.json の使い方が書いてある。

## 参考資料

- Julia emitter: `src/toolchain/emit/julia/`
- TS emitter（参考実装）: `src/toolchain/emit/ts/`
- Julia runtime: `src/runtime/julia/`
- emitter 実装ガイドライン: `docs/ja/spec/spec-emitter-guide.md`
- mapping.json 仕様: `docs/ja/spec/spec-runtime-mapping.md`

## 未完了タスク

### P1-EMITTER-SELFHOST-JULIA: emit/julia/cli.py を単独で selfhost C++ build に通す

文脈: [docs/ja/plans/p1-emitter-selfhost-per-backend.md](../plans/p1-emitter-selfhost-per-backend.md)

各 backend emitter は subprocess で独立起動する自己完結プログラム。pytra-cli.py 全体の selfhost とは切り離し、`toolchain.emit.julia.cli` をエントリに単独で C++ build を通す。

1. [x] [ID: P1-EMITTER-SELFHOST-JULIA-S1] `python3 src/pytra-cli.py -build src/toolchain/emit/julia/cli.py --target cpp -o work/selfhost/emit/julia/` を実行し、変換が通るようにする
   - 2026-04-16: 完了。13 module を parse→resolve→compile→optimize→link→emit まで通し、42 本の C++ を `work/selfhost/emit/julia/` に生成。
   - 付随: linker の `_attach_method_signature_hints` / `_attach_function_signature_hints` で相互参照メソッドの deep-copy が指数的に肥大する問題を発見。snapshot 化して修正。`julia/subset.py` 単体で 5.2GB になっていた linked east3 が 13MB に落ち着いた（全 backend 共通）。
   - 付随: `toolchain/link/linker.py` に `from pytra.typing import cast` を再導入（他 instance の diff で消えていた）。
   - 付随: selfhost source 側の調整: `julia/subset.py` の starred expr と `collections.abc` を除去、`common/cli_runner.py` で Callable alias を PEP 695 形式に移行し、empty-dict 代入を JsonVal で通る形に書き直し。
2. [ ] [ID: P1-EMITTER-SELFHOST-JULIA-S2] 生成された C++ を `g++ -std=c++20 -O0` でコンパイルを通す（source 側の型注釈不整合を修正）
   - 2026-04-16: 進行中。着手済の修正:
     - `cpp/types.py` に uppercase `Callable[[...], R]` ハンドラを追加（`callable[...]` と同じ `std::function` に畳む）。
     - `resolve/py/resolver.py` の callable 署名推論で `| None` を保持するように修正（`_refine_callable_params_from_calls` と定義パラメータ推論の両経路）。
   - 残 blocker (cli_runner.cpp まわり):
     - `Optional[list[str]]` パラメータの呼び出しで `(*(*argv))` と二重 deref されて参照型にマッチしない。
     - 同じ関数内で tuple destructuring 結果の `str file_ext` / `str output_dir_text` が再宣言として出力される。
     - `std::function` 戻り値に `.unbox<int64>()` を付けて生成されてしまう（emit_fn/direct_emit_fn 呼び出し側）。
     - これらは cpp emitter 側の修正が必要で、source 側の型注釈調整だけでは回避できないため一旦停止。
3. [ ] [ID: P1-EMITTER-SELFHOST-JULIA-S3] コンパイル済み emitter で既存 fixture の manifest を処理し、Python 版 emitter と parity 一致を確認する
