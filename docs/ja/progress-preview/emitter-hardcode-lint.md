<a href="../../en/progress-preview/emitter-hardcode-lint.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# emitter ハードコード違反マトリクス

> 機械生成ファイル。`python3 tools/check/check_emitter_hardcode_lint.py` で更新する。
> 生成日時: 2026-04-01T12:05:04
> [関連リンク](./index.md)

emitter が EAST3 の情報を使わず、モジュール名・runtime 関数名・クラス名等を文字列で直書きしている箇所を grep で検出したマトリクス。
違反数が 0 に近づくほど emitter が EAST3 正本に従った実装になっている。

| アイコン | 意味 |
|---|---|
| 🟩 | 違反なし |
| 🟥 | 違反あり（詳細は下の表を参照） |
| ⬜ | 未実装（toolchain2 に emitter なし） |

> **js** は独自 emitter を持たず **ts** emitter を共用するため、js 列は ts と同一の結果を表示する。

| カテゴリ | cpp | rs | cs | ps1 | js | ts | dart | go | java | swift | kotlin | ruby | lua | scala | php | nim | julia | zig |
|--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| module name | 🟩 | 🟥 | 🟩 | ⬜ | 🟩 | 🟩 | ⬜ | 🟩 | 🟩 | ⬜ | ⬜ | 🟩 | 🟥 | ⬜ | 🟩 | 🟩 | ⬜ | ⬜ |
| runtime symbol | 🟩 | 🟩 | 🟩 | ⬜ | 🟩 | 🟩 | ⬜ | 🟩 | 🟩 | ⬜ | ⬜ | 🟩 | 🟩 | ⬜ | 🟩 | 🟩 | ⬜ | ⬜ |
| target const | 🟩 | 🟩 | 🟩 | ⬜ | 🟩 | 🟩 | ⬜ | 🟩 | 🟩 | ⬜ | ⬜ | 🟩 | 🟩 | ⬜ | 🟩 | 🟩 | ⬜ | ⬜ |
| prefix match | 🟥 | 🟩 | 🟩 | ⬜ | 🟩 | 🟩 | ⬜ | 🟩 | 🟩 | ⬜ | ⬜ | 🟩 | 🟩 | ⬜ | 🟩 | 🟩 | ⬜ | ⬜ |
| class name | 🟩 | 🟥 | 🟩 | ⬜ | 🟩 | 🟩 | ⬜ | 🟩 | 🟩 | ⬜ | ⬜ | 🟥 | 🟩 | ⬜ | 🟥 | 🟥 | ⬜ | ⬜ |
| Python syntax | 🟩 | 🟩 | 🟩 | ⬜ | 🟩 | 🟩 | ⬜ | 🟩 | 🟩 | ⬜ | ⬜ | 🟥 | 🟩 | ⬜ | 🟩 | 🟥 | ⬜ | ⬜ |
| type_id | 🟩 | 🟩 | 🟩 | ⬜ | 🟥 | 🟥 | ⬜ | 🟩 | 🟩 | ⬜ | ⬜ | 🟩 | 🟩 | ⬜ | 🟩 | 🟩 | ⬜ | ⬜ |
| skip pure py | 🟩 | 🟩 | 🟩 | ⬜ | 🟩 | 🟩 | ⬜ | 🟥 | 🟩 | ⬜ | ⬜ | 🟥 | 🟩 | ⬜ | 🟥 | 🟥 | ⬜ | ⬜ |
| rt: type_id | 🟥 | 🟥 | 🟥 | ⬜ | 🟥 | 🟥 | 🟩 | 🟥 | 🟩 | 🟩 | 🟩 | 🟥 | 🟥 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 |
| **🟩 PASS** | 7 | 6 | 8 | — | 7 | 7 | 1 | 7 | 9 | 1 | 1 | 5 | 7 | 1 | 7 | 6 | 1 | 1 |
| **🟥 FAIL** | 2 | 3 | 1 | — | 2 | 2 | — | 2 | — | — | — | 4 | 2 | — | 2 | 3 | — | — |
| **⬜ 未実装** | — | — | — | 9 | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

