# ランタイムの仕様について

<a href="../../en/spec/spec-runtime.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

### 0. 正本と責務境界

runtime の唯一正本（SoT）は、次の pure Python モジュール群とする。

- `src/pytra/built_in/*.py`
- `src/pytra/std/*.py`
- `src/pytra/utils/*.py`

必須ルール:

- SoT に書けるロジックは、runtime 側へ手で再実装してはならない。
- backend / emitter は、EAST で解決済みの module / symbol / signature を描画するだけとする。
- backend / emitter にライブラリ関数名、モジュール名、型名の変換テーブルや特別分岐を直書きしてはならない。
- `math`, `json`, `gif`, `png`, `Path`, `assertions`, `re`, `typing` などの知識を、変換器ソースコードへ埋めてはならない。

### 0.5 runtime 配置分類

全言語の runtime 配置は、責務として次の 4 区分に統一する。

- `core`
  - 低レベル runtime / ABI / object 表現 / GC / I/O / OS / SDK 接着など。
  - SoT の代替実装置き場ではない。
- `built_in`
  - `src/pytra/built_in/*.py` に対応する runtime 責務。
- `std`
  - `src/pytra/std/*.py` に対応する runtime 責務。
- `utils`
  - `src/pytra/utils/*.py` に対応する runtime 責務。

代表的な配置:

- 既定 / legacy:
  - `src/runtime/<lang>/core/`
  - `src/runtime/<lang>/built_in/`
  - `src/runtime/<lang>/std/`
  - `src/runtime/<lang>/utils/`
- 言語非依存の自動生成（`.east` 中間表現）:
  - `src/runtime/generated/{built_in,std,utils}/`
- 現行 C++ runtime（手書きのみ）:
  - `src/runtime/cpp/{core,built_in,std,compiler}/`

補足:

- `.east` ファイルは言語非依存の EAST3 JSON 中間表現。link 時に各ターゲット言語に変換される。
- `runtime/<lang>/` には手書きの言語固有コードのみ配置する。`native/` / `generated/` の階層は廃止済み。
- `built_in/std/utils` は SoT 由来の責務区分であり、同等ロジックを `core/` に複製してはならない。

### 0.6 runtime ファイル命名規則

runtime ファイルの ownership 表現:

- `.east` ファイル（`src/runtime/generated/`）:
  - `src/pytra/` の Python ソースから `pytra compile` で生成される EAST3 JSON。
  - link 時に各ターゲット言語に変換される。手編集禁止。
- 手書きファイル（`src/runtime/<lang>/`）:
  - 各ターゲット言語固有のランタイムコード。手書き。

意味:

- `.gen.*`
  - SoT から機械生成したファイル。
  - 手編集禁止。
- `.ext.*`
  - ABI 接着、OS / SDK 呼び出し、`@extern` の受け皿など、言語依存の最小実装。
  - 手編集可。
- `generated/`
  - C++ module runtime の自動生成正本。
- `native/`
  - C++ module runtime の target-language-specific companion。

必須ルール:

- `src/runtime/cpp/{built_in,std,utils}` に module runtime の `.h/.cpp` を新規追加してはならない。suffix ベース ownership は legacy-closed とする。
- 未移行 target では `.gen/.ext` を継続してよい。C++ `core` は plain naming (`core/*.h`, `native/core/*.{h,cpp}`) を正本とする。
- `*.ext.*` に SoT と同等の本体ロジックを書いてはならない。
- C++ module runtime の ownership は basename suffix ではなく `generated/native` のディレクトリで判別する。

例:

- `src/runtime/cpp/generated/std/math.h`
- `src/runtime/cpp/native/std/math.cpp`
- `src/runtime/cpp/generated/std/math.h`
- `src/runtime/cpp/native/core/py_runtime.h`

補足:

