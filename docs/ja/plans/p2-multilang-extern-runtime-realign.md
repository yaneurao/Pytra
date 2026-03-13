# P2: 全言語 `@extern` runtime/emitter 契約の再整列

最終更新: 2026-03-13

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P2-MULTILANG-EXTERN-RUNTIME-REALIGN-01`

背景:
- `src/pytra/std/math.py`、`src/pytra/std/time.py`、`src/pytra/std/os.py`、`src/pytra/std/os_path.py`、`src/pytra/std/sys.py`、`src/pytra/std/glob.py`、`src/pytra/built_in/io_ops.py`、`src/pytra/built_in/scalar_ops.py` などは `@extern` / `extern(...)` を使って runtime 外部境界を宣言している。
- 2026-03-13 時点の非 C++ lane では、この宣言が generated runtime postprocess や backend emitter の special case によって host API 直結へ畳み込まれている。
- 代表例として `src/runtime/cs/generated/std/math.cs` は `System.Math` 実装と source に存在しない `tau` を持ち、`tools/gen_runtime_from_manifest.py` と各 backend emitter に `pytra.std.math` 固有知識が分散している。
- この状態では `src/pytra/**` が SoT にならず、`@extern` が「外部境界宣言」ではなく「backend が勝手に host API 実装へ潰してよい印」として誤用されている。
- C++ は header/source 分離で `extern` 宣言と native 実装の分離が比較的守られており、非 C++ も同じ原理へ戻す必要がある。

目的:
- `@extern` を全言語で共通の「外部境界宣言」として扱い直し、generated lane から host 固有意味論を追い出す。
- host API への接続は `src/runtime/<lang>/native/**` の ownership に集約し、backend emitter は generic extern metadata だけを見る構造へ戻す。
- `src/pytra/**` の API surface を正本に戻し、source にない symbol 追加や module-specific rewrite を止める。

対象:
- `src/pytra/std/*` / `src/pytra/built_in/*` にある runtime SoT の `@extern` / `extern(...)`
- `tools/runtime_generation_manifest.json` と `tools/gen_runtime_from_manifest.py`
- 各 backend emitter にある `pytra.std.math` など module-specific extern special case
- runtime symbol index / layout contract / representative smoke / docs の extern ownership 記述
- 全 target language の generated/native runtime artifact 更新

非対象:
- user program 側の ambient global `extern()`（`document`, `window.document` など）の意味論拡張
- `@extern` 以外の runtime helper 全般の redesign
- host runtime API の機能追加

受け入れ基準:
- generated runtime artifact が `@extern` symbol の host 固有実装を直書きしない。
- `System.Math` / `Math.*` / `pyMath*` など host binding は `src/runtime/<lang>/native/**` の canonical owner に閉じる。
- backend emitter から `pytra.std.math` のような module-specific extern hardcode が撤去され、generic extern/runtime metadata 経由へ揃う。
- `src/pytra/**` に存在しない symbol（例: `tau`）を generated artifact が勝手に追加しない。
- C++ reference lane を壊さず、非 C++ 全 target の representative runtime/emitter regression が current contract に更新される。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `rg -n "std_math_live_wrapper|pytra\\.std\\.math|System\\.Math|Math\\.PI|Math\\.Sqrt|tau" src tools test docs -g '!**/archive/**'`
- `python3 tools/gen_runtime_from_manifest.py --items std/math,std/time,std/os,std/os_path,std/sys,std/glob,built_in/io_ops,built_in/scalar_ops --targets rs,cs,js,ts,go,java,swift,kotlin,ruby,lua,scala,php,nim`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_gen_runtime_from_manifest.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2*_smoke.py'`
- `git diff --check`

## 分解

- [ ] [ID: P2-MULTILANG-EXTERN-RUNTIME-REALIGN-01-S1-01] runtime SoT 上の `@extern` module と、generated rewrite / emitter hardcode / native owner の current inventory を全 target で棚卸しする。
- [ ] [ID: P2-MULTILANG-EXTERN-RUNTIME-REALIGN-01-S1-02] `@extern` を「宣言のみ」「native owner 実装」「ambient extern は別系統」に分けた cross-target contract を spec / plan に固定する。
- [ ] [ID: P2-MULTILANG-EXTERN-RUNTIME-REALIGN-01-S2-01] `tools/runtime_generation_manifest.json` と `tools/gen_runtime_from_manifest.py` から module-specific extern rewrite を除去し、generated lane を declaration/wrapper-only に揃える。
- [ ] [ID: P2-MULTILANG-EXTERN-RUNTIME-REALIGN-01-S2-02] 各 target の `src/runtime/<lang>/native/**` に extern-backed canonical owner を整備し、runtime symbol index / layout contract を同期する。
- [ ] [ID: P2-MULTILANG-EXTERN-RUNTIME-REALIGN-01-S2-03] 各 backend emitter の `pytra.std.math` など module-specific extern hardcode を撤去し、generic extern/runtime metadata 経由へ移す。
- [ ] [ID: P2-MULTILANG-EXTERN-RUNTIME-REALIGN-01-S3-01] representative runtime artifact / smoke / docs / contract inventory を current extern ownership contract に同期して task を閉じる。

決定ログ:
- 2026-03-13: ユーザー指摘により、`@extern` を backend shortcut として扱っていた現行非 C++ 設計を誤りと認め、全 target を対象に SoT/native-owner/generic-emitter へ戻す P2 task として起票した。