## 詳細

### class_name / nim (1)

```
src/toolchain2/emit/nim/emitter.py:154: "Exception", "BaseException", "RuntimeError", "ValueError",
```

### class_name / php (2)

```
src/toolchain2/emit/php/emitter.py:143: "Exception", "BaseException", "RuntimeError", "ValueError",
src/toolchain2/emit/php/emitter.py:1178: if exc_rt in ("Exception", "RuntimeError", "ValueError", "TypeError", "IndexError", "KeyError"):
```

### class_name / rs (1)

```
src/toolchain2/emit/rs/emitter.py:1433: is_path_ref = inner_rs in ("Path", "PyPath", "pathlib.Path", "pytra.std.pathlib.Path") or inner_rs.endswith(".Path")
```

### class_name / ruby (1)

```
src/toolchain2/emit/ruby/emitter.py:131: "Exception", "RuntimeError", "ValueError", "TypeError",
```

### module_name / lua (1)

```
src/toolchain2/emit/lua/emitter.py:1945: if mod_name == "math":
```

### module_name / rs (5)

```
src/toolchain2/emit/rs/emitter.py:1394: if module_id == "os" and attr == "environ":
src/toolchain2/emit/rs/emitter.py:1992: if mod_name == "os":
src/toolchain2/emit/rs/emitter.py:1994: if mod_name == "subprocess":
src/toolchain2/emit/rs/emitter.py:2775: if method == "glob" and len(rendered_args) == 1:
src/toolchain2/emit/rs/emitter.py:3899: if mod_name in ("os", "subprocess"):
```

### prefix_match / cpp (1)

```
src/toolchain2/emit/cpp/runtime_paths.py:28: rel = resolve_runtime_module_rel_tail("pytra.std." + module_id)
```

### python_syntax / nim (1)

```
src/toolchain2/emit/nim/emitter.py:891: if attr == "__init__" and isinstance(owner_node, dict) and _str(owner_node, "repr") == "super()":
```

### python_syntax / ruby (2)

```
src/toolchain2/emit/ruby/emitter.py:757: if isinstance(owner_node, dict) and _str(owner_node, "repr") == "super()":
src/toolchain2/emit/ruby/emitter.py:1644: _emit(ctx, "super()")
```

### rt:type_id / cpp (48)