- `rc<list<T>>` のような backend 内部 typed handle helper を導入する場合も、配置先は `core/` とする。
- これは SoT 由来 module runtime ではなく、container / object 表現の低レベル支援層だからである。

### 0.6n C++ 以外の言語の native ファイル命名規則

C++ 以外（C#, Java, Rust, Go, Kotlin, Swift など）の `native/` ファイルは、次の命名規則に従う。

- native ファイル名: `<name>_native.<ext>`
- native クラス/モジュール名: `<name>_native`（ファイル名とクラス名を一致させる）

理由:

- C++ は `generated/` と `native/` で **同名ファイル**（`math.h` / `math.cpp` など）を使い、ディレクトリだけで ownership を区別できる。これはリンカ/インクルードシステムが同一シンボルを統合するモデルのため成立する。
- C++ 以外の言語では、`generated/std/os.cs` と `native/std/os.cs` が同一ビルドに含まれるとき、**ファイル名だけでは区別できない**（C# の場合はクラス名の衝突リスクもある）。
- `_native` suffix をファイル名・クラス名の両方に付けることで、**ファイル名 = クラス名**という各言語の慣習を守りつつ、generated 側との区別を明示する。

例（C#）:

- `src/runtime/cs/generated/std/os.cs` → `public static class os`（generated, SoT 由来）
- `src/runtime/cs/native/std/os_native.cs` → `public static class os_native`（native, host API 実装）

例（Java が将来対象になる場合）:

- `src/runtime/java/generated/std/os.java` → `class os`
- `src/runtime/java/native/std/os_native.java` → `class os_native`

必須ルール:

- C++ 以外の `native/std/<name>_native.<ext>` は、対応する `generated/std/<name>.<ext>` から委譲を受ける薄いラッパーとして実装する。
- `generated/` 側が `native/` 側へ委譲する形（`<name>_native.<method>()` 呼び出し）を正本とし、逆方向の依存を持ってはならない。
- `native/` 側に SoT と同等の本体ロジックを重複実装してはならない。host API への最小接続コードに限定する。
- コンパイラの最適化（インライン展開）により委譲コストは実質ゼロになることを前提とし、mix-in や partial class による単一ファイル化は行わない。

### 0.60 C++ module runtime の現行 layout

`src/runtime/cpp/` の checked-in runtime は、次の ownership layout を正本とする。

- `src/runtime/cpp/generated/{built_in,std,utils,core}/`
- `src/runtime/cpp/native/{built_in,std,utils,core}/`

意味:

- `generated/`
  - SoT から生成した checked-in runtime artifact。
- `native/`
  - hand-written canonical runtime と、C++ 固有 companion / ABI glue。

必須ルール:

- checked-in `src/runtime/cpp/{core,pytra}/**` は持たない。安定 SDK include surface が必要なら、source tree ではなく export/package 時に生成する。
- 生成コード / compiler / test は、`generated/...` または `native/core/...` の direct ownership header を使う。
- `runtime_symbol_index` では、C++ の `public_headers` と `compiler_headers` を direct ownership header へ揃える。
- 宣言の正本は原則 `generated/*.h` に置き、`native/*.h` は template / inline helper / ABI glue など本当に必要な場合だけに制限する。
- `native/` は「何でも手書きで置ける場所」ではなく、C++ 固有 companion に限定する。

補足:

- この layout を確立した移行ログは `docs/ja/plans/archive/20260307-p0-cpp-runtime-layout-generated-native.md` と `docs/ja/plans/archive/20260313-p0-cpp-runtime-packaging-deshim.md` に残す。
- `src/runtime/cpp/{built_in,std,utils}` の legacy flat/suffix ownership は closed とし、新規追加も再導入も禁止する。

### 0.601 C++ core runtime の ownership split

low-level runtime の責務名 `core` は維持するが、checked-in surface は `generated/core` と `native/core` に限る。

- `src/runtime/cpp/generated/core/`
  - pure Python SoT から変換できる low-level core artifact
