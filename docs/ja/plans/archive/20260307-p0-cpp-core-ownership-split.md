<a href="../../../en/plans/archive/20260307-p0-cpp-core-ownership-split.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: C++ core runtime ownership 分離（`generated/core` + `native/core` + `core` 互換面）

最終更新: 2026-03-07

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-CORE-OWNERSHIP-SPLIT-01`
- 参照仕様: `docs/ja/spec/spec-runtime.md`
- 参照仕様: `docs/ja/spec/spec-abi.md`
- 先行整理: `docs/ja/plans/archive/20260307-p0-cpp-runtime-layout-generated-native.md`

背景:
- `P0-CPP-RUNTIME-LAYOUT-REALIGN-01` で `std/built_in/utils` の module runtime は `generated/` + `native/` + `pytra/` shim へ再編できたが、`src/runtime/cpp/core/` は依然として「手書き core 一式」を 1 ディレクトリへ抱えたままである。
- 現状の `core/` は、`py_runtime.ext.h` / `py_types.ext.h` / `list.ext.h` / `dict.ext.h` / `gc.ext.cpp` など、低レベル runtime 基盤としては妥当だが、将来 pure Python SoT から変換できる core helper を追加した瞬間に generated と handwritten が同じ `core/` 配下へ混在する。
- その状態は、直前に `std/built_in/utils` で解消した「同一責務ディレクトリ内で ownership が見えない」問題を `core/` で再発させる。
- したがって、core についても `generated/core` と `native/core` を導入し、generated/handwritten の物理分離を先に済ませておく必要がある。

目的:
- C++ low-level runtime (`core`) について、generated と handwritten の ownership をディレクトリで分離する。
- 既存の stable include 面である `runtime/cpp/core/...` は当面維持し、backend / generated runtime / tests への影響を段階的に閉じ込める。
- 将来 pure Python SoT から変換できる core helper が増えても、`core/` に generated/handwritten が混在しない構造を先に作る。

対象:
- `src/runtime/cpp/core/`
- 新設する `src/runtime/cpp/generated/core/`
- 新設する `src/runtime/cpp/native/core/`
- C++ runtime include / build graph / symbol index 導線
  - `src/backends/cpp/cli.py`
  - `src/backends/cpp/emitter/header_builder.py`
  - `tools/gen/gen_runtime_symbol_index.py`
  - `tools/cpp_runtime_deps.py`
  - `tools/check/check_runtime_cpp_layout.py`
  - `tools/check/check_runtime_core_gen_markers.py`
- C++ runtime 関連 test / docs

非対象:
- `std/built_in/utils` module runtime の再設計
- `pytra/core/` という新しい public root の導入
- C++ core 全体の pure Python SoT 化
- `sample/cpp/*.cpp` の手編集
- list ref-first TODO の semantic change を同時に載せること

受け入れ基準:
- `src/runtime/cpp/generated/core/` が「SoT 由来 core artifact の唯一の置き場」として定義される。
- `src/runtime/cpp/native/core/` が「C++ 固有 / handwritten core artifact の唯一の置き場」として定義される。
- `src/runtime/cpp/core/` は stable include 面と互換 forwarder のみに縮退し、generated と handwritten の実装正本を混在させない。
- C++ backend / generated runtime / tests は引き続き `runtime/cpp/core/...` を include できるが、build graph / symbol index は `generated/core` / `native/core` の compile source を解決できる。
- guard が `generated/core` への marker 必須、`native/core` への marker 禁止、`core/` への実装再侵入禁止を監査できる。

確認コマンド（予定）:
- `python3 tools/check/check_todo_priority.py`
- `python3 tools/check/check_runtime_cpp_layout.py`
- `python3 tools/check/check_runtime_core_gen_markers.py`
- `python3 tools/gen/gen_runtime_symbol_index.py --check`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_runtime_symbol_index.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_cpp_runtime_build_graph.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_cpp_runtime_symbol_index_integration.py'`

## 先に固定する設計判断

### A. 目標レイアウト

```text
src/runtime/cpp/
  core/              # stable include surface / compatibility forwarder
  generated/
    core/
    built_in/
    std/
    utils/
  native/
    core/
    built_in/
    std/
    utils/
  pytra/
    built_in/
    std/
    utils/
```

### B. 各ディレクトリの意味

- `core/`
  - 低レベル runtime の stable include surface。
  - 既存 include (`runtime/cpp/core/*.ext.h`) との互換窓口。
  - 実装正本を置く場所ではない。
- `generated/core/`
  - pure Python SoT から変換された low-level core artifact。
  - 生成痕跡 (`AUTO-GENERATED FILE. DO NOT EDIT.` / `source:` / `generated-by:`) を必須にする。
- `native/core/`
  - C++ 固有の low-level runtime 実装。
  - GC / I/O / object layout / ABI glue / template helper など、SoT だけでは表現しにくい部分を置く。

### C. この計画でやらないこと

- `pytra/core/` を新設して public root を二重化しない。
- `core/` の include 名を一気に `pytra/core/...` へ変えない。
- `core/` の pure Python SoT を想像で大量新設しない。
- `std/built_in/utils` の既存 layout を巻き戻さない。

## 実装で迷いやすい点

### 1. `core/` は「handwritten 実装フォルダ」ではなく「互換 include 面」に縮退させる

この計画の本質は、`core/` を消すことではなく、`core/` に ownership が混在しないよう役割を変えることにある。

残してよい:
- forwarder header
- 互換 include 名
- レイアウト説明文書

置いてはいけない:
- generated 実装正本
- handwritten 実装正本
- `.cpp` 本体

### 2. `generated/core` は「今すぐ大量に埋める場所」ではない

- まずは empty lane でもよい。
- 重要なのは「将来 SoT から変換する core helper をどこへ置くか」を先に決めること。
- 初回フェーズでは、最低でも 1 つの representative path か fixture-level smoke で導線を実証する。

### 3. `native/core` は「何でも手書きしてよい巨大フォルダ」ではない

置いてよい:
- `gc`, `io` の `.cpp`
- object / container 表現ヘッダ
- `py_runtime` の low-level 集約
- template / inline helper

置いてはいけない:
- SoT と等価な高レベル runtime 本体
- `std` / `built_in` / `utils` module runtime の再流入
- temporary compatibility wrapper だけの duplicate 本体

### 4. include 面は当面 `core/...` を保つ

- `module_name_to_cpp_include("pytra.core.dict") -> "core/dict.ext.h"` のような既存契約は、最初の P0 では崩さない。
- build graph / symbol index が `core/...` から `generated/core` / `native/core` を引けるようにする。
- include root の改名は別計画に切り出す。

## フェーズ

### Phase 1: 現状棚卸しと責務固定

- `src/runtime/cpp/core/` の既存ファイルを棚卸しし、
  - stable include surface 候補
  - native/core 正本
  - 将来 generated/core 候補
  - docs / 非対象
  に分類する。
- `core/` を「互換 include 面」、`generated/core` を「生成正本」、`native/core` を「手書き正本」として plan/spec に固定する。
- `pytra/core` を導入しない理由も決定ログへ残す。

### Phase 2: path / index / guard 契約の設計

- `runtime_symbol_index` が core module に対して
  - public header: `src/runtime/cpp/core/...`
  - compile source: `src/runtime/cpp/generated/core/...` / `src/runtime/cpp/native/core/...`
  を持てるようにする。
- `cpp_runtime_deps.py` が `core/...` forwarder から `generated/core` / `native/core` の source を導出できるようにする。
- `check_runtime_cpp_layout.py` と `check_runtime_core_gen_markers.py` の責務を整理し、
  - `core/` 実装再侵入禁止
  - `generated/core` marker 必須
  - `native/core` marker 禁止
  を明文化する。

### Phase 3: handwritten core の物理移動

- 現行 `core/` の handwritten 正本を `native/core/` へ移す。
- `gc.ext.cpp` / `io.ext.cpp` のような compile source は `native/core/` へ移す。
- `dict.ext.h` / `list.ext.h` / `py_types.ext.h` / `py_runtime.ext.h` などの include 正本も `native/core/` へ移し、`core/` には forwarder を残すか、必要最小限の互換 façade へ縮退させる。
- このフェーズでは include 名互換を優先し、basename suffix の cleanup は後段に回してよい。

### Phase 4: generated/core lane の実証

- `generated/core/` を repo 上の正式レイアウトとして追加する。
- 代表ケースを 1 つ決める。
  - 実ファイル migration が安全なら 1 件移す。
  - まだ安全な real candidate がなければ fixture / synthetic test で `generated/core` の導線だけを証明する。
- 「generated/core が空でも設計は成立するが、導線未検証で終わらない」ことを重視する。

### Phase 5: docs / tests / closeout

- spec と README を `core handwritten-only` から `core compatibility surface + generated/native ownership split` へ更新する。
- `test_runtime_symbol_index.py` / `test_cpp_runtime_build_graph.py` / `test_cpp_runtime_symbol_index_integration.py` で representative contract を固定する。
- TODO / archive / 決定ログを更新し、`core` でも ownership 混在を許さない方針を完了扱いで閉じる。

## Phase 5 実施結果

- spec は Phase 1〜4 で更新済みの `spec-runtime.md` / `spec-abi.md` を正本とし、`core handwritten-only` ではなく `core compatibility surface + generated/native ownership split` が現行契約であることを再確認した。
- README 側は `src/runtime/cpp/core/README.md` / `src/runtime/cpp/native/README.md` / `src/runtime/cpp/generated/core/README.md` に加え、`src/runtime/cpp/std/README.md` の配置境界も更新し、`core` が stable include surface、`generated/core` と `native/core` が ownership lane であることを repo 全体で揃えた。
- representative tests には real repo contract を見る assertion を追加し、`test_runtime_symbol_index.py` で `core` public header + `generated/core` lane + `native/core` ownership が同時に存在することを固定した。既存の `test_cpp_runtime_symbol_index_integration.py` と `check_runtime_cpp_layout.py` も引き続き green であることを確認した。
- active TODO から本 P0 セクションを外し、plan を `docs/ja/plans/archive/20260307-p0-cpp-core-ownership-split.md` へ移した。`docs/ja/todo/archive/20260307.md` と `docs/ja/todo/archive/index.md` も同期し、core ownership split を完了扱いで閉じた。

## Phase 1 実施結果

2026-03-07 時点の `src/runtime/cpp/core/` 棚卸し結果は次のとおり。

- `compat surface` 候補: 10 files
  - `dict.ext.h`
  - `exceptions.ext.h`
  - `gc.ext.h`
  - `io.ext.h`
  - `list.ext.h`
  - `py_runtime.ext.h`
  - `py_scalar_types.ext.h`
  - `py_types.ext.h`
  - `set.ext.h`
  - `str.ext.h`
- `native/core` compile source 正本: 2 files
  - `gc.ext.cpp`
  - `io.ext.cpp`
- `generated/core` 既存候補: 0 files
  - 現行 `core/` 直下にあるコードは、いずれも object/container 表現・RC/GC・I/O・template helper・ABI glue に結びついており、既存 checked-in artifact のまま `generated/core` へ移せるものはない。
  - `generated/core` lane の実証は `S4-01` で synthetic fixture か将来の real candidate を使って行う。
- `非対象 / docs`: 1 file
  - `README.md`

分類判断:

- `gc.ext.cpp` / `io.ext.cpp` は include surface を持たない native compile source とみなし、将来は `native/core/*.ext.cpp` へ移す。
- `gc.ext.h` / `io.ext.h` は compile source の対応 header であり、将来は `native/core/*.ext.h` を正本にしつつ `core/*.ext.h` には forwarder を残す。
- `dict.ext.h` / `list.ext.h` / `set.ext.h` / `str.ext.h` / `py_scalar_types.ext.h` / `py_types.ext.h` / `exceptions.ext.h` / `py_runtime.ext.h` は、現在は object 表現・container 実装・低レベル helper・例外/I/O集約を含む handwritten core 正本であり、将来は `native/core/*.ext.h` へ移す。
- `py_runtime.ext.h` は generated runtime や native companion から広く参照される集約 header なので、`core/` 互換面を消さず、最終的には `core/py_runtime.ext.h -> native/core/py_runtime.ext.h` forwarder へ縮退させる。
- 現時点では、`core/` 内のどの既存ファイルも「generated/core へそのまま rename してよい既存 artifact」には分類しない。

移行マップ:

| 現在のファイル | 現在の分類 | 将来の `core/` | 将来の正本 | 備考 |
| --- | --- | --- | --- | --- |
| `src/runtime/cpp/core/README.md` | 非対象 / docs | 残置 | なし | レイアウト説明のみ。 |
| `src/runtime/cpp/core/gc.ext.cpp` | native compile source | 削除 | `src/runtime/cpp/native/core/gc.ext.cpp` | `.cpp` は互換 surface に残さない。 |
| `src/runtime/cpp/core/io.ext.cpp` | native compile source | 削除 | `src/runtime/cpp/native/core/io.ext.cpp` | 同上。 |
| `src/runtime/cpp/core/gc.ext.h` | compat + native header | forwarder | `src/runtime/cpp/native/core/gc.ext.h` | build graph は native source を引く。 |
| `src/runtime/cpp/core/io.ext.h` | compat + native header | forwarder | `src/runtime/cpp/native/core/io.ext.h` | `PyFile` 実体の include 窓口。 |
| `src/runtime/cpp/core/dict.ext.h` | compat + native header | forwarder | `src/runtime/cpp/native/core/dict.ext.h` | `pytra.core.dict` の public include は当面維持。 |
| `src/runtime/cpp/core/list.ext.h` | compat + native header | forwarder | `src/runtime/cpp/native/core/list.ext.h` | list object 表現本体。 |
| `src/runtime/cpp/core/set.ext.h` | compat + native header | forwarder | `src/runtime/cpp/native/core/set.ext.h` | set object 表現本体。 |
| `src/runtime/cpp/core/str.ext.h` | compat + native header | forwarder | `src/runtime/cpp/native/core/str.ext.h` | `str` value type / helper 本体。 |
| `src/runtime/cpp/core/py_scalar_types.ext.h` | compat + native header | forwarder | `src/runtime/cpp/native/core/py_scalar_types.ext.h` | scalar alias / primitive helper。 |
| `src/runtime/cpp/core/py_types.ext.h` | compat + native header | forwarder | `src/runtime/cpp/native/core/py_types.ext.h` | object/list/dict/set/rc alias 集約。 |
| `src/runtime/cpp/core/exceptions.ext.h` | compat + native header | forwarder | `src/runtime/cpp/native/core/exceptions.ext.h` | low-level exception helper。 |
| `src/runtime/cpp/core/py_runtime.ext.h` | compat + native header | forwarder | `src/runtime/cpp/native/core/py_runtime.ext.h` | generated/native runtime から最広範に参照される集約 header。 |

Phase 1 契約固定:

- `docs/ja/spec/spec-runtime.md` に、承認済み次段 layout として `core` compatibility surface + `generated/core` + `native/core` を追記した。
- `docs/ja/spec/spec-abi.md` に、low-level core は `pytra/core` を増やさず `core/...` include root を維持したまま ownership を分離する方針を追記した。
- `src/runtime/cpp/core/README.md` も「handwritten 実装専用」から「stable include surface。ownership split 後は forwarder へ縮退予定」という説明へ更新した。

## Phase 2 実施結果

- `tools/gen/gen_runtime_symbol_index.py` に C++ core 専用 artifact 解決 helper を追加し、`core/*.ext.h` public header を維持したまま、compile source は `generated/core` / `native/core` / 現行 `core/*.ext.cpp` の順で探索できるよう更新した。
- `tools/cpp_runtime_deps.py` は `runtime/cpp/core/*.ext.h` から future `generated/core/*.ext.cpp` / `native/core/*.ext.cpp` を候補導出できるよう更新し、現行 `core/*.ext.cpp` は fallback に残した。
- representative unit には synthetic runtime tree を使う future-proof test を追加し、
  - runtime symbol index 側で `core/dict.ext.h -> generated/core/dict.ext.cpp + native/core/dict.ext.cpp`
  - build graph 側で `runtime_cpp_candidates_from_header(core/dict.ext.h)` が future core split 候補を返す
  ことを確認した。
- `tools/check/check_runtime_cpp_layout.py` は `generated/{built_in,std,utils}` / `native/{built_in,std,utils}` / `pytra/{built_in,std,utils}` と `generated/core` / `native/core` / `core` surface を別 bucket として扱うよう更新し、`core/` には既知 baseline (`gc/io`) 以外の `.cpp` が再侵入した時点で fail する guard にした。あわせて `pytra/core` のような unsupported bucket も fail-fast する。
- `tools/check/check_runtime_core_gen_markers.py` は全言語の `pytra-gen` / `pytra-core` 監査を維持したまま、C++ `generated/core` の `source/generated-by` marker 必須、`native/core` と `core` surface の marker 禁止を追加した。
- synthetic unit として `test_check_runtime_cpp_layout.py` を新設し、移行期の `core` baseline + future `generated/native/core` lane が通ること、`core/*.cpp` 再侵入と `pytra/core` 再導入が fail することを固定した。`test_check_runtime_core_gen_markers.py` にも C++ core split reason の回帰を追加した。

## Phase 3 実施結果

- handwritten core compile source の第一弾として `src/runtime/cpp/core/gc.ext.cpp` と `src/runtime/cpp/core/io.ext.cpp` を `src/runtime/cpp/native/core/` へ移した。header include 面は `core/gc.ext.h` / `core/io.ext.h` のまま維持し、`.cpp` 実体だけを `core/` から追い出した。
- compile source を直書きしていた representative smoke (`test_cpp_runtime_boxing.py`, `test_cpp_runtime_iterable.py`, `test_cpp_runtime_type_id.py`, `test_py2cpp_list_pyobj_model.py`, `tools/check/verify_image_runtime_parity.py`) は `native/core/*.ext.cpp` 参照へ同期した。
- `tools/check/check_runtime_cpp_layout.py` は `core/` に `.cpp` が 1 本でも残っていたら fail する形へ締め、`test_runtime_symbol_index.py` / `test_cpp_runtime_build_graph.py` には実 repo の `core/gc.ext.h -> native/core/gc.ext.cpp` 契約を固定した。
- `tools/runtime_symbol_index.json` を再生成し、`pytra.core.gc` / `pytra.core.io` の compile source が `native/core/*.ext.cpp` を指す状態へ同期した。
- handwritten core header の正本も `src/runtime/cpp/native/core/` へ移し、`src/runtime/cpp/core/*.ext.h` は `runtime/cpp/native/core/*.ext.h` を読む薄い forwarder に差し替えた。`py_runtime.ext.h` inventory guard は `native/core` 正本を検査し、`core/py_runtime.ext.h` が forwarder であることも固定した。
- `tools/check/check_runtime_cpp_layout.py` の `py_runtime` duplicate scan は `native/core/py_runtime.ext.h` を優先して見るよう更新し、`test_runtime_symbol_index.py` では `pytra.core.dict` が public header は `core/dict.ext.h` のまま、ownership は `native` になることを固定した。
- `tools/check/check_runtime_cpp_layout.py` に「`runtime/cpp/native/core/...` を直接 include してよいのは `core/*.ext.h` forwarder だけ」という guard を追加し、synthetic test で generated runtime からの直接 include を fail-fast 化した。backend integration でも transpile 出力が `runtime/cpp/core/py_runtime.ext.h` を維持し、`native/core` を踏まないことを固定した。

## Phase 4 実施結果

- `src/runtime/cpp/generated/core/README.md` を追加し、`generated/core/` を「まだ real artifact が 0 件でも維持する正式レイアウト」として repo 上に定着させた。
- `tools/check/check_runtime_cpp_layout.py` は `generated/core` と `native/core` の directory 自体が存在しない場合も fail するよう更新し、ownership split lane の消失を防ぐ guard にした。
- compile/source 解決の representative proof は既存 synthetic unit を正式レイアウト前提に据えたまま維持し、`test_runtime_symbol_index.py` の `core/dict.ext.h -> generated/core/dict.ext.cpp + native/core/dict.ext.cpp` と `test_cpp_runtime_build_graph.py` の `runtime_cpp_candidates_from_header(core/dict.ext.h)` が green であることを再確認した。
- `generated/core` に置いてよい条件も固定した。許可するのは「pure Python SoT から機械変換でき、`core/...` include 面を崩さず、`native/core` 直 include や C++ 固有 ownership/ABI glue を必要としない low-level helper」のみとし、`gc/io`・object/container 表現・RC/GC・例外/I/O 集約・高レベル module runtime の逆流入は当面 `native/core` 側に留める。

## 分解

- [x] [ID: P0-CPP-CORE-OWNERSHIP-SPLIT-01] C++ low-level runtime (`core`) に `generated/core` + `native/core` を導入し、stable include 面を保ったまま generated/handwritten の物理混在を解消する。

- [x] [ID: P0-CPP-CORE-OWNERSHIP-SPLIT-01-S1-01] `src/runtime/cpp/core/` の既存ファイルを `compat surface` / `native 正本` / `generated 候補` / `非対象` に分類し、移行マップを作る。
- [x] [ID: P0-CPP-CORE-OWNERSHIP-SPLIT-01-S1-02] `core/` を互換 include 面、`generated/core` を生成正本、`native/core` を手書き正本とする契約を plan/spec に固定し、`pytra/core` を導入しない理由を明記する。

- [x] [ID: P0-CPP-CORE-OWNERSHIP-SPLIT-01-S2-01] `runtime_symbol_index` / `cpp_runtime_deps.py` / header 解決導線を `core` public header + `generated/native/core` compile source 前提へ拡張する。
- [x] [ID: P0-CPP-CORE-OWNERSHIP-SPLIT-01-S2-02] `check_runtime_cpp_layout.py` と `check_runtime_core_gen_markers.py` を core split 前提へ更新し、`core/` 実装再侵入・marker 混在を fail-fast 化する。

- [x] [ID: P0-CPP-CORE-OWNERSHIP-SPLIT-01-S3-01] handwritten core source (`gc/io` など) を `native/core/` へ移し、build graph と compile source 収集を同期する。
- [x] [ID: P0-CPP-CORE-OWNERSHIP-SPLIT-01-S3-02] handwritten core header (`py_runtime/py_types/list/dict/set/str` など) を `native/core/` 正本へ移し、`core/` には互換 forwarder / façade だけを残す。
- [x] [ID: P0-CPP-CORE-OWNERSHIP-SPLIT-01-S3-03] backend / generated runtime / tests の include 面を `core/...` 互換のまま維持しつつ、直接 `native/core` を踏まない規則を固定する。

- [x] [ID: P0-CPP-CORE-OWNERSHIP-SPLIT-01-S4-01] `generated/core/` の正式レイアウトを追加し、real candidate か synthetic fixture で compile/source 解決を 1 件実証する。
- [x] [ID: P0-CPP-CORE-OWNERSHIP-SPLIT-01-S4-02] generated/core に置く条件と、まだ置けない core helper を判定する基準を決定ログへ固定する。

- [x] [ID: P0-CPP-CORE-OWNERSHIP-SPLIT-01-S5-01] spec / README / representative tests を更新し、`core handwritten-only` 前提を廃止する。
- [x] [ID: P0-CPP-CORE-OWNERSHIP-SPLIT-01-S5-02] TODO / archive / guard を更新し、core ownership split を完了扱いで閉じる。

決定ログ:
- 2026-03-07: ユーザー指示により、`core/` に pure Python 由来 artifact を直接混在させない方針を固定し、`generated/core` + `native/core` の別計画を P0 として起票する。
- 2026-03-07: `pytra/core` は新しい public root としては導入せず、当面は `core/...` include 面を維持して互換コストを局所化する方針を採る。
- 2026-03-07: この計画の第一目的は「generated/core を今すぐ大量に作ること」ではなく、「将来 generated core が必要になっても ownership が混ざらない土台を先に作ること」とする。
- 2026-03-07: `src/runtime/cpp/core/` の既存 13 files を棚卸しし、`README.md` を除く 12 files はすべて handwritten core と判断した。`generated/core` へそのまま移せる既存 artifact は 0 件で、lane 実証は `S4-01` に切り出す。
- 2026-03-07: `core/` には `.cpp` 実体を残さず、`gc/io` の compile source は `native/core` へ移す。header は `core/*.ext.h` の互換 include 名を維持するため、最終的に forwarder として残す方針を固定した。
- 2026-03-07: `S1-02` として `spec-runtime` / `spec-abi` / `core/README` を更新し、`core/` は stable include surface、`generated/core` は SoT 由来正本、`native/core` は handwritten 正本とする契約を固定した。`pytra/core` は public root を二重化して ownership を曖昧にするため導入しない。
- 2026-03-07: `S2-01` として `runtime_symbol_index` / `cpp_runtime_deps` を future core split 対応に拡張した。`core/*.ext.h` は public header のまま維持し、compile source は `generated/core` / `native/core` / 現行 `core/*.ext.cpp` fallback の順で解決する。
- 2026-03-07: `S2-02` として `check_runtime_cpp_layout.py` / `check_runtime_core_gen_markers.py` を core split 前提へ更新した。移行期の `core/` には legacy baseline の `gc/io` 以外の `.cpp` を許さず、`pytra/core` も unsupported bucket として fail-fast にしたうえで、C++ `generated/core` / `native/core` / `core` surface の marker 契約を separate guard で固定した。
- 2026-03-07: `S3-01` として `gc.ext.cpp` / `io.ext.cpp` を `native/core/` へ移し、`core/` から handwritten compile source を除去した。`core/*.ext.h` include 面は維持しつつ、runtime symbol index・build graph・runtime smoke・image parity は `native/core/*.ext.cpp` を使うよう同期した。
- 2026-03-07: `S3-02` として `dict/exceptions/gc/io/list/py_runtime/py_scalar_types/py_types/set/str` の handwritten core header 正本を `native/core/` へ移し、`core/*.ext.h` はすべて forwarder に縮退させた。compile / parity / inventory guard は `core/...` 互換 include のまま green を維持し、`runtime_symbol_index` 上の core ownership も `ext` から `native` へ寄せた。
- 2026-03-07: `S3-03` として `native/core` の直接 include を `core/*.ext.h` forwarder だけに制限する guard を追加した。synthetic layout test で generated runtime からの直接 include を fail-fast にし、backend integration test では transpile 出力が引き続き `runtime/cpp/core/py_runtime.ext.h` を使い `runtime/cpp/native/core/...` を出さないことを固定した。
- 2026-03-07: `S4-01` として `src/runtime/cpp/generated/core/README.md` を追加し、`generated/core` を空レーンでも消してはいけない正式レイアウトへ昇格させた。`check_runtime_cpp_layout.py` は `generated/core` / `native/core` の directory 存在自体を要求するよう更新し、compile/source 解決の実証は `test_runtime_symbol_index.py` と `test_cpp_runtime_build_graph.py` の synthetic `dict.ext` ケースを green のまま維持する形で固定した。
- 2026-03-07: `S4-02` として `generated/core` の受け入れ基準を固定した。SoT から機械変換でき、`core/...` include 面を壊さず、`native/core` 直 include や C++ 固有 ownership/ABI glue を必要としない low-level helper だけを `generated/core` 候補とし、`gc/io`・object/container 表現・RC/GC・例外/I/O 集約・高レベル module runtime 逆流入は当面 `native/core` に留める。
- 2026-03-07: `S5-01` として `std/README.md` の layout boundary も新契約へ揃え、representative test に real repo の `core` surface + `generated/core` lane + `native/core` ownership assertion を追加した。これで `core handwritten-only` 前提を docs/test の両方から外した。
- 2026-03-07: `S5-02` として active TODO から本 P0 セクションを撤去し、plan を `docs/ja/plans/archive/20260307-p0-cpp-core-ownership-split.md` へ移した。`docs/ja/todo/archive/index.md` と `docs/ja/todo/archive/20260307.md` も同期し、次の最上位未完了を `P0-CPP-LIST-REFFIRST-01-S3-02` に戻した。