```
src/runtime/cpp/built_in/base_ops.h:68: if constexpr (::std::is_same_v<Exact, bool>) return value.type_id() == PYTRA_TID_BOOL;
src/runtime/cpp/built_in/base_ops.h:69: else if constexpr (::std::is_same_v<Exact, int64>) return value.type_id() == PYTRA_TID_INT;
src/runtime/cpp/built_in/base_ops.h:70: else if constexpr (::std::is_same_v<Exact, float64>) return value.type_id() == PYTRA_TID_FLOAT;
src/runtime/cpp/built_in/base_ops.h:71: else if constexpr (::std::is_same_v<Exact, str>) return value.type_id() == PYTRA_TID_STR;
src/runtime/cpp/built_in/base_ops.h:86: return static_cast<bool>(v) && v.type_id() == PYTRA_TID_BOOL;
src/runtime/cpp/built_in/base_ops.h:95: return static_cast<bool>(v) && v.type_id() == PYTRA_TID_INT;
src/runtime/cpp/built_in/base_ops.h:105: return static_cast<bool>(v) && v.type_id() == PYTRA_TID_FLOAT;
src/runtime/cpp/built_in/base_ops.h:115: return static_cast<bool>(v) && v.type_id() == PYTRA_TID_STR;
src/runtime/cpp/built_in/base_ops.h:130: return static_cast<bool>(v) && v.type_id() == PYTRA_TID_LIST;
src/runtime/cpp/built_in/base_ops.h:143: return static_cast<bool>(v) && v.type_id() == PYTRA_TID_DICT;
src/runtime/cpp/built_in/base_ops.h:156: return static_cast<bool>(v) && v.type_id() == PYTRA_TID_SET;
src/runtime/cpp/built_in/base_ops.h:268: if (v.type_id() == PYTRA_TID_STR)
src/runtime/cpp/built_in/base_ops.h:270: if (v.type_id() == PYTRA_TID_INT)
src/runtime/cpp/built_in/base_ops.h:272: if (v.type_id() == PYTRA_TID_FLOAT)
src/runtime/cpp/built_in/base_ops.h:274: if (v.type_id() == PYTRA_TID_BOOL)
src/runtime/cpp/core/conversions.h:47: if (v.type_id() == PYTRA_TID_BOOL)
src/runtime/cpp/core/conversions.h:95: if (v.type_id() == PYTRA_TID_INT)
src/runtime/cpp/core/py_runtime.h:31: bool py_tid_is_subtype(int64 actual_type_id, int64 expected_type_id);
src/runtime/cpp/core/py_runtime.h:32: bool py_tid_issubclass(int64 actual_type_id, int64 expected_type_id);
src/runtime/cpp/core/py_runtime.h:33: bool py_tid_isinstance(const object& value, int64 expected_type_id);
src/runtime/cpp/core/py_runtime.h:34: int64 py_tid_register_class_type(int64 base_type_id);
src/runtime/cpp/core/py_scalar_types.h:22: static constexpr pytra_type_id PYTRA_TID_NONE = 0;
src/runtime/cpp/core/py_scalar_types.h:23: static constexpr pytra_type_id PYTRA_TID_BOOL = 1;
src/runtime/cpp/core/py_scalar_types.h:24: static constexpr pytra_type_id PYTRA_TID_INT = 2;
src/runtime/cpp/core/py_scalar_types.h:25: static constexpr pytra_type_id PYTRA_TID_FLOAT = 3;
src/runtime/cpp/core/py_scalar_types.h:26: static constexpr pytra_type_id PYTRA_TID_STR = 4;
src/runtime/cpp/core/py_scalar_types.h:27: static constexpr pytra_type_id PYTRA_TID_LIST = 5;
src/runtime/cpp/core/py_scalar_types.h:28: static constexpr pytra_type_id PYTRA_TID_DICT = 6;
src/runtime/cpp/core/py_scalar_types.h:29: static constexpr pytra_type_id PYTRA_TID_SET = 7;
src/runtime/cpp/core/py_scalar_types.h:30: static constexpr pytra_type_id PYTRA_TID_OBJECT = 8;
src/runtime/cpp/core/py_scalar_types.h:31: static constexpr pytra_type_id PYTRA_TID_USER_BASE = 1000;
src/runtime/cpp/core/py_types.h:72: static constexpr pytra_type_id value = PYTRA_TID_LIST;
src/runtime/cpp/core/py_types.h:77: static constexpr pytra_type_id value = PYTRA_TID_DICT;
src/runtime/cpp/core/py_types.h:82: static constexpr pytra_type_id value = PYTRA_TID_SET;
src/runtime/cpp/core/py_types.h:102: return make_object<list<T>>(PYTRA_TID_LIST);
src/runtime/cpp/core/py_types.h:107: return make_object<list<T>>(PYTRA_TID_LIST, ::std::move(values));
src/runtime/cpp/core/py_types.h:130: return make_object<dict<K, V>>(PYTRA_TID_DICT);
src/runtime/cpp/core/py_types.h:135: return make_object<dict<K, V>>(PYTRA_TID_DICT, ::std::move(values));
src/runtime/cpp/core/py_types.h:164: return make_object<set<T>>(PYTRA_TID_SET);
src/runtime/cpp/core/py_types.h:169: return make_object<set<T>>(PYTRA_TID_SET, ::std::move(values));
src/runtime/cpp/core/py_types.h:200: return make_object<list<T>>(PYTRA_TID_LIST, ::std::move(values));
src/runtime/cpp/core/py_types.h:208: return make_object<dict<K, V>>(PYTRA_TID_DICT, ::std::move(values));
src/runtime/cpp/core/py_types.h:216: return make_object<set<T>>(PYTRA_TID_SET, ::std::move(values));
src/runtime/cpp/core/py_types.h:239: cb = new ControlBlock{0, PYTRA_TID_INT, boxed.get(), &deleter_impl<PyBoxedValue<int64>>};
src/runtime/cpp/core/py_types.h:248: cb = new ControlBlock{0, PYTRA_TID_STR, boxed.get(), &deleter_impl<PyBoxedValue<str>>};
src/runtime/cpp/core/py_types.h:255: cb = new ControlBlock{0, PYTRA_TID_FLOAT, boxed.get(), &deleter_impl<PyBoxedValue<float64>>};
src/runtime/cpp/core/py_types.h:262: cb = new ControlBlock{0, PYTRA_TID_BOOL, boxed.get(), &deleter_impl<PyBoxedValue<bool>>};
src/runtime/cpp/core/py_types.h:269: cb = new ControlBlock{0, PYTRA_TID_STR, boxed.get(), &deleter_impl<PyBoxedValue<str>>};
```