- `src/runtime/cpp/native/core/`
  - handwritten low-level runtime 正本

必須ルール:

- low-level handwritten core は `native/core/` にのみ置く。
- pure helper として閉じる low-level core artifact だけを `generated/core/` に置く。
- checked-in `runtime/cpp/core/*.h` と `runtime/cpp/pytra/core/*.h` は再導入してはならない。
- compiler / generated runtime / native companion / backend 出力は `runtime/cpp/native/core/...` を直接 include する。
- `generated/core` / `generated/built_in` の artifact は、`src/py2x.py --emit-runtime-cpp` の正規導線だけで生成し、module 専用 generator や ad-hoc template を追加してはならない。
- `generated/core` / `generated/built_in` の checked-in artifact は、plain naming と `source:` / `generated-by:` marker を必須とする。
- export-time SDK が必要なら、runtime symbol index / manifest から生成する。source tree に互換 shim を常設してはならない。

### 0.61 include / 参照規約

- backend / build script / transpiler は、必要な runtime ファイルを ownership が判別できる正規名で参照する。
- 「人が書きやすい短い unsuffixed alias」を追加してはならない。
- include / compile 時の参照先は、その target の現行 ownership scheme から一意に決まるように保つ。

C++ では追加で次を守る。

- 生成コードが使う include は、runtime symbol index が返す direct ownership header に固定する（例: `generated/std/time.h`, `generated/utils/png.h`, `native/core/dict.h`）。
- 低レベル prelude は `runtime/cpp/native/core/py_runtime.h` を正本にする。
- `generated/` / `native/` の実パス解決は runtime symbol index と build graph 導線が担い、emitter が ad-hoc に直書きしてはならない。
- `--emit-runtime-cpp` は generated artifact だけを `src/runtime/cpp/generated/...` へ出力する。`native/` は companion 実装の置き場であり、自動生成出力先ではない。
- `runtime_symbol_index` / build graph は C++ の `public_headers == compiler_headers` を保ち、その direct ownership header から compile source を導出しなければならない。
- `check_runtime_cpp_layout.py` は `src/runtime/cpp/{core,pytra}` 再出現を fail させ、同時に `generated/native` の ownership 境界を監査しなければならない。
- C++ runtime に新しい include root を足してはならない。checked-in surface は direct ownership path だけに限定する。

### 0.62 `core` と module companion の境界

- C++ の low-level runtime は `generated/core` と `native/core` で表現し、standalone な checked-in `core/` surface は持たない。
- `std/utils/built_in` のモジュール補完実装は、C++ module runtime では `native/` に置く。
- `generated/core` / `native/core` に置いてよいのは、module 非依存の ABI / object / container / I/O / OS 接着だけとする。
- `rc<list<T>>` helper のような backend 内部 alias 維持層は `native/core` に置いてよいが、ABI 境界ではないことを docs/spec で明記する。
- `native/*.h` は template / inline helper など本当に必要な場合だけに制限し、宣言の正本は原則 `generated/*.h` へ寄せる。
- `native/core/*.h` は object / container 表現や low-level helper の正本を置いてよいが、high-level module runtime を再流入させてはならない。
- `generated/core/*.h|*.cpp` は real candidate がある場合だけ導入し、SoT marker を必須にする。

`py_runtime` については追加で次を守る。

