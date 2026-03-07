# P1: C++ `py_runtime` を低レベル glue へ縮退させる

最終更新: 2026-03-08

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-CPP-PY-RUNTIME-SLIM-01`

背景:
- 現在の C++ core include surface である `src/runtime/cpp/core/py_runtime.h` は shim に縮退済みだが、実体の `src/runtime/cpp/native/core/py_runtime.h` は依然として巨大で、low-level ABI / object 表現 / GC glue だけでなく、pure Python で表現可能な built_in 意味論も相当量含んでいる。
- 代表例として、`str::split` / `splitlines` / `count` / `join` のような文字列処理、`object` / `list` / `dict` / `set` の高水準 helper、汎用 predicate / iteration 補助の一部は、C++ 固有 ABI 接着ではなく、SoT 由来の built_in runtime として分離可能である。
- ただし `str.join` のように `list[str]` を value ABI 正規形で受けたい helper は、naive に generated 化すると C++ internal ref-first model に引かれて `rc<list<str>>` へ寄る危険がある。このため、generated helper 境界に固定 ABI を与える `@abi` 導入が先行で必要になる。
- `spec-runtime` は、`built_in` 由来ロジックを `py_runtime` へ埋め込むことを誤り例として明示している。一方で `rc<>`、GC、`PyObj`、`type_id`、I/O / OS 接着などの low-level 責務は `core/` に残すべきと定義している。[spec-runtime.md](../spec/spec-runtime.md)
- この状態のままだと、C++ でしか使えない手書き runtime が肥大化し、他言語 runtime と SoT の共有可能範囲が狭くなる。pure Python で書ける意味論を SoT / generated 側へ戻せば、他言語 runtime の実装量も縮小できる。
- ただし、これは linked-program 導入や backend 側 knowledge leak 撤去より後段の整理である。先に compiler 側の責務境界を固め、その後に runtime ownership を整理する方が安全である。

目的:
- `native/core/py_runtime.h` から「pure Python SoT へ戻せる意味論」を分離し、`core/` を low-level ABI / object / container / runtime glue 中心の層へ縮退させる。
- SoT で表現できる built_in semantics は `src/pytra/built_in/*.py` へ戻し、必要に応じて C++ では `generated/core/` または `generated/built_in/` として生成できる形へ寄せる。
- 他言語 runtime でも共有できる意味論を手書き C++ core に閉じ込めないことで、runtime の重複実装を減らす。
- `py_runtime` には「C++ でしか書けないもの」「ABI 境界で必要なもの」だけを残す。

対象:
- `src/runtime/cpp/native/core/py_runtime.h`
- `src/runtime/cpp/core/py_runtime.h`
- `src/runtime/cpp/generated/core/`
- 必要に応じて `src/pytra/built_in/*.py`
- C++ runtime generation / symbol index / build graph / representative tests
- `docs/ja/spec/spec-runtime.md`
- 必要に応じて `docs/ja/spec/spec-dev.md`

非対象:
- linked-program 導入そのもの
- backend 側の runtime module 知識漏れ撤去
- `std` / `utils` runtime の ownership 再編
- `core/` include root を `pytra/core` へ変更すること
- `rc<>` / GC / `PyObj` を pure Python で再実装すること
- いま動いている C++ runtime ABI を一気に刷新すること

受け入れ基準:
- `native/core/py_runtime.h` に残るロジックは、`GC` / `PyObj` / `object` / `type_id` / low-level container 表現 / I/O / OS / ABI glue / target-language-specific helper に概ね限定される。
- pure Python で表現可能な built_in semantics は、`native/core/py_runtime.h` から撤去されるか、少なくとも「generated/core` または `generated/built_in` へ移す候補」として棚卸し・分類済みになる。
- `core/py_runtime.h` は引き続き stable include surface を維持するが、意味論の正本は `native/core` 以外へ戻せる部分から順次戻す。
- SoT へ戻したロジックは C++ 以外でも再利用可能な形になり、他言語 runtime 縮小の障害にならない。
- representative C++ runtime / backend / parity test が非退行で通る。
- `spec-runtime` に「`py_runtime` に残してよいもの / 残してはいけないもの」の境界が明文化される。

依存関係:
- 先行して `P0-LINKED-PROGRAM-OPT-01` を完了させる。
- 可能なら `P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01` の主要方針も先に固定する。
- `P1-RUNTIME-ABI-DECORATOR-01` を先に進め、generated/helper 境界で `value_readonly` / `value` を指定できるようにする。
- 本計画はそれら完了後に着手する P1 とする。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_runtime_cpp_layout.py`
- `python3 tools/check_runtime_core_gen_markers.py`
- `python3 tools/gen_runtime_symbol_index.py --check`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_cpp_runtime_*.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_*.py'`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root sample --all-samples`

## 1. 問題の本質

問題は「`py_runtime.h` が大きいこと」自体ではない。  
本質は、異なる ownership のロジックが 1 ファイルへ混在していることにある。

現状の `native/core/py_runtime.h` には、少なくとも次の 4 種類が混在している。

1. genuinely native / low-level
   - `PyObj`
   - `object`
   - GC 接着
   - `type_id`
   - `argv/stdout/stderr`
   - `filesystem` / `fstream` / `regex` など C++ 標準ライブラリ・OS 接着
2. core container/object representation helper
   - `rc<list<T>>`
   - `obj_to_*`
   - `py_to_*`
   - `py_at` / `py_set_at` / `py_append` のような low-level operation
3. pure Python で書ける built_in semantics
   - 文字列分割・カウント・結合
   - iterable / predicate / sequence 補助の一部
   - 汎用 list/dict/set helper の一部
4. 生成 runtime への bridge / include 集約
   - `generated/built_in/*.h` をまとめて取り込む薄い glue

このうち 1 と 2 は `core` に残してよい。  
問題は 3 が `native/core` に残っていることで、SoT と他言語共有の障害になっている。

## 2. 分離原則

本計画では、`py_runtime` 内の各要素を次のいずれかへ振り分ける。

- `native/core` に残す
  - C++ 固有 ABI / memory / OS / SDK glue
  - `PyObj` / `object` / `rc<>`
  - `type_id`
  - low-level container representation
  - runtime process / I/O state
- `generated/core` へ移す
  - low-level だが pure Python SoT から機械変換可能な helper
  - 他 module に依存せず、`native/core` 直 include を必要としない helper
- `generated/built_in` へ移す
  - built_in module 由来の意味論
  - `src/pytra/built_in/*.py` を正本に戻せるもの
- `native/built_in` に置く
  - built_in semantics だが、C++ 標準ライブラリ / ABI glue を薄く必要とする companion

重要な禁止事項:

- `native/core` を「とりあえず置ける手書き箱」にしない。
- pure Python で戻せるものを、便利だからという理由で `py_runtime` に残さない。
- 逆に `GC` / `PyObj` / `type_id` を無理に SoT 化しない。

## 3. 残すもの / 移すものの判断基準

### 3.1 `native/core` に残すべきもの

- `PyObj` の継承体系
- `object` ハンドル管理
- RC / GC の low-level 操作
- `type_id` 登録と subtype 判定
- `PyFile` / I/O / `argv`
- `filesystem` / `regex` など OS / C++ runtime 接着
- target-specific fast path

### 3.2 SoT / generated 側へ戻すべき候補

- `str.split`
- `str.splitlines`
- `str.count`
- `str.join`
- 汎用 iterable / sequence helper のうち pure Python で表現可能なもの
- built_in predicates / collection helper のうち ABI glue でないもの

### 3.3 境界上の候補

以下は単純に移せない可能性があるため、実装前に分類を確定する。

- `object` を介した dynamic dispatch helper
- `list<object>` / `dict<str, object>` ベースの boxing / unboxing 補助
- `rc<list<T>>` と value list の相互変換 helper
- template / inline 前提で header に残す必要があるもの

## 4. 実装方針

### Phase 1: 棚卸し

- `native/core/py_runtime.h` の全ロジックを function / class / helper 単位で棚卸しする。
- 各項目を `native/core` / `generated/core` / `generated/built_in` / `native/built_in` / 保留 に分類する。
- 代表例を文書とテストで固定する。

### Phase 2: 契約固定

- `spec-runtime` / `spec-dev` に `py_runtime` の責務境界を追記する。
- `generated/core` に置けるものの条件を具体化する。
- `native/core/py_runtime.h` は「最終的に low-level aggregator へ縮退する」ことを明文化する。

### Phase 3: SoT 側の受け皿作成

- `src/pytra/built_in/*.py` に戻せるロジックを追加・分割する。
- 必要なら `generated/core` の emission lane を整える。
- C++ 側だけの暫定 wrapper でごまかさず、SoT へ戻せるものは戻す。

### Phase 4: C++ 実装移行

- `native/core/py_runtime.h` から pure-Python semantics を撤去する。
- `core/py_runtime.h` の stable include surface は維持する。
- include 経路、symbol index、build graph、tests を追従させる。

### Phase 5: 非退行確認と guard

- representative runtime tests / sample parity を再実行する。
- `py_runtime` へ SoT 由来 semantics が再侵入したときに検知できる guard の必要性を評価し、必要なら追加する。

## 5. 具体タスク分解

- [x] [ID: P1-CPP-PY-RUNTIME-SLIM-01-S1-01] `native/core/py_runtime.h` の function/class/helper を棚卸しし、`native/core` / `generated/core` / `generated/built_in` / `native/built_in` / 保留へ分類する。
- [ ] [ID: P1-CPP-PY-RUNTIME-SLIM-01-S1-02] `spec-runtime` / `spec-dev` に `py_runtime` の責務境界と「残してよいもの / 戻すべきもの」を明文化する。
- [ ] [ID: P1-CPP-PY-RUNTIME-SLIM-01-S2-01] `src/pytra/built_in/*.py` 側へ戻す候補を決め、SoT 上の配置案を固定する。
- [ ] [ID: P1-CPP-PY-RUNTIME-SLIM-01-S2-02] `generated/core` または `generated/built_in` の emission lane に必要な generator / layout 契約を整備する。
- [ ] [ID: P1-CPP-PY-RUNTIME-SLIM-01-S3-01] 文字列・collection 系の pure-Python built_in semantics を `native/core/py_runtime.h` から段階的に撤去し、正規の generated lane へ移す。
- [ ] [ID: P1-CPP-PY-RUNTIME-SLIM-01-S3-02] `native/core/py_runtime.h` を low-level ABI / object / container / process glue 中心へ整理し、include 集約を最小化する。
- [ ] [ID: P1-CPP-PY-RUNTIME-SLIM-01-S4-01] runtime symbol index / build graph / representative C++ runtime tests を新しい ownership に追従させる。
- [ ] [ID: P1-CPP-PY-RUNTIME-SLIM-01-S4-02] fixture/sample parity・docs 同期・必要な guard 追加まで完了し、本計画を閉じる。

## 5.1 棚卸し結果

対象ファイル: [src/runtime/cpp/native/core/py_runtime.h](../../../src/runtime/cpp/native/core/py_runtime.h)

`native/core` に残す確定群:
- `PyIntObj` / `PyFloatObj` / `PyBoolObj` / `PyStrObj` / `PyListObj` / `PyDictObj` / `PySetObj` と iterator object 群（`PyListIterObj` / `PyDictKeyIterObj` / `PyStrIterObj`）。
- `object_new` / `make_object` / `obj_to_*` / `py_to*` / `py_len` / `py_to_string` などの boxing / unboxing / dynamic conversion family。
- `py_list_*` / `py_dict_*` / `py_at` / `py_slice` / `py_append` / `py_set_at` / `py_extend` / `py_pop` / `py_clear` / `py_reverse` / `py_sort` の low-level container primitive family。
- `py_runtime_user_type_base_registry` / `py_register_class_type` / `py_is_subtype` / `py_runtime_type_id` / `py_isinstance` の type_id / subtype registry family。
- `py_iter_or_raise` / `py_next_or_stop` / `py_dyn_range_*` / operator overload 群 / `py_runtime_argv*` / `py_runtime_write_stdout` / `py_runtime_write_stderr` などの process / dynamic dispatch / C++ glue family。

`generated/built_in` へ戻す確定候補:
- `str::split` / `splitlines` / `count` / `join`。この4件は pure Python SoT へ戻せる文字列 built_in semantics で、`join` は `@abi` lane で先行実証済み。
- `zip` / `sorted` / `sum` / `py_min` / `py_max`。いずれも高水準 built_in algorithm で、`native/core` に置く必然が薄い。

`generated/core` の即時確定候補:
- 現時点では 0 件。`py_runtime.h` 内の generic helper は大半が `object` / `std::any` / template / operator overload と密結合しており、low-level ownership を切らずに pure helper だけ抜くには lane 設計が先に必要。

`native/built_in` の即時確定候補:
- 現時点では 0 件。`py_runtime.h` 内の high-level helper で C++ 標準ライブラリ glue が本質なものはまだ薄くなく、まずは `generated/built_in` へ戻せる群を優先する。

保留:
- `py_ord` / `py_chr` / `py_to_int64_base` などの scalar conversion family。
- `dict_get_*` / `dict_get_node` / `py_dict_get_default` などの dynamic object access convenience family。
- `py_div` / `py_floordiv` / `py_mod` と object/`std::any` operator overload family。
- `py_dict_items` / `py_dict_keys` / `py_dict_values` と `py_at(const str&)` を含む mixed helper family。

保留理由:
- いずれも pure Python semantics に見える一方で、`object` / `std::any` / `optional` / template specialization と結びついており、`generated/core` lane の設計なしに切り離すと ownership と include 依存を壊しやすい。
- `generated/built_in` へ戻すべきか `native/core` に残すべきかは、`S1-02` の責務境界固定と `S2-02` の emission lane 設計後に再判定する。

## 6. リスク

- `template` / `inline` 依存が強い helper は、単純に `.cpp` へ逃がせない。
- 文字列・collection helper は他の core header に分散しており、`py_runtime` だけを見て移すと依存方向を壊す可能性がある。
- SoT 側へ戻した結果、他言語 backend の既存 runtime 生成に波及するため、C++ 単独改修のつもりで始めると blast radius を見誤る。
- そのため、最初の段階では「まず棚卸しと ownership 固定」を優先し、移行は段階的に進める。

## 決定ログ

- 2026-03-07: `py_runtime.h` を単に小さくするのではなく、「pure Python で書ける意味論を SoT / generated 側へ戻し、`native/core` を low-level glue へ縮退させる」ことを本計画の目的とした。
- 2026-03-07: 優先順位としては、P0-LINKED-PROGRAM-OPT-01 と P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01 の後段で扱うのが安全と判断し、P1 へ積む方針を採用した。
- 2026-03-07: `str.join` など `list[...]` helper を pure Python SoT へ戻すには、generated helper 側に fixed ABI override が必要と判断した。そのため P1-RUNTIME-ABI-DECORATOR-01 を本計画の先行依存に追加した。
- 2026-03-08: runtime-abi decorator plan が完了し、`src/pytra/built_in/string_ops.py` の `py_join` は `@abi(args={"parts": "value_readonly"}, ret="value")` 付き pure Python SoT として generated C++ helper へ移行済みになった。`py_runtime` 縮退では同じ fixed-ABI helper lane を再利用できるため、`str.join` は blocker ではなく代表移行済みケースとして扱う。
- 2026-03-08: [ID: P1-CPP-PY-RUNTIME-SLIM-01-S1-01] `src/runtime/cpp/native/core/py_runtime.h`（3267行）を family 単位で棚卸しし、low-level core / generated built_in 候補 / 保留へ分類した。`str::split` / `splitlines` / `count` / `join` と `zip` / `sorted` / `sum` / `py_min` / `py_max` は `generated/built_in` 候補として確定し、`generated/core` / `native/built_in` は現段階では即時確定 0 件とした。