### rt:type_id / cs (78)

```
src/runtime/cs/built_in/py_runtime.cs:133: public const long PYTRA_TID_NONE = 0;
src/runtime/cs/built_in/py_runtime.cs:134: public const long PYTRA_TID_BOOL = 1;
src/runtime/cs/built_in/py_runtime.cs:135: public const long PYTRA_TID_INT = 2;
src/runtime/cs/built_in/py_runtime.cs:136: public const long PYTRA_TID_FLOAT = 3;
src/runtime/cs/built_in/py_runtime.cs:137: public const long PYTRA_TID_STR = 4;
src/runtime/cs/built_in/py_runtime.cs:138: public const long PYTRA_TID_LIST = 5;
src/runtime/cs/built_in/py_runtime.cs:139: public const long PYTRA_TID_DICT = 6;
src/runtime/cs/built_in/py_runtime.cs:140: public const long PYTRA_TID_SET = 7;
src/runtime/cs/built_in/py_runtime.cs:141: public const long PYTRA_TID_OBJECT = 8;
src/runtime/cs/built_in/py_runtime.cs:142: public const long PYTRA_TID_BASE_EXCEPTION = 9;
src/runtime/cs/built_in/py_runtime.cs:143: public const long PYTRA_TID_EXCEPTION = 10;
src/runtime/cs/built_in/py_runtime.cs:144: public const long PYTRA_TID_RUNTIME_ERROR = 11;
src/runtime/cs/built_in/py_runtime.cs:145: public const long PYTRA_TID_VALUE_ERROR = 12;
src/runtime/cs/built_in/py_runtime.cs:146: public const long PYTRA_TID_TYPE_ERROR = 13;
src/runtime/cs/built_in/py_runtime.cs:147: public const long PYTRA_TID_INDEX_ERROR = 14;
src/runtime/cs/built_in/py_runtime.cs:148: public const long PYTRA_TID_KEY_ERROR = 15;
src/runtime/cs/built_in/py_runtime.cs:149: public const long PYTRA_TID_INT8 = 16;
src/runtime/cs/built_in/py_runtime.cs:150: public const long PYTRA_TID_INT16 = 17;
src/runtime/cs/built_in/py_runtime.cs:151: public const long PYTRA_TID_INT32 = 18;
src/runtime/cs/built_in/py_runtime.cs:152: public const long PYTRA_TID_INT64 = 19;
src/runtime/cs/built_in/py_runtime.cs:153: public const long PYTRA_TID_UINT8 = 20;
src/runtime/cs/built_in/py_runtime.cs:154: public const long PYTRA_TID_UINT16 = 21;
src/runtime/cs/built_in/py_runtime.cs:155: public const long PYTRA_TID_UINT32 = 22;
src/runtime/cs/built_in/py_runtime.cs:156: public const long PYTRA_TID_UINT64 = 23;
src/runtime/cs/built_in/py_runtime.cs:157: public const long PYTRA_TID_FLOAT32 = 24;
src/runtime/cs/built_in/py_runtime.cs:158: public const long PYTRA_TID_FLOAT64 = 25;
src/runtime/cs/built_in/py_runtime.cs:324: RegisterTypeNode(PYTRA_TID_NONE, -1);
src/runtime/cs/built_in/py_runtime.cs:325: RegisterTypeNode(PYTRA_TID_OBJECT, -1);
src/runtime/cs/built_in/py_runtime.cs:326: RegisterTypeNode(PYTRA_TID_INT, PYTRA_TID_OBJECT);
src/runtime/cs/built_in/py_runtime.cs:327: RegisterTypeNode(PYTRA_TID_BOOL, PYTRA_TID_INT);
src/runtime/cs/built_in/py_runtime.cs:328: RegisterTypeNode(PYTRA_TID_INT8, PYTRA_TID_INT);
src/runtime/cs/built_in/py_runtime.cs:329: RegisterTypeNode(PYTRA_TID_INT16, PYTRA_TID_INT);
src/runtime/cs/built_in/py_runtime.cs:330: RegisterTypeNode(PYTRA_TID_INT32, PYTRA_TID_INT);
src/runtime/cs/built_in/py_runtime.cs:331: RegisterTypeNode(PYTRA_TID_INT64, PYTRA_TID_INT);
src/runtime/cs/built_in/py_runtime.cs:332: RegisterTypeNode(PYTRA_TID_UINT8, PYTRA_TID_INT);
src/runtime/cs/built_in/py_runtime.cs:333: RegisterTypeNode(PYTRA_TID_UINT16, PYTRA_TID_INT);
src/runtime/cs/built_in/py_runtime.cs:334: RegisterTypeNode(PYTRA_TID_UINT32, PYTRA_TID_INT);
src/runtime/cs/built_in/py_runtime.cs:335: RegisterTypeNode(PYTRA_TID_UINT64, PYTRA_TID_INT);
src/runtime/cs/built_in/py_runtime.cs:336: RegisterTypeNode(PYTRA_TID_FLOAT, PYTRA_TID_OBJECT);
src/runtime/cs/built_in/py_runtime.cs:337: RegisterTypeNode(PYTRA_TID_FLOAT32, PYTRA_TID_FLOAT);
src/runtime/cs/built_in/py_runtime.cs:338: RegisterTypeNode(PYTRA_TID_FLOAT64, PYTRA_TID_FLOAT);
src/runtime/cs/built_in/py_runtime.cs:339: RegisterTypeNode(PYTRA_TID_STR, PYTRA_TID_OBJECT);
src/runtime/cs/built_in/py_runtime.cs:340: RegisterTypeNode(PYTRA_TID_LIST, PYTRA_TID_OBJECT);
src/runtime/cs/built_in/py_runtime.cs:341: RegisterTypeNode(PYTRA_TID_DICT, PYTRA_TID_OBJECT);
src/runtime/cs/built_in/py_runtime.cs:342: RegisterTypeNode(PYTRA_TID_SET, PYTRA_TID_OBJECT);
src/runtime/cs/built_in/py_runtime.cs:343: RegisterTypeNode(PYTRA_TID_BASE_EXCEPTION, PYTRA_TID_OBJECT);
src/runtime/cs/built_in/py_runtime.cs:344: RegisterTypeNode(PYTRA_TID_EXCEPTION, PYTRA_TID_BASE_EXCEPTION);
src/runtime/cs/built_in/py_runtime.cs:345: RegisterTypeNode(PYTRA_TID_RUNTIME_ERROR, PYTRA_TID_EXCEPTION);
src/runtime/cs/built_in/py_runtime.cs:346: RegisterTypeNode(PYTRA_TID_VALUE_ERROR, PYTRA_TID_EXCEPTION);
src/runtime/cs/built_in/py_runtime.cs:347: RegisterTypeNode(PYTRA_TID_TYPE_ERROR, PYTRA_TID_EXCEPTION);
src/runtime/cs/built_in/py_runtime.cs:348: RegisterTypeNode(PYTRA_TID_INDEX_ERROR, PYTRA_TID_EXCEPTION);
src/runtime/cs/built_in/py_runtime.cs:349: RegisterTypeNode(PYTRA_TID_KEY_ERROR, PYTRA_TID_EXCEPTION);
src/runtime/cs/built_in/py_runtime.cs:358: baseTid = PYTRA_TID_OBJECT;
src/runtime/cs/built_in/py_runtime.cs:375: public static long py_register_class_type(long baseTypeId = PYTRA_TID_OBJECT)
src/runtime/cs/built_in/py_runtime.cs:409: return PYTRA_TID_NONE;
src/runtime/cs/built_in/py_runtime.cs:413: return PYTRA_TID_BOOL;
src/runtime/cs/built_in/py_runtime.cs:417: return PYTRA_TID_INT8;
src/runtime/cs/built_in/py_runtime.cs:421: return PYTRA_TID_INT16;
src/runtime/cs/built_in/py_runtime.cs:425: return PYTRA_TID_INT32;
src/runtime/cs/built_in/py_runtime.cs:429: return PYTRA_TID_INT64;
src/runtime/cs/built_in/py_runtime.cs:433: return PYTRA_TID_UINT8;
src/runtime/cs/built_in/py_runtime.cs:437: return PYTRA_TID_UINT16;
src/runtime/cs/built_in/py_runtime.cs:441: return PYTRA_TID_UINT32;
src/runtime/cs/built_in/py_runtime.cs:445: return PYTRA_TID_UINT64;
src/runtime/cs/built_in/py_runtime.cs:449: return PYTRA_TID_FLOAT32;
src/runtime/cs/built_in/py_runtime.cs:453: return PYTRA_TID_FLOAT64;
src/runtime/cs/built_in/py_runtime.cs:457: return PYTRA_TID_STR;
src/runtime/cs/built_in/py_runtime.cs:461: return PYTRA_TID_KEY_ERROR;
src/runtime/cs/built_in/py_runtime.cs:465: return PYTRA_TID_INDEX_ERROR;
src/runtime/cs/built_in/py_runtime.cs:469: return PYTRA_TID_VALUE_ERROR;
src/runtime/cs/built_in/py_runtime.cs:473: return PYTRA_TID_TYPE_ERROR;
src/runtime/cs/built_in/py_runtime.cs:477: return PYTRA_TID_EXCEPTION;
src/runtime/cs/built_in/py_runtime.cs:481: return PYTRA_TID_DICT;
src/runtime/cs/built_in/py_runtime.cs:485: return PYTRA_TID_SET;
src/runtime/cs/built_in/py_runtime.cs:489: return PYTRA_TID_LIST;
src/runtime/cs/built_in/py_runtime.cs:493: FieldInfo field = t.GetField("PYTRA_TYPE_ID", BindingFlags.Public | BindingFlags.Static);
src/runtime/cs/built_in/py_runtime.cs:506: return PYTRA_TID_OBJECT;
src/runtime/cs/built_in/py_runtime.cs:555: public static bool pytra_isinstance(long actualTypeId, long expectedTypeId)
```