- `src/runtime/cpp/native/core/py_runtime.h` は low-level runtime の canonical header であり、high-level built_in semantics の正本ではない。
- `src/runtime/cpp/native/core/py_runtime.h` に残してよいのは、`PyObj` / `object` / `rc<>` / type_id / low-level container primitive / dynamic iteration / process I/O / C++ 標準ライブラリ・OS glue だけとする。
- `str::split` / `splitlines` / `count` / `join`、`zip` / `sorted` / `sum` / `py_min` / `py_max` のような pure Python で表現可能な helper は `native/core/py_runtime.h` に permanent に残してはならず、`generated/built_in` または SoT 側へ戻す候補として扱う。
- generic helper（`sum/min/max/zip/sorted` など）は、`@template("T", ...)` + linked-program specialization を primary lane とし、`native/core/py_runtime.h` に新しい hand-written template helper を足して延命してはならない。
- `dict_get_*` / `py_dict_get_default` / `py_ord` / `py_chr` / `py_div` / `py_floordiv` / `py_mod` など、`object` / `std::any` / template specialization と密結合した helper は `generated/core` lane 設計前に性急に移してはならない。これらは保留分類を許容する。
- `generated/core` は「low-level helper の新しい捨て先」ではない。`native/core` 直 include や target 固有 ownership を必要とする helper を押し込んではならない。
- `check_runtime_cpp_layout.py` は、`native/core/py_runtime.h` が `predicates` / `sequence` / `iter_ops` の removed transitive include を再導入していないことも検証しなければならない。`string_ops` は `str` method delegate のため当面許容するが、他の built_in companion を集約器へ戻してはならない。

### 0.621 `generated/built_in` と `generated/core` の emission lane contract

`py_runtime` を slim 化するときは、helper を `generated/built_in` と `generated/core` のどちらへ流すかを次で固定する。

- `generated/built_in`
  - SoT は `src/pytra/built_in/*.py` に置く。
  - 役割は pure Python で表現可能な built_in semantics の checked-in C++ artifact 化であり、`str::split` / `splitlines` / `count` / `join`、object-specialized `zip` / `sorted` / `sum` / `min` / `max` のような helper を受ける。
  - generic helper は raw `@template` surface をそのまま backend へ見せず、linked-program specialization 後の specialized helper artifact として materialize する。backend は specialization collector を再実装してはならない。
  - template-only module は header-only generated artifact を許容し、`compile_sources=[]` が canonical になりうる。`numeric_ops` / `zip_ops` のような helper のために空の `.cpp` をでっち上げてはならない。
  - `.h` は stable `native/core/*.h` と、必要なら同名 module の `native/<bucket>/*.h` companion だけを include してよい。legacy shim path や無関係な handwritten glue をぶら下げてはならない。
  - `.cpp` は `runtime/cpp/native/core/py_runtime.h` と sibling generated header を include してよいが、C++ 専用 handwritten glue を埋め込んではならない。
  - mutable container を helper 境界で value 受けしたい場合は、`@abi` などの明示契約を使う。backend 内部の ref-first 表現を stable helper ABI として露出してはならない。
- `generated/core`
  - SoT は pure Python で書ける low-level helper に限定し、`built_in` / `std` / `utils` module runtime の単なる移植先として使ってはならない。
  - checked-in `runtime/cpp/core/*.h` は持たず、include 面は `generated/core` または `native/core` の ownership lane に揃える。
  - `object` / `rc<>` / container 表現 / GC / 例外 / process I/O の ownership をまたぐ helper は、`generated/core` へ性急に移してはならない。
  - `generated/core` は「low-level だが pure helper として閉じるもの」だけを受け、lane 設計なしに `native/core/py_runtime.h` の肥大化逃がしとして使ってはならない。
- 共通
  - build graph / runtime symbol index は direct ownership header（`public_headers` / `compiler_headers`）から compile source を導出し、emitter が ad-hoc に path を合成してはならない。
  - helper を移す判断は「pure Python で書けるか」だけでなく、「stable include 面を壊さないか」「ownership/ABI glue を新設しないか」で判定する。

### 0.622 JSON dynamic boundary と `JsonValue` 共通ADT

注記:

- 本節は承認済みの次段 target design を定義する。
- 2026-03-08 時点の現行実装では `json.loads()` が `object` を返す経路が残っていてよい。
- ただし新規実装・新規 helper・新規 runtime では、本節の contract を正本とする。