### rt:type_id / go (2)

```
src/runtime/go/built_in/py_runtime.go:248: func pytra_isinstance(actualTypeId int64, tid int64) bool {
src/runtime/go/built_in/py_runtime.go:302: func py_runtime_object_type_id(value any) int64 {
```

### rt:type_id / js (2)

```
src/runtime/js/built_in/py_runtime.js:19: const PYTRA_TYPE_ID = Symbol.for("pytra.type_id");
src/runtime/js/built_in/py_runtime.js:279: const tagged = value[PYTRA_TYPE_ID];
```

### rt:type_id / lua (2)

```
src/runtime/lua/built_in/py_runtime.lua:934: function __pytra_isinstance(obj, class_tbl)
src/runtime/lua/built_in/py_runtime.lua:972: pytra_isinstance = __pytra_isinstance
```

### rt:type_id / rs (62)

```
src/runtime/rs/built_in/py_runtime.rs:1201: pub const PYTRA_TID_NONE: i64 = 0;
src/runtime/rs/built_in/py_runtime.rs:1202: pub const PYTRA_TID_BOOL: i64 = 1;
src/runtime/rs/built_in/py_runtime.rs:1203: pub const PYTRA_TID_INT: i64 = 2;
src/runtime/rs/built_in/py_runtime.rs:1204: pub const PYTRA_TID_FLOAT: i64 = 3;
src/runtime/rs/built_in/py_runtime.rs:1205: pub const PYTRA_TID_STR: i64 = 4;
src/runtime/rs/built_in/py_runtime.rs:1206: pub const PYTRA_TID_LIST: i64 = 5;
src/runtime/rs/built_in/py_runtime.rs:1207: pub const PYTRA_TID_DICT: i64 = 6;
src/runtime/rs/built_in/py_runtime.rs:1208: pub const PYTRA_TID_SET: i64 = 7;
src/runtime/rs/built_in/py_runtime.rs:1209: pub const PYTRA_TID_OBJECT: i64 = 8;
src/runtime/rs/built_in/py_runtime.rs:1225: PYTRA_TID_NONE,
src/runtime/rs/built_in/py_runtime.rs:1227: order: PYTRA_TID_NONE,
src/runtime/rs/built_in/py_runtime.rs:1228: min: PYTRA_TID_NONE,
src/runtime/rs/built_in/py_runtime.rs:1229: max: PYTRA_TID_NONE,
src/runtime/rs/built_in/py_runtime.rs:1233: PYTRA_TID_BOOL,
src/runtime/rs/built_in/py_runtime.rs:1235: order: PYTRA_TID_BOOL,
src/runtime/rs/built_in/py_runtime.rs:1236: min: PYTRA_TID_BOOL,
src/runtime/rs/built_in/py_runtime.rs:1237: max: PYTRA_TID_BOOL,
src/runtime/rs/built_in/py_runtime.rs:1241: PYTRA_TID_INT,
src/runtime/rs/built_in/py_runtime.rs:1243: order: PYTRA_TID_INT,
src/runtime/rs/built_in/py_runtime.rs:1244: min: PYTRA_TID_INT,
src/runtime/rs/built_in/py_runtime.rs:1245: max: PYTRA_TID_INT,
src/runtime/rs/built_in/py_runtime.rs:1249: PYTRA_TID_FLOAT,
src/runtime/rs/built_in/py_runtime.rs:1251: order: PYTRA_TID_FLOAT,
src/runtime/rs/built_in/py_runtime.rs:1252: min: PYTRA_TID_FLOAT,
src/runtime/rs/built_in/py_runtime.rs:1253: max: PYTRA_TID_FLOAT,
src/runtime/rs/built_in/py_runtime.rs:1257: PYTRA_TID_STR,
src/runtime/rs/built_in/py_runtime.rs:1259: order: PYTRA_TID_STR,
src/runtime/rs/built_in/py_runtime.rs:1260: min: PYTRA_TID_STR,
src/runtime/rs/built_in/py_runtime.rs:1261: max: PYTRA_TID_STR,
src/runtime/rs/built_in/py_runtime.rs:1265: PYTRA_TID_LIST,
src/runtime/rs/built_in/py_runtime.rs:1267: order: PYTRA_TID_LIST,
src/runtime/rs/built_in/py_runtime.rs:1268: min: PYTRA_TID_LIST,
src/runtime/rs/built_in/py_runtime.rs:1269: max: PYTRA_TID_LIST,
src/runtime/rs/built_in/py_runtime.rs:1273: PYTRA_TID_DICT,
src/runtime/rs/built_in/py_runtime.rs:1275: order: PYTRA_TID_DICT,
src/runtime/rs/built_in/py_runtime.rs:1276: min: PYTRA_TID_DICT,
src/runtime/rs/built_in/py_runtime.rs:1277: max: PYTRA_TID_DICT,
src/runtime/rs/built_in/py_runtime.rs:1281: PYTRA_TID_SET,
src/runtime/rs/built_in/py_runtime.rs:1283: order: PYTRA_TID_SET,
src/runtime/rs/built_in/py_runtime.rs:1284: min: PYTRA_TID_SET,
src/runtime/rs/built_in/py_runtime.rs:1285: max: PYTRA_TID_SET,
src/runtime/rs/built_in/py_runtime.rs:1289: PYTRA_TID_OBJECT,
src/runtime/rs/built_in/py_runtime.rs:1291: order: PYTRA_TID_OBJECT,
src/runtime/rs/built_in/py_runtime.rs:1292: min: PYTRA_TID_OBJECT,
src/runtime/rs/built_in/py_runtime.rs:1293: max: PYTRA_TID_OBJECT,
src/runtime/rs/built_in/py_runtime.rs:1328: PYTRA_TID_BOOL
src/runtime/rs/built_in/py_runtime.rs:1333: PYTRA_TID_INT
src/runtime/rs/built_in/py_runtime.rs:1338: PYTRA_TID_FLOAT
src/runtime/rs/built_in/py_runtime.rs:1343: PYTRA_TID_STR
src/runtime/rs/built_in/py_runtime.rs:1348: PYTRA_TID_LIST
src/runtime/rs/built_in/py_runtime.rs:1353: PYTRA_TID_DICT
src/runtime/rs/built_in/py_runtime.rs:1358: PYTRA_TID_SET
src/runtime/rs/built_in/py_runtime.rs:1365: None => PYTRA_TID_NONE,
src/runtime/rs/built_in/py_runtime.rs:1372: PyAny::Int(_) => PYTRA_TID_INT,
src/runtime/rs/built_in/py_runtime.rs:1373: PyAny::Float(_) => PYTRA_TID_FLOAT,
src/runtime/rs/built_in/py_runtime.rs:1374: PyAny::Bool(_) => PYTRA_TID_BOOL,
src/runtime/rs/built_in/py_runtime.rs:1375: PyAny::Str(_) => PYTRA_TID_STR,
src/runtime/rs/built_in/py_runtime.rs:1376: PyAny::List(_) => PYTRA_TID_LIST,
src/runtime/rs/built_in/py_runtime.rs:1377: PyAny::Dict(_) => PYTRA_TID_DICT,
src/runtime/rs/built_in/py_runtime.rs:1378: PyAny::Set(_) => PYTRA_TID_SET,
src/runtime/rs/built_in/py_runtime.rs:1379: PyAny::None => PYTRA_TID_NONE,
src/runtime/rs/built_in/py_runtime.rs:1420: PYTRA_TID_NONE
```

### rt:type_id / ruby (1)

```
src/runtime/ruby/built_in/py_runtime.rb:442: def __pytra_isinstance(obj, type_cls)
```

### rt:type_id / ts (3)

```
src/runtime/ts/built_in/py_runtime.ts:30: const PYTRA_TYPE_ID = Symbol.for("pytra.type_id");
src/runtime/ts/built_in/py_runtime.ts:276: [PYTRA_TYPE_ID]?: number;
src/runtime/ts/built_in/py_runtime.ts:302: const raw = tagged[PYTRA_TYPE_ID];
```

### skip_pure_python / go (2)

```
src/runtime/go/mapping.json:0: skip_modules contains "pytra.std.pathlib" but pytra.std.pathlib is pure Python (no @extern)
src/runtime/go/mapping.json:0: skip_modules contains "pytra.std.random" but pytra.std.random is pure Python (no @extern)
```

### skip_pure_python / nim (1)

```
src/runtime/nim/mapping.json:0: skip_modules contains "pytra.std.random" but pytra.std.random is pure Python (no @extern)
```

### skip_pure_python / php (1)

```
src/runtime/php/mapping.json:0: skip_modules contains "pytra.std.random" but pytra.std.random is pure Python (no @extern)
```

### skip_pure_python / ruby (1)

```
src/runtime/ruby/mapping.json:0: skip_modules contains "pytra.std.random" but pytra.std.random is pure Python (no @extern)
```

### type_id / ts (1)

```
src/toolchain2/emit/ts/emitter.py:882: if fn_id == "pytra_isinstance":
```