静的型付けを前提にする Pytra では、JSON の動的性を一般 `object` helper へ広げてはならない。
JSON 由来の動的境界は、`JsonValue` / `JsonObj` / `JsonArr` という JSON 専用 surface に閉じ込める。

必須ルール:

- `sum(object)`、`zip(object, object)`、`sorted(object)`、object overload の `dict.keys/items/values` など、user-facing の dynamic built-in helper を JSON のために追加してはならない。
- `object` 値に対して built-in / operator / collection helper を直接適用してはならない。user code は先に decode して concrete type へ落としてから使う。
- JSON decode のために plain assignment の意味を変えて implicit cast を導入してはならない。
- JSON の dynamic 性を理由に `native/core/py_runtime.h` へ hand-written fallback helper を増やしてはならない。

共通ADT:

- `JsonValue`
  - `Null`
  - `Bool`
  - `Int`
    - payload 型は `int64`
  - `Float`
    - payload 型は `float64`
  - `Str`
  - `Obj`
  - `Arr`
- `JsonObj`
  - 意味論上は `dict[str, JsonValue]`
- `JsonArr`
  - 意味論上は `list[JsonValue]`

source surface の方針:

- `json.loads(...)` の長期正規形は一般 `object` ではなく `JsonValue` とする。
- public module root は引き続き `pytra.std.json` とする。`json` が JSON 専用 nominal surface を持つようになっても、`utils/json.py` へ移してはならない。
- 理由は、`json` は Pytra 固有 utility ではなく stdlib compatibility family に属するためである。Pytra 独自の decode-first 契約を持っても、公開 namespace は `std` に固定する。
- user code は `JsonValue` / `JsonObj` / `JsonArr` の decode API を通して値を取り出す。
- general-purpose `cast` を JSON だけのために language-wide 必須機能として先行導入しなくてよい。
- 必要な narrowing は JSON module 専用 API に寄せる。

v1 decode surface（exact API）:

- `JsonValue.as_obj() -> JsonObj | None`
- `JsonValue.as_arr() -> JsonArr | None`
- `JsonValue.as_str() -> str | None`
- `JsonValue.as_int() -> int | None`
- `JsonValue.as_float() -> float | None`
- `JsonValue.as_bool() -> bool | None`
- `JsonObj.get(key: str) -> JsonValue | None`
- `JsonObj.get_obj(key: str) -> JsonObj | None`
- `JsonObj.get_arr(key: str) -> JsonArr | None`
- `JsonObj.get_str(key: str) -> str | None`
- `JsonObj.get_int(key: str) -> int | None`
- `JsonArr.get(index: int) -> JsonValue | None`
- `JsonArr.get_obj(index: int) -> JsonObj | None`
- `JsonArr.get_arr(index: int) -> JsonArr | None`
- `JsonArr.get_str(index: int) -> str | None`
- `JsonArr.get_int(index: int) -> int | None`
- `JsonArr.get_float(index: int) -> float | None`
- `JsonArr.get_bool(index: int) -> bool | None`

補足:

- `loads`, `loads_obj`, `loads_arr`, `JsonValue.as_*`, `JsonObj.get_*`, `JsonArr.get_*` を v1 の canonical API 名とする。
- v1 は general-purpose `cast` や `match` を前提にせず、上記 helper だけで decode できることを優先する。
- `match` による型分岐を後から導入してもよいが、それは `JsonValue` を decode しやすくする補助であって、dynamic helper 復活の理由にはならない。
- JSON number の判定規則は次で固定する。
  - 小数点と exponent を含まない number は `JsonValue.Int(int64)` として解釈する。
  - 小数点または exponent を含む number は `JsonValue.Float(float64)` として解釈する。
  - `int64` 範囲外の整数は parse error とする。
  - `NaN` / `Infinity` / `-Infinity` は JSON として不正であり受理してはならない。

backend lowering 方針:

- `JsonValue` は target 非依存の共通ADTとして定義し、各 backend は自言語で自然な tagged union / enum / variant へ落とす。
- v1 の優先実装順は `C++ -> Rust -> Swift -> Nim` とする。
- v1 の具体 carrier は次を正本とする。
  - C++:
    - `class JsonValue` + `std::variant<::std::monostate, bool, int64, float64, str, rc<JsonObj>, rc<JsonArr>>`
    - `JsonObj` は `dict<str, JsonValue>` を保持する nominal wrapper
    - `JsonArr` は `list<JsonValue>` を保持する nominal wrapper
  - Rust:
    - `enum JsonValue { Null, Bool(bool), Int(i64), Float(f64), Str(String), Obj(BTreeMap<String, JsonValue>), Arr(Vec<JsonValue>) }`
  - Swift:
    - `indirect enum JsonValue { case null, bool(Bool), int(Int64), float(Double), str(String), obj([String: JsonValue]), arr([JsonValue]) }`
  - Nim:
    - `ref object` + `kind` discriminator の tagged union
    - `obj` は `Table[string, JsonValue]`、`arr` は `seq[JsonValue]`
- 一時的に `object` や `dict[str, object]` / `list[object]` を内部 carrier に使う実装は許容してよいが、それは backend/runtime 内部 detail に限る。
- user-facing surface は `JsonValue` 系 nominal type を正本とし、一般 `object` surface を露出してはならない。

`py_runtime.h` との関係:

- `sum(object)` / `zip(object, object)` / object overload の `dict.keys/items/values` は permanent API にしてはならない。
- これらは legacy compatibility debt としてのみ一時残存を許容し、段階的に compile error へ寄せる。
- `json.loads()` を使う user code は、dynamic helper ではなく `JsonValue` decode API を通る前提で書けるようにする。
- `native/core/py_runtime.h` に残してよいのは JSON carrier と low-level bridge の最小実装だけとし、user-facing dynamic algorithm helper は残してはならない。

誤りの例:

- `std/math` の補完実装を `core/` に置く
- `utils/png` の本体を `core/` に手書きする
- `built_in` 由来ロジックを `py_runtime` へ埋め込む
- `py_runtime` の肥大化を避けるために low-level helper まで無差別に `generated/built_in` へ逃がす

### 0.63 特殊生成スクリプト禁止

- `src/py2x.py` / 将来の統一 CLI を通さずに、特定モジュール専用の runtime 生成スクリプトを追加してはならない。
- `png.py`, `gif.py`, `json.py`, `math.py` などは、必ず正規の変換器経由で target の正規 runtime artifact を生成する。
- runtime 生成のために、言語別の特別命名や特別テンプレートを追加してはならない。

### 0.64 `src/pytra` での `__all__` 禁止

`src/pytra/**/*.py` では `__all__` を定義してはならない。

- selfhost 実装・変換器実装の単純性を優先する。
- 公開シンボル制御は、トップレベル定義の有無で表現する。
- `built_in/std/utils` の SoT モジュールも同様に `__all__` を使わない。

### 0.65 host-only import alias 規約（`as __name`）

`import ... as __m` / `from ... import ... as __f` のように alias が `__` で始まる import は host-only import として扱う。

- host-only import は Python 実行時補助専用とする。
- 主用途は `@extern` 関数の Python フォールバック本体評価。
- トランスパイラは host-only import を EAST の `Import` / `ImportFrom` として出力しない。
- `_name` のように `_` 1 個だけの alias は host-only ではない。

### 0.66 標準ライブラリのサブモジュール実装規約

`os.path` のような標準ライブラリのサブモジュールは、独立した SoT モジュールとして扱う。

必須:

- サブモジュールは `src/pytra/std/<name>.py` に分離する。
  - 例: `os.path` -> `src/pytra/std/os_path.py`
- 親モジュールはモジュール import で参照する。
  - 例: `from pytra.std import os_path as path`
- 呼び出しは module function call として維持する。
  - 例: `path.join(...)`
- native 実装が必要な関数は、SoT 側で `@extern` 宣言し、runtime 側では対応する companion 層に実体を置く。
  - C++ module runtime では `native/`
- `extern_contract_v1` / `extern_v1` は declaration-only metadata として扱い、native owner 実装の所在を表してはならない。
- ambient global 変数宣言の `extern()` / `extern("symbol")` は runtime SoT `@extern` とは別系統であり、runtime symbol index の native owner 決定へ混ぜてはならない。

禁止:

- サブモジュールを `object` 変数に格納する実装
- emitter / runtime でサブモジュール名に依存した特別分岐を足す実装

### 0.67 mutable 型の内部表現ポリシー

runtime / backend の内部表現は、ABI の正規形とは別に次の原則で決める。

必須ルール:

- immutable 型は value-first でよい。
  - 例: `bool`, `int`, `float`, `str`
- mutable 型は ref-first とする。
  - 例: `list`, `dict`, `set`, `bytearray`, mutable な user class
- C++ backend では、ref-first 表現として `rc<>` や同等の typed handle を使ってよい。
- ただし、これは backend 内部表現であり、ABI ではない。`@extern` 境界や言語間境界へそのまま露出してはならない。

値型縮退は、最適化の結果としてのみ許可する。

- mutable 型を「最初から値型」とみなしてはいけない。
- 値型縮退には mutation / alias / escape の解析が必要である。
- 関数をまたぐ縮退には call graph と SCC 固定点計算が必要である。
- unknown call / `Any` / `object` / `@extern` / 外部 SDK 境界をまたぐ経路は fail-closed とし、ref-first のまま残す。

補足:

- `str` のような immutable 型を値型で持つことと、`list` / `dict` を値型で持つことは同列ではない。
- `a = b` 後の破壊的更新が観測されうる型は、共有参照が正本である。
- 「一旦 ref-first にして、証明できた経路だけ stack/value へ縮退する」という順序を崩してはならない。

### 0.68 runtime symbol index と backend の責務境界

runtime symbol の所属 module と target artifact は、`tools/runtime_symbol_index.json` を正とする。

必須ルール:

- IR は target 非依存な `runtime_module_id` と `runtime_symbol` を保持する。
- backend は `runtime_module_id` / `runtime_symbol` を受け取り、target 別の include path / compile source / companion を index から導出する。
- `runtime/cpp/generated/std/time.h` のような target 固有 path を IR に埋めてはならない。
- `py_enumerate -> iter_ops` のような module 所属対応を backend/emitter ソースへ再直書きしてはならない。
- backend/emitter が決めてよいのは target 固有の描画名・namespace・構文だけである。

backend が解釈してよい runtime metadata:

- `runtime_module_id`
- `runtime_symbol`
- declaration-only `extern_contract_v1` / `extern_v1`
- `semantic_tag`
- `runtime_call`
- `resolved_runtime_call`
- `resolved_runtime_source`
- linker/lowerer が付与する adapter kind / ABI kind / import binding metadata

backend が解釈してはならない source-side knowledge:

- source import 名そのもの
  - 例: `math`, `pytra.utils`, `pytra.std.math`
- source module attr の語形
  - 例: `.pi`, `.e`, `.sqrt`
- helper 固有名
  - 例: `pyMathPi`, `pyMathE`, `save_gif`, `write_rgb_png`, `grayscale_palette`
- helper の引数 ABI を推測するための ad-hoc 規則
  - 例: `save_gif` の arity / default / keyword (`delay_cs`, `loop`) を emitter が直解釈すること

補足:

- `resolved_runtime_call` や `semantic_tag` を target symbol へ写すこと自体は許可される。
- ただし、その変換は source-side module 名や helper 名の文字列一致ではなく、index / lowerer が決めた metadata に従って行わなければならない。

責務の分担:

- IR:
  - `runtime_module_id`
  - `runtime_symbol`
  - 必要最小限の dispatch 情報
- runtime symbol index:
  - module ごとの公開 symbol
  - target ごとの `public_headers`
  - target ごとの `compile_sources`
  - `gen/ext` companion
- backend/tooling:
  - include の dedupe / sort
  - namespace 文字列の描画
  - build graph 構成

非C++ backend への適用方針:

- C++ を先行実装としつつ、他 backend も同じ `runtime_module_id + runtime_symbol + index` 契約へ揃える。
- 非C++ backend は target 固有の public import / package path を持ってよいが、その解決は index 消費層で行う。
- `resolved_runtime_call` や module/file path の対応を backend ごとに別々の手書き table として再実装してはならない。
- target ごとに異なるのは「どう import するか」「どう fully-qualified name を描画するか」であって、「どの module がその symbol を持つか」ではない。
- `pyMath*` / `scala.math.*` / `png_helper` のような target helper 名は、最終描画結果に現れてよいが、source module 名や helper ABI の分岐条件として emitter 正本に残してはならない。

### 0.7 C++ runtime の運用

C++ runtime は次を正規配置とする。

- `src/runtime/cpp/generated/{built_in,std,utils,core}/`
- `src/runtime/cpp/native/{built_in,std,utils,core}/`

再生成:

- `built_in/std/utils/core` の SoT 由来モジュールは `--emit-runtime-cpp` で `generated/` へ生成する。
- 例:
  - `python3 src/py2x.py src/pytra/built_in/type_id.py --target cpp --emit-runtime-cpp`
  - `python3 src/py2x.py src/pytra/std/math.py --target cpp --emit-runtime-cpp`
  - `python3 src/py2x.py src/pytra/utils/png.py --target cpp --emit-runtime-cpp`

最低限の検証:

- `python3 tools/check_runtime_cpp_layout.py`
- `python3 tools/check_runtime_std_sot_guard.py`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root sample --all-samples`

禁止事項:

- `src/runtime/cpp/generated/**` の手編集
- `src/runtime/cpp/native/core/**` や `src/runtime/cpp/native/{built_in,std,utils}/**` への SoT 同等ロジック再実装
- checked-in `src/runtime/cpp/{core,pytra}/**` の再導入
- backend / emitter での module / symbol 名の直書き解決
- runtime 生成のためのモジュール専用スクリプト追加

### 0.71 多言語 runtime への適用

この分類と命名規則は C++ 専用ではなく、全言語 runtime へ広げる。

- canonical target layout は `src/runtime/<lang>/generated/**` と `src/runtime/<lang>/native/**` である。
- non-C++ runtime の baseline end state は、`cpp/generated/{built_in,std,utils}` の module set を基準に `generated = baseline` を満たすこととする。
- baseline module に対して `blocked` / `compare_artifact` / `no_runtime_module` / `helper_artifact` / `native canonical` を close 条件として使ってはならない。
- `src/toolchain/compiler/noncpp_runtime_layout_contract.py` と `src/toolchain/compiler/noncpp_runtime_layout_rollout_remaining_contract.py` が保持する blocked/native/helper の記述は legacy inventory であり、active end-state policy ではない。
- `pytra-gen/pytra-core` や checked-in `pytra/**` は互換 debt inventory であり、最終形ではない。

各言語 backend は、SoT 由来コードを canonical generated lane に生成し、必要最小限の handwritten companion だけを native lane へ置く。

### 0.72 Runtime `@extern` Ownership Metadata

- `extern_contract_v1` / `extern_v1` は declaration-only metadata として扱い、native owner 実装の所在を表してはならない。
- ambient global 変数宣言の `extern()` / `extern("symbol")` は runtime SoT `@extern` とは別系統であり、runtime symbol index の native owner 決定へ混ぜてはならない。
