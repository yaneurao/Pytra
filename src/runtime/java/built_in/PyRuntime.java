// Java ネイティブ変換向け Python 互換ランタイム補助。
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.PrintStream;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.StringJoiner;

final class PyRuntime {
    private static final long __PYTRA_NONE_TID = 0L;
    private static final long __PYTRA_BOOL_TID = 1L;
    private static final long __PYTRA_INT_TID = 2L;
    private static final long __PYTRA_FLOAT_TID = 3L;
    private static final long __PYTRA_STR_TID = 4L;
    private static final long __PYTRA_LIST_TID = 5L;
    private static final long __PYTRA_DICT_TID = 6L;
    private static final long __PYTRA_SET_TID = 7L;
    private static final long __PYTRA_OBJECT_TID = 8L;

    static ArrayList<String> __pytra_argv = new ArrayList<>();
    static ArrayList<String> __pytra_path = new ArrayList<>();
    private static List<Long> __pytra_registered_type_ranges = java.util.Collections.emptyList();

    private PyRuntime() {
    }

    static long pyRuntimeValueTypeId(Object value) {
        if (value == null) {
            return __PYTRA_NONE_TID;
        }
        if (value instanceof Boolean) {
            return __PYTRA_BOOL_TID;
        }
        if (value instanceof Integer || value instanceof Long || value instanceof Short || value instanceof Byte) {
            return __PYTRA_INT_TID;
        }
        if (value instanceof Float || value instanceof Double) {
            return __PYTRA_FLOAT_TID;
        }
        if (value instanceof String) {
            return __PYTRA_STR_TID;
        }
        if (value instanceof Map<?, ?>) {
            return __PYTRA_DICT_TID;
        }
        if (value instanceof java.util.Set<?>) {
            return __PYTRA_SET_TID;
        }
        if (value instanceof List<?> || value instanceof byte[]) {
            return __PYTRA_LIST_TID;
        }
        Long userTid = __pytra_user_type_id(value);
        if (userTid != null) {
            return userTid.longValue();
        }
        return __PYTRA_OBJECT_TID;
    }

    static boolean pytraIsinstance(long actualTypeId, long tid) {
        if (actualTypeId == tid) {
            return true;
        }
        int base = (int) (tid * 2L);
        if (base < 0 || base + 1 >= __pytra_registered_type_ranges.size()) {
            return false;
        }
        long entry = __pytra_registered_type_ranges.get(base);
        long exit = __pytra_registered_type_ranges.get(base + 1);
        return actualTypeId >= entry && actualTypeId <= exit;
    }

    static void __pytra_register_type_ranges(List<Long> ranges) {
        if (ranges == null) {
            __pytra_registered_type_ranges = java.util.Collections.emptyList();
            return;
        }
        __pytra_registered_type_ranges = ranges;
    }

    private static Long __pytra_user_type_id(Object value) {
        try {
            java.lang.reflect.Method method = value.getClass().getMethod("__pytra_type_id");
            Object out = method.invoke(value);
            return Long.valueOf(pyToLong(out));
        } catch (ReflectiveOperationException _err) {
            return null;
        }
    }

    private static String pyRepr(Object v) {
        if (v instanceof String) {
            String s = (String) v;
            return "'" + s.replace("\\", "\\\\").replace("'", "\\'") + "'";
        }
        return pyToString(v);
    }

    static String pyToString(Object v) {
        if (v == null) {
            return "None";
        }
        if (v instanceof Throwable) {
            Throwable err = (Throwable) v;
            String message = err.getMessage();
            if (message != null && !message.isEmpty()) {
                return message;
            }
            return err.getClass().getSimpleName();
        }
        if (v instanceof Boolean) {
            Boolean b = (Boolean) v;
            return b ? "True" : "False";
        }
        if (v instanceof Double || v instanceof Float) {
            return String.valueOf(v).replace("E", "e");
        }
        if (v instanceof List<?>) {
            List<?> list = (List<?>) v;
            StringJoiner sj = new StringJoiner(", ", "[", "]");
            for (Object it : list) {
                sj.add(pyRepr(it));
            }
            return sj.toString();
        }
        if (v instanceof Map<?, ?>) {
            Map<?, ?> map = (Map<?, ?>) v;
            StringJoiner sj = new StringJoiner(", ", "{", "}");
            for (Map.Entry<?, ?> e : map.entrySet()) {
                sj.add(pyRepr(e.getKey()) + ": " + pyRepr(e.getValue()));
            }
            return sj.toString();
        }
        return String.valueOf(v);
    }

    static String pyTupleToString(List<?> value) {
        StringJoiner sj = new StringJoiner(", ", "(", ")");
        for (Object item : value) {
            sj.add(pyRepr(item));
        }
        String text = sj.toString();
        if (value.size() == 1) {
            return text.substring(0, text.length() - 1) + ",)";
        }
        return text;
    }

    static void pyPrint(Object... values) {
        StringJoiner sj = new StringJoiner(" ");
        for (Object value : values) {
            sj.add(pyToString(value));
        }
        System.out.println(sj);
    }

    static boolean pyBool(Object v) {
        if (v == null) {
            return false;
        }
        if (v instanceof Boolean) {
            Boolean b = (Boolean) v;
            return b;
        }
        if (v instanceof Integer) {
            Integer i = (Integer) v;
            return i != 0;
        }
        if (v instanceof Long) {
            Long i = (Long) v;
            return i != 0L;
        }
        if (v instanceof Double) {
            Double d = (Double) v;
            return d != 0.0;
        }
        if (v instanceof String) {
            String s = (String) v;
            return !s.isEmpty();
        }
        if (v instanceof List<?>) {
            List<?> list = (List<?>) v;
            return !list.isEmpty();
        }
        if (v instanceof Map<?, ?>) {
            Map<?, ?> map = (Map<?, ?>) v;
            return !map.isEmpty();
        }
        if (v instanceof java.util.Collection<?>) {
            java.util.Collection<?> collection = (java.util.Collection<?>) v;
            return !collection.isEmpty();
        }
        return true;
    }

    static int pyLen(Object v) {
        if (v instanceof String) {
            String s = (String) v;
            return s.length();
        }
        if (v instanceof List<?>) {
            List<?> list = (List<?>) v;
            return list.size();
        }
        if (v instanceof byte[]) {
            byte[] bytes = (byte[]) v;
            return bytes.length;
        }
        if (v instanceof Map<?, ?>) {
            Map<?, ?> map = (Map<?, ?>) v;
            return map.size();
        }
        if (v instanceof java.util.Collection<?>) {
            java.util.Collection<?> collection = (java.util.Collection<?>) v;
            return collection.size();
        }
        throw new RuntimeException("len() unsupported type");
    }

    static List<Object> pyRange(int start, int stop, int step) {
        if (step == 0) {
            throw new RuntimeException("range() step must not be zero");
        }
        List<Object> out = new ArrayList<>();
        if (step > 0) {
            for (int i = start; i < stop; i += step) {
                out.add(i);
            }
        } else {
            for (int i = start; i > stop; i += step) {
                out.add(i);
            }
        }
        return out;
    }

    static ArrayList<Object> pyReversed(Object value) {
        ArrayList<Object> out = new ArrayList<>();
        if (value instanceof List<?>) {
            List<?> items = (List<?>) value;
            for (int i = items.size() - 1; i >= 0; i--) {
                out.add(items.get(i));
            }
            return out;
        }
        throw new RuntimeException("reversed() unsupported type");
    }

    static ArrayList<Object> pyEnumerate(Object value) {
        return pyEnumerate(value, 0L);
    }

    static ArrayList<Object> pyEnumerate(Object value, Object startValue) {
        ArrayList<Object> out = new ArrayList<>();
        List<Object> items = pyIter(value);
        long i = pyToLong(startValue);
        int index = 0;
        while (index < items.size()) {
            ArrayList<Object> pair = new ArrayList<>(2);
            pair.add(i);
            pair.add(items.get(index));
            out.add(pair);
            i += 1L;
            index += 1;
        }
        return out;
    }

    static String pyTypeName(Object value) {
        if (value == null) {
            return "NoneType";
        }
        return value.getClass().getSimpleName();
    }

    static long pyListIndex(Object listObj, Object needle) {
        List<Object> items = pyIter(listObj);
        int index = 0;
        while (index < items.size()) {
            if (pyEq(items.get(index), needle)) {
                return index;
            }
            index += 1;
        }
        throw new RuntimeException("list.index missing value");
    }

    static ArrayList<Object> pyZip(Object lhs, Object rhs) {
        ArrayList<Object> out = new ArrayList<>();
        List<Object> leftItems = pyIter(lhs);
        List<Object> rightItems = pyIter(rhs);
        int n = Math.min(leftItems.size(), rightItems.size());
        int i = 0;
        while (i < n) {
            ArrayList<Object> pair = new ArrayList<>(2);
            pair.add(leftItems.get(i));
            pair.add(rightItems.get(i));
            out.add(pair);
            i += 1;
        }
        return out;
    }

    static double pySum(Object iterable) {
        List<Object> items = pyIter(iterable);
        double total = 0.0;
        for (Object item : items) {
            total += pyToFloat(item);
        }
        return total;
    }

    static String pyFormat(Object value, String spec) {
        if (spec == null || spec.isEmpty()) {
            return pyToString(value);
        }
        if (spec.endsWith("%")) {
            String javaSpec = "%" + _pyFormatFlags(spec.substring(0, spec.length() - 1)) + "f";
            return String.format(java.util.Locale.US, javaSpec, pyToFloat(value) * 100.0) + "%";
        }
        char kind = spec.charAt(spec.length() - 1);
        String flags = _pyFormatFlags(spec.substring(0, spec.length() - 1));
        String javaSpec = "%" + flags + kind;
        if (kind == 'd' || kind == 'x' || kind == 'X') {
            return String.format(java.util.Locale.US, javaSpec, pyToLong(value));
        }
        if (kind == 'f') {
            return String.format(java.util.Locale.US, javaSpec, pyToFloat(value));
        }
        if (kind == 's') {
            return String.format(java.util.Locale.US, javaSpec, pyToString(value));
        }
        return pyToString(value);
    }

    private static String _pyFormatFlags(String spec) {
        if (spec.indexOf('<') >= 0) {
            return spec.replace("<", "-");
        }
        return spec;
    }

    static double pyToFloat(Object v) {
        if (v instanceof Integer) {
            Integer i = (Integer) v;
            return i;
        }
        if (v instanceof Long) {
            Long i = (Long) v;
            return i;
        }
        if (v instanceof Double) {
            Double d = (Double) v;
            return d;
        }
        if (v instanceof Boolean) {
            Boolean b = (Boolean) v;
            return b ? 1.0 : 0.0;
        }
        throw new RuntimeException("cannot convert to float");
    }

    static int pyToInt(Object v) {
        if (v instanceof Integer) {
            Integer i = (Integer) v;
            return i;
        }
        if (v instanceof Long) {
            Long i = (Long) v;
            return (int) i.longValue();
        }
        if (v instanceof Double) {
            Double d = (Double) v;
            // Python の int() は小数部切り捨て（0方向）なので Java のキャストで合わせる。
            return (int) d.doubleValue();
        }
        if (v instanceof Boolean) {
            Boolean b = (Boolean) v;
            return b ? 1 : 0;
        }
        throw new RuntimeException("cannot convert to int");
    }

    static long pyToLong(Object v) {
        if (v instanceof Integer) {
            Integer i = (Integer) v;
            return i.longValue();
        }
        if (v instanceof Long) {
            Long i = (Long) v;
            return i.longValue();
        }
        if (v instanceof Double) {
            Double d = (Double) v;
            return (long) d.doubleValue();
        }
        if (v instanceof Boolean) {
            Boolean b = (Boolean) v;
            return b ? 1L : 0L;
        }
        throw new RuntimeException("cannot convert to long");
    }

    static Object pyAdd(Object a, Object b) {
        if (a instanceof String || b instanceof String) {
            return pyToString(a) + pyToString(b);
        }
        if ((a instanceof Integer || a instanceof Long || a instanceof Boolean)
                && (b instanceof Integer || b instanceof Long || b instanceof Boolean)) {
            return pyToLong(a) + pyToLong(b);
        }
        return pyToFloat(a) + pyToFloat(b);
    }

    static Object pySub(Object a, Object b) {
        if ((a instanceof Integer || a instanceof Long || a instanceof Boolean)
                && (b instanceof Integer || b instanceof Long || b instanceof Boolean)) {
            return pyToLong(a) - pyToLong(b);
        }
        return pyToFloat(a) - pyToFloat(b);
    }

    static Object pyMul(Object a, Object b) {
        if ((a instanceof Integer || a instanceof Long || a instanceof Boolean)
                && (b instanceof Integer || b instanceof Long || b instanceof Boolean)) {
            return pyToLong(a) * pyToLong(b);
        }
        return pyToFloat(a) * pyToFloat(b);
    }

    static Object pyDiv(Object a, Object b) {
        return pyToFloat(a) / pyToFloat(b);
    }

    static Object pyFloorDiv(Object a, Object b) {
        if ((a instanceof Integer || a instanceof Long || a instanceof Boolean)
                && (b instanceof Integer || b instanceof Long || b instanceof Boolean)) {
            long ai = pyToLong(a);
            long bi = pyToLong(b);
            long q = ai / bi;
            long r = ai % bi;
            if (r != 0 && ((r > 0) != (bi > 0))) {
                q -= 1;
            }
            return q;
        }
        return (int) Math.floor(pyToFloat(a) / pyToFloat(b));
    }

    static Object pyMod(Object a, Object b) {
        if ((a instanceof Integer || a instanceof Long || a instanceof Boolean)
                && (b instanceof Integer || b instanceof Long || b instanceof Boolean)) {
            long ai = pyToLong(a);
            long bi = pyToLong(b);
            long r = ai % bi;
            if (r != 0 && ((r > 0) != (bi > 0))) {
                r += bi;
            }
            return r;
        }
        throw new RuntimeException("mod unsupported type");
    }

    static Object pyMin(Object... values) {
        if (values.length == 0) {
            throw new RuntimeException("min() arg is empty");
        }
        Object out = values[0];
        for (int i = 1; i < values.length; i++) {
            Object a = out;
            Object b = values[i];
            if (a instanceof Long || b instanceof Long) {
                if (pyToLong(b) < pyToLong(a)) {
                    out = b;
                }
                continue;
            }
            if (a instanceof Integer && b instanceof Integer) {
                if (pyToInt(b) < pyToInt(a)) {
                    out = b;
                }
            } else if (pyToFloat(b) < pyToFloat(a)) {
                out = b;
            }
        }
        return out;
    }

    static Object __pytra_py_min(Object a, Object b) {
        return pyMin(a, b);
    }

    static long __pytra_py_min(long a, long b) {
        return pyToLong(pyMin(a, b));
    }

    static double __pytra_py_min(double a, double b) {
        return pyToFloat(pyMin(a, b));
    }

    static double __pytra_py_min(long a, double b) {
        return pyToFloat(pyMin(a, b));
    }

    static double __pytra_py_min(double a, long b) {
        return pyToFloat(pyMin(a, b));
    }

    static Object pyMax(Object... values) {
        if (values.length == 0) {
            throw new RuntimeException("max() arg is empty");
        }
        Object out = values[0];
        for (int i = 1; i < values.length; i++) {
            Object a = out;
            Object b = values[i];
            if (a instanceof Long || b instanceof Long) {
                if (pyToLong(b) > pyToLong(a)) {
                    out = b;
                }
                continue;
            }
            if (a instanceof Integer && b instanceof Integer) {
                if (pyToInt(b) > pyToInt(a)) {
                    out = b;
                }
            } else if (pyToFloat(b) > pyToFloat(a)) {
                out = b;
            }
        }
        return out;
    }

    static Object __pytra_py_max(Object a, Object b) {
        return pyMax(a, b);
    }

    static long __pytra_py_max(long a, long b) {
        return pyToLong(pyMax(a, b));
    }

    static double __pytra_py_max(double a, double b) {
        return pyToFloat(pyMax(a, b));
    }

    static double __pytra_py_max(long a, double b) {
        return pyToFloat(pyMax(a, b));
    }

    static double __pytra_py_max(double a, long b) {
        return pyToFloat(pyMax(a, b));
    }

    static Object pyLShift(Object a, Object b) {
        return pyToInt(a) << pyToInt(b);
    }

    static Object pyRShift(Object a, Object b) {
        return pyToInt(a) >> pyToInt(b);
    }

    static Object pyBitAnd(Object a, Object b) {
        return pyToInt(a) & pyToInt(b);
    }

    static Object pyBitOr(Object a, Object b) {
        return pyToInt(a) | pyToInt(b);
    }

    static Object pyBitXor(Object a, Object b) {
        return pyToInt(a) ^ pyToInt(b);
    }

    static Object pyNeg(Object a) {
        if (a instanceof Integer || a instanceof Long || a instanceof Boolean) {
            return -pyToLong(a);
        }
        return -pyToFloat(a);
    }

    static boolean pyEq(Object a, Object b) {
        return pyToString(a).equals(pyToString(b));
    }

    static boolean pyNe(Object a, Object b) {
        return !pyEq(a, b);
    }

    static boolean pyLt(Object a, Object b) {
        return pyToFloat(a) < pyToFloat(b);
    }

    static boolean pyLe(Object a, Object b) {
        return pyToFloat(a) <= pyToFloat(b);
    }

    static boolean pyGt(Object a, Object b) {
        return pyToFloat(a) > pyToFloat(b);
    }

    static boolean pyGe(Object a, Object b) {
        return pyToFloat(a) >= pyToFloat(b);
    }

    static boolean pyIn(Object item, Object container) {
        if (container instanceof String) {
            String s = (String) container;
            return s.contains(pyToString(item));
        }
        if (container instanceof List<?>) {
            List<?> list = (List<?>) container;
            for (Object v : list) {
                if (pyEq(v, item)) {
                    return true;
                }
            }
            return false;
        }
        if (container instanceof Map<?, ?>) {
            Map<?, ?> map = (Map<?, ?>) container;
            return map.containsKey(item);
        }
        if (container instanceof java.util.Collection<?>) {
            java.util.Collection<?> collection = (java.util.Collection<?>) container;
            for (Object value : collection) {
                if (pyEq(value, item)) {
                    return true;
                }
            }
            return false;
        }
        return false;
    }

    static List<Object> pyIter(Object value) {
        if (value instanceof List<?>) {
            List<?> list = (List<?>) value;
            return new ArrayList<>((List<Object>) list);
        }
        if (value instanceof byte[]) {
            byte[] arr = (byte[]) value;
            List<Object> out = new ArrayList<>();
            for (byte b : arr) {
                out.add((int) (b & 0xff));
            }
            return out;
        }
        if (value instanceof String) {
            String s = (String) value;
            List<Object> out = new ArrayList<>();
            for (int i = 0; i < s.length(); i++) {
                out.add(String.valueOf(s.charAt(i)));
            }
            return out;
        }
        if (value instanceof Map<?, ?>) {
            Map<?, ?> map = (Map<?, ?>) value;
            return new ArrayList<>(((Map<Object, Object>) map).keySet());
        }
        if (value instanceof java.util.Collection<?>) {
            java.util.Collection<?> collection = (java.util.Collection<?>) value;
            return new ArrayList<>(collection);
        }
        throw new RuntimeException("iter unsupported");
    }

    static Object pyTernary(boolean cond, Object a, Object b) {
        return cond ? a : b;
    }

    static Object pyListFromIter(Object value) {
        return pyIter(value);
    }

    static Object pySlice(Object value, Object start, Object end) {
        if (value instanceof String) {
            String s = (String) value;
            int n = s.length();
            int st = (start == null) ? 0 : pyToInt(start);
            int ed = (end == null) ? n : pyToInt(end);
            if (st < 0)
                st += n;
            if (ed < 0)
                ed += n;
            if (st < 0)
                st = 0;
            if (ed < 0)
                ed = 0;
            if (st > n)
                st = n;
            if (ed > n)
                ed = n;
            if (st > ed)
                st = ed;
            return s.substring(st, ed);
        }
        if (value instanceof List<?>) {
            List<?> list = (List<?>) value;
            int n = list.size();
            int st = (start == null) ? 0 : pyToInt(start);
            int ed = (end == null) ? n : pyToInt(end);
            if (st < 0)
                st += n;
            if (ed < 0)
                ed += n;
            if (st < 0)
                st = 0;
            if (ed < 0)
                ed = 0;
            if (st > n)
                st = n;
            if (ed > n)
                ed = n;
            if (st > ed)
                st = ed;
            return new ArrayList<>(list.subList(st, ed));
        }
        throw new RuntimeException("slice unsupported");
    }

    static Object pyGet(Object value, Object key) {
        if (value instanceof List<?>) {
            List<?> list = (List<?>) value;
            int i = pyToInt(key);
            if (i < 0)
                i += list.size();
            return list.get(i);
        }
        if (value instanceof Map<?, ?>) {
            Map<?, ?> map = (Map<?, ?>) value;
            return ((Map<Object, Object>) map).get(key);
        }
        if (value instanceof String) {
            String s = (String) value;
            int i = pyToInt(key);
            if (i < 0)
                i += s.length();
            return String.valueOf(s.charAt(i));
        }
        throw new RuntimeException("subscript unsupported");
    }

    static void pySet(Object value, Object key, Object newValue) {
        if (value instanceof List<?>) {
            List<?> list = (List<?>) value;
            int i = pyToInt(key);
            List<Object> l = (List<Object>) list;
            if (i < 0)
                i += l.size();
            l.set(i, newValue);
            return;
        }
        if (value instanceof Map<?, ?>) {
            Map<?, ?> map = (Map<?, ?>) value;
            ((Map<Object, Object>) map).put(key, newValue);
            return;
        }
        throw new RuntimeException("setitem unsupported");
    }

    static Object pyPop(Object value, Object idx) {
        if (value instanceof List<?>) {
            List<?> list = (List<?>) value;
            List<Object> l = (List<Object>) list;
            int i = (idx == null) ? (l.size() - 1) : pyToInt(idx);
            if (i < 0)
                i += l.size();
            Object out = l.get(i);
            l.remove(i);
            return out;
        }
        throw new RuntimeException("pop unsupported");
    }

    static Object pyPop(Object value) {
        return pyPop(value, null);
    }

    static Object pyOrd(Object v) {
        String s = pyToString(v);
        return (int) s.charAt(0);
    }

    static Object pyChr(Object v) {
        return Character.toString((char) pyToInt(v));
    }

    static Object pyBytearray(Object size) {
        int n = (size == null) ? 0 : pyToInt(size);
        List<Object> out = new ArrayList<>();
        for (int i = 0; i < n; i++) {
            out.add(0);
        }
        return out;
    }

    static Object pyBytes(Object v) {
        return v;
    }

    static String pyStrJoin(String sep, List<?> items) {
        StringJoiner sj = new StringJoiner(sep);
        for (Object item : items) {
            sj.add(String.valueOf(item));
        }
        return sj.toString();
    }

    static String pyStrStrip(String value) {
        return value.trim();
    }

    static String pyStrRStrip(String value) {
        int end = value.length();
        while (end > 0 && Character.isWhitespace(value.charAt(end - 1))) {
            end -= 1;
        }
        return value.substring(0, end);
    }

    static boolean pyStrStartswith(String value, String prefix) {
        return value.startsWith(prefix);
    }

    static boolean pyStrEndswith(String value, String suffix) {
        return value.endsWith(suffix);
    }

    static String pyStrReplace(String value, String oldValue, String newValue) {
        return value.replace(oldValue, newValue);
    }

    static String pyStrUpper(String value) {
        return value.toUpperCase();
    }

    static long __pytra_find(Object value, Object sub) {
        return pyToString(value).indexOf(pyToString(sub));
    }

    static long __pytra_rfind(Object value, Object sub) {
        return pyToString(value).lastIndexOf(pyToString(sub));
    }

    static long __pytra_count_substr(Object value, Object sub) {
        String s = pyToString(value);
        String needle = pyToString(sub);
        if (needle.isEmpty()) {
            return s.length() + 1L;
        }
        long count = 0L;
        int index = 0;
        while (true) {
            int found = s.indexOf(needle, index);
            if (found < 0) {
                return count;
            }
            count += 1L;
            index = found + needle.length();
        }
    }

    static long __pytra_str_index(Object value, Object sub) {
        long found = __pytra_find(value, sub);
        if (found < 0L) {
            throw new RuntimeException("substring not found");
        }
        return found;
    }

    static ArrayList<Object> pyDictKeys(Object value) {
        if (value instanceof Map<?, ?>) {
            Map<?, ?> map = (Map<?, ?>) value;
            return new ArrayList<>(((Map<Object, Object>) map).keySet());
        }
        throw new RuntimeException("dict.keys unsupported");
    }

    static ArrayList<Object> pyDictValues(Object value) {
        if (value instanceof Map<?, ?>) {
            Map<?, ?> map = (Map<?, ?>) value;
            return new ArrayList<>(((Map<Object, Object>) map).values());
        }
        throw new RuntimeException("dict.values unsupported");
    }

    static ArrayList<Object> pyDictItems(Object value) {
        if (value instanceof Map<?, ?>) {
            Map<?, ?> map = (Map<?, ?>) value;
            ArrayList<Object> out = new ArrayList<>();
            for (Map.Entry<?, ?> entry : map.entrySet()) {
                ArrayList<Object> pair = new ArrayList<>(2);
                pair.add(entry.getKey());
                pair.add(entry.getValue());
                out.add(pair);
            }
            return out;
        }
        throw new RuntimeException("dict.items unsupported");
    }

    static void pyMakedirs(String path, boolean existOk) {
        try {
            java.nio.file.Path dir = Paths.get(path);
            if (!existOk && Files.exists(dir)) {
                throw new RuntimeException("Directory already exists: " + path);
            }
            Files.createDirectories(dir);
        } catch (IOException ex) {
            throw new RuntimeException(ex);
        }
    }

    static void __pytra_set_argv(ArrayList<String> args) {
        __pytra_argv = new ArrayList<>(args);
    }

    static void __pytra_set_path(ArrayList<String> paths) {
        __pytra_path = new ArrayList<>(paths);
    }

    static String __pytra_join(String... parts) {
        if (parts.length == 0) {
            return "";
        }
        String result = parts[0];
        int i = 1;
        while (i < parts.length) {
            String part = parts[i];
            if (part.startsWith("/")) {
                result = part;
            } else if (result.endsWith("/")) {
                result = result + part;
            } else {
                result = result + "/" + part;
            }
            i += 1;
        }
        return result;
    }

    static ArrayList<Object> __pytra_splitext(String path) {
        int slash = Math.max(path.lastIndexOf('/'), path.lastIndexOf('\\'));
        int dot = path.lastIndexOf('.');
        String root = path;
        String ext = "";
        if (dot > slash && dot >= 0) {
            root = path.substring(0, dot);
            ext = path.substring(dot);
        }
        return new ArrayList<>(java.util.Arrays.asList(root, ext));
    }

    static String __pytra_basename(String path) {
        String trimmed = (path.endsWith("/") || path.endsWith("\\")) ? path.substring(0, path.length() - 1) : path;
        int slash = Math.max(trimmed.lastIndexOf('/'), trimmed.lastIndexOf('\\'));
        if (slash < 0) {
            return trimmed;
        }
        return trimmed.substring(slash + 1);
    }

    static String __pytra_dirname(String path) {
        String trimmed = (path.endsWith("/") || path.endsWith("\\")) ? path.substring(0, path.length() - 1) : path;
        int slash = Math.max(trimmed.lastIndexOf('/'), trimmed.lastIndexOf('\\'));
        if (slash < 0) {
            return "";
        }
        if (slash == 0) {
            return "/";
        }
        return trimmed.substring(0, slash);
    }

    static boolean __pytra_exists(String path) {
        try {
            return Files.exists(Paths.get(path));
        } catch (RuntimeException _err) {
            return false;
        }
    }

    static ArrayList<String> __pytra_glob(String pattern) {
        ArrayList<String> out = new ArrayList<>();
        try {
            String dir = __pytra_dirname(pattern);
            if (dir.equals("")) {
                dir = ".";
            }
            String base = __pytra_basename(pattern);
            final String dirText = dir;
            String regex = base
                .replace("\\", "\\\\")
                .replace(".", "\\.")
                .replace("+", "\\+")
                .replace("^", "\\^")
                .replace("$", "\\$")
                .replace("{", "\\{")
                .replace("}", "\\}")
                .replace("(", "\\(")
                .replace(")", "\\)")
                .replace("|", "\\|")
                .replace("[", "\\[")
                .replace("]", "\\]")
                .replace("*", ".*")
                .replace("?", ".");
            java.util.regex.Pattern compiled = java.util.regex.Pattern.compile("^" + regex + "$");
            java.nio.file.Path dirPath = Paths.get(dir);
            try (java.nio.file.DirectoryStream<java.nio.file.Path> stream = Files.newDirectoryStream(dirPath)) {
                for (java.nio.file.Path path : stream) {
                    String name = path.getFileName().toString();
                    if (compiled.matcher(name).matches()) {
                        out.add(dirText.equals(".") ? name : dirText + "/" + name);
                    }
                }
            }
        } catch (IOException _err) {
            return out;
        }
        return out;
    }

    static String __pytra_re_sub(String pattern, String repl, String text, long count) {
        java.util.regex.Pattern compiled = java.util.regex.Pattern.compile(pattern);
        if (count == 0L) {
            return compiled.matcher(text).replaceAll(repl);
        }
        String result = text;
        long i = 0L;
        while (i < count) {
            java.util.regex.Matcher matcher = compiled.matcher(result);
            if (!matcher.find()) {
                return result;
            }
            result = matcher.replaceFirst(repl);
            i += 1L;
        }
        return result;
    }

    static String __pytra_re_sub(String pattern, String repl, String text) {
        return __pytra_re_sub(pattern, repl, text, 0L);
    }

    static final class __pytra_str {
        private __pytra_str() {
        }

        static boolean isalpha(String value) {
            return __pytra_str_isalpha(value);
        }

        static boolean isdigit(String value) {
            return __pytra_str_isdigit(value);
        }
    }

    private static void __pytra_gif_append(ArrayList<Long> dst, List<?> src) {
        int i = 0;
        while (i < src.size()) {
            Object value = src.get(i);
            dst.add(Long.valueOf(pyToLong(value) & 0xffL));
            i += 1;
        }
    }

    private static ArrayList<Long> __pytra_gif_u16le(long value) {
        ArrayList<Long> out = new ArrayList<>();
        out.add(Long.valueOf(value & 0xffL));
        out.add(Long.valueOf((value >> 8) & 0xffL));
        return out;
    }

    private static ArrayList<Long> __pytra_lzw_encode(List<?> data, long minCodeSize) {
        if (data.isEmpty()) {
            return new ArrayList<>();
        }

        long clearCode = 1L << minCodeSize;
        long endCode = clearCode + 1L;
        long codeSize = minCodeSize + 1L;
        ArrayList<Long> out = new ArrayList<>();
        long bitBuffer = clearCode;
        long bitCount = codeSize;
        while (bitCount >= 8L) {
            out.add(Long.valueOf(bitBuffer & 0xffL));
            bitBuffer >>= 8;
            bitCount -= 8L;
        }
        codeSize = minCodeSize + 1L;

        int index = 0;
        while (index < data.size()) {
            long value = pyToLong(data.get(index));

            bitBuffer |= value << bitCount;
            bitCount += codeSize;
            while (bitCount >= 8L) {
                out.add(Long.valueOf(bitBuffer & 0xffL));
                bitBuffer >>= 8;
                bitCount -= 8L;
            }

            bitBuffer |= clearCode << bitCount;
            bitCount += codeSize;
            while (bitCount >= 8L) {
                out.add(Long.valueOf(bitBuffer & 0xffL));
                bitBuffer >>= 8;
                bitCount -= 8L;
            }

            codeSize = minCodeSize + 1L;
            index += 1;
        }

        bitBuffer |= endCode << bitCount;
        bitCount += codeSize;
        while (bitCount >= 8L) {
            out.add(Long.valueOf(bitBuffer & 0xffL));
            bitBuffer >>= 8;
            bitCount -= 8L;
        }
        if (bitCount > 0L) {
            out.add(Long.valueOf(bitBuffer & 0xffL));
        }
        return out;
    }

    private static byte[] __pytra_bytes_raw(List<?> data) {
        byte[] out = new byte[data.size()];
        int i = 0;
        while (i < data.size()) {
            out[i] = (byte) (pyToLong(data.get(i)) & 0xffL);
            i += 1;
        }
        return out;
    }

    static ArrayList<Long> __pytra_bytes(Object data) {
        return __pytra_bytearray(data);
    }

    static ArrayList<Long> __pytra_bytes() {
        return new ArrayList<Long>();
    }

    static <T> void __pytra_append(java.util.List<T> target, T value) {
        target.add(value);
    }

    static long __pytra_max(long left, long right) {
        return Math.max(left, right);
    }

    static double __pytra_max(double left, double right) {
        return Math.max(left, right);
    }

    static long __pytra_min(long left, long right) {
        return Math.min(left, right);
    }

    static double __pytra_min(double left, double right) {
        return Math.min(left, right);
    }

    static <T> ArrayList<T> __pytra_py_sorted(java.util.List<T> data) {
        ArrayList<T> out = new ArrayList<T>(data);
        out.sort((left, right) -> {
            if (left instanceof String || right instanceof String) {
                return pyToString(left).compareTo(pyToString(right));
            }
            return java.lang.Double.compare(pyToFloat(left), pyToFloat(right));
        });
        return out;
    }

    static ArrayList<Long> __pytra_grayscale_palette() {
        ArrayList<Long> out = new ArrayList<>();
        long i = 0L;
        while (i < 256L) {
            out.add(Long.valueOf(i));
            out.add(Long.valueOf(i));
            out.add(Long.valueOf(i));
            i += 1L;
        }
        return out;
    }

    static void __pytra_save_gif(String path, long width, long height, List<?> frames, Object palette, long delayCs, long loop) {
        List<?> paletteList;
        if (palette instanceof List<?>) {
            paletteList = (List<?>) palette;
        } else {
            paletteList = pyIter(palette);
        }
        if (paletteList.size() != (256 * 3)) {
            throw new RuntimeException("palette must be 256*3 bytes");
        }

        long frameSize = width * height;
        ArrayList<Long> out = new ArrayList<>();
        __pytra_gif_append(out, java.util.Arrays.asList(71L, 73L, 70L, 56L, 57L, 97L));
        __pytra_gif_append(out, __pytra_gif_u16le(width));
        __pytra_gif_append(out, __pytra_gif_u16le(height));
        __pytra_gif_append(out, java.util.Arrays.asList(0xF7L, 0L, 0L));
        __pytra_gif_append(out, paletteList);
        __pytra_gif_append(
            out,
            java.util.Arrays.asList(0x21L, 0xFFL, 0x0BL, 78L, 69L, 84L, 83L, 67L, 65L, 80L, 69L, 50L, 46L, 48L, 0x03L, 0x01L)
        );
        __pytra_gif_append(out, __pytra_gif_u16le(loop));
        out.add(0L);

        int frameIndex = 0;
        while (frameIndex < frames.size()) {
            Object frameObj = frames.get(frameIndex);
            List<?> frameList = frameObj instanceof List<?> ? (List<?>) frameObj : pyIter(frameObj);
            if (frameList.size() != frameSize) {
                throw new RuntimeException("frame size mismatch");
            }
            __pytra_gif_append(out, java.util.Arrays.asList(0x21L, 0xF9L, 0x04L, 0x00L));
            __pytra_gif_append(out, __pytra_gif_u16le(delayCs));
            __pytra_gif_append(out, java.util.Arrays.asList(0x00L, 0x00L));
            out.add(0x2CL);
            __pytra_gif_append(out, __pytra_gif_u16le(0L));
            __pytra_gif_append(out, __pytra_gif_u16le(0L));
            __pytra_gif_append(out, __pytra_gif_u16le(width));
            __pytra_gif_append(out, __pytra_gif_u16le(height));
            out.add(0L);
            out.add(8L);

            ArrayList<Long> compressed = __pytra_lzw_encode(frameList, 8L);
            int pos = 0;
            while (pos < compressed.size()) {
                int remain = compressed.size() - pos;
                int chunkLen = remain > 255 ? 255 : remain;
                out.add(Long.valueOf(chunkLen));
                int i = 0;
                while (i < chunkLen) {
                    out.add(compressed.get(pos + i));
                    i += 1;
                }
                pos += chunkLen;
            }
            out.add(0L);
            frameIndex += 1;
        }

        out.add(0x3BL);
        try {
            java.nio.file.Path outPath = Paths.get(path);
            java.nio.file.Path parent = outPath.getParent();
            if (parent != null) {
                Files.createDirectories(parent);
            }
            Files.write(outPath, __pytra_bytes_raw(out));
        } catch (IOException ex) {
            throw new RuntimeException(ex);
        }
    }

    static void __pytra_save_gif(String path, long width, long height, List<?> frames, Object palette, long delayCs) {
        __pytra_save_gif(path, width, height, frames, palette, delayCs, 0L);
    }

    static void __pytra_save_gif(String path, long width, long height, List<?> frames, Object palette) {
        __pytra_save_gif(path, width, height, frames, palette, 4L, 0L);
    }

    static boolean __pytra_str_isalpha(String value) {
        if (value == null || value.isEmpty()) {
            return false;
        }
        int i = 0;
        while (i < value.length()) {
            if (!Character.isLetter(value.charAt(i))) {
                return false;
            }
            i += 1;
        }
        return true;
    }

    static json.JsonValue __pytra_loads(String text) {
        return json.loads(text);
    }

    static json.JsonArr __pytra_loads_arr(String text) {
        return json.loads_arr(text);
    }

    static json.JsonObj __pytra_loads_obj(String text) {
        return json.loads_obj(text);
    }

    static String __pytra_dumps(Object value, boolean ensureAscii, Object indent, Object separators) {
        return json.dumps(value, ensureAscii, indent, separators);
    }

    static boolean pyAssertTrue(boolean cond, String label) {
        if (cond) {
            return true;
        }
        pyPrint(label.isEmpty() ? "[assert_true] False" : "[assert_true] " + label + ": False");
        return false;
    }

    static boolean pyAssertEq(Object actual, Object expected, String label) {
        boolean ok = pyToString(actual).equals(pyToString(expected));
        if (ok) {
            return true;
        }
        String detail = "actual=" + pyToString(actual) + ", expected=" + pyToString(expected);
        pyPrint(label.isEmpty() ? "[assert_eq] " + detail : "[assert_eq] " + label + ": " + detail);
        return false;
    }

    static boolean pyAssertAll(List<?> results, String label) {
        for (Object value : results) {
            if (!pyBool(value)) {
                pyPrint(label.isEmpty() ? "[assert_all] False" : "[assert_all] " + label + ": False");
                return false;
            }
        }
        return true;
    }

    static String pyAssertStdout(List<?> expected, Runnable fn) {
        PrintStream original = System.out;
        ByteArrayOutputStream buffer = new ByteArrayOutputStream();
        PrintStream capture = new PrintStream(buffer);
        System.setOut(capture);
        try {
            fn.run();
        } finally {
            capture.flush();
            System.setOut(original);
        }
        String actualText = buffer.toString().replace("\r\n", "\n");
        if (actualText.endsWith("\n")) {
            actualText = actualText.substring(0, actualText.length() - 1);
        }
        StringJoiner expectedJoin = new StringJoiner("\n");
        for (Object item : expected) {
            expectedJoin.add(String.valueOf(item));
        }
        String expectedText = expectedJoin.toString();
        if (!actualText.equals(expectedText)) {
            return "[assert_stdout] FAIL\n  expected: " + expected.toString() + "\n  actual:   [" + actualText + "]";
        }
        return "True";
    }

    static boolean pyIsDigit(Object v) {
        String s = pyToString(v);
        if (s.isEmpty()) {
            return false;
        }
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c < '0' || c > '9') {
                return false;
            }
        }
        return true;
    }

    static boolean pyIsAlpha(Object v) {
        String s = pyToString(v);
        if (s.isEmpty()) {
            return false;
        }
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z'))) {
                return false;
            }
        }
        return true;
    }

    static List<Object> pyList(Object... items) {
        List<Object> out = new ArrayList<>();
        for (Object item : items) {
            out.add(item);
        }
        return out;
    }

    static Map<Object, Object> pyDict(Object... kv) {
        Map<Object, Object> out = new HashMap<>();
        for (int i = 0; i + 1 < kv.length; i += 2) {
            out.put(kv[i], kv[i + 1]);
        }
        return out;
    }

    static void __pytra_noop(Object... args) {
    }

    static final class PyFile {
        private final String path;
        private final String mode;
        private final String encoding;

        PyFile(String path, String mode, String encoding) {
            this.path = path;
            this.mode = mode;
            this.encoding = encoding == null || encoding.isEmpty() ? "utf-8" : encoding;
        }

        String read() {
            try {
                return Files.readString(Paths.get(path), java.nio.charset.Charset.forName(encoding));
            } catch (IOException ex) {
                throw new RuntimeException(ex);
            }
        }

        long write(Object value) {
            try {
                if (mode.contains("b")) {
                    java.util.ArrayList<Long> src = __pytra_bytearray(value);
                    byte[] bytes = new byte[src.size()];
                    int i = 0;
                    while (i < src.size()) {
                        bytes[i] = (byte) (src.get(i) & 0xFFL);
                        i += 1;
                    }
                    Files.write(Paths.get(path), bytes);
                    return bytes.length;
                }
                String text = String.valueOf(value);
                byte[] bytes = text.getBytes(java.nio.charset.Charset.forName(encoding));
                Files.write(Paths.get(path), bytes);
                return text.length();
            } catch (IOException ex) {
                throw new RuntimeException(ex);
            }
        }

        PyFile __enter__() {
            return this;
        }

        Object __exit__(Object excType, Object excVal, Object excTb) {
            close();
            return null;
        }

        void close() {
        }
    }

    static PyFile open(String path, String mode) {
        return new PyFile(path, mode, "utf-8");
    }

    static PyFile open(String path, String mode, String encoding) {
        return new PyFile(path, mode, encoding);
    }

    static PyFile __pytra_open(String path, String mode) {
        return open(path, mode);
    }

    static PyFile __pytra_open(String path, String mode, String encoding) {
        return open(path, mode, encoding);
    }

    static long __pytra_int(Object value) {
        if (value == null) {
            return 0L;
        }
        if (value instanceof Number) {
            return ((Number) value).longValue();
        }
        if (value instanceof Boolean) {
            return ((Boolean) value) ? 1L : 0L;
        }
        if (value instanceof String) {
            String s = ((String) value).trim();
            if (s.isEmpty()) {
                return 0L;
            }
            try {
                return Long.parseLong(s);
            } catch (NumberFormatException ex) {
                return 0L;
            }
        }
        return 0L;
    }

    static java.util.ArrayList<Long> __pytra_int_to_bytes(Object value, Object length, Object byteorder) {
        long v = __pytra_int(value);
        long n = __pytra_int(length);
        String order = String.valueOf(byteorder);
        java.util.ArrayList<Long> out = new java.util.ArrayList<Long>();
        long i = 0L;
        while (i < n) {
            long b = v & 255L;
            out.add(b);
            v = v >> 8L;
            i += 1L;
        }
        if (!java.util.Objects.equals(order, "little")) {
            java.util.Collections.reverse(out);
        }
        return out;
    }

    static long __pytra_len(Object value) {
        if (value == null) {
            return 0L;
        }
        if (value instanceof String) {
            return ((String) value).length();
        }
        if (value instanceof java.util.Map<?, ?>) {
            return ((java.util.Map<?, ?>) value).size();
        }
        if (value instanceof java.util.List<?>) {
            return ((java.util.List<?>) value).size();
        }
        if (value instanceof java.util.Collection<?>) {
            return ((java.util.Collection<?>) value).size();
        }
        return 0L;
    }

    static boolean __pytra_str_isdigit(Object value) {
        String s = String.valueOf(value);
        if (s.isEmpty()) {
            return false;
        }
        int i = 0;
        while (i < s.length()) {
            if (!Character.isDigit(s.charAt(i))) {
                return false;
            }
            i += 1;
        }
        return true;
    }

    static boolean __pytra_str_isalpha(Object value) {
        String s = String.valueOf(value);
        if (s.isEmpty()) {
            return false;
        }
        int i = 0;
        while (i < s.length()) {
            if (!Character.isLetter(s.charAt(i))) {
                return false;
            }
            i += 1;
        }
        return true;
    }

    static String __pytra_str_slice(String s, long start, long stop) {
        long n = s.length();
        long lo = start;
        long hi = stop;
        if (lo < 0L) {
            lo += n;
        }
        if (hi < 0L) {
            hi += n;
        }
        if (lo < 0L) {
            lo = 0L;
        }
        if (hi < 0L) {
            hi = 0L;
        }
        if (lo > n) {
            lo = n;
        }
        if (hi > n) {
            hi = n;
        }
        if (hi < lo) {
            hi = lo;
        }
        return s.substring((int) lo, (int) hi);
    }

    static java.util.ArrayList<Long> __pytra_bytearray(Object init) {
        java.util.ArrayList<Long> out = new java.util.ArrayList<Long>();
        if (init instanceof Number) {
            long n = ((Number) init).longValue();
            long i = 0L;
            while (i < n) {
                out.add(0L);
                i += 1L;
            }
            return out;
        }
        if (init instanceof java.util.List<?>) {
            java.util.List<?> src = (java.util.List<?>) init;
            int i = 0;
            while (i < src.size()) {
                Object v = src.get(i);
                if (v instanceof Number) {
                    out.add(((Number) v).longValue());
                } else {
                    out.add(0L);
                }
                i += 1;
            }
        }
        return out;
    }

    static java.util.ArrayList<Long> __pytra_bytearray() {
        return __pytra_bytearray(0L);
    }

    static void __pytra_write_rgb_png(String path, long width, long height, Object pixels) {
        pyWriteRgbPng(path, width, height, __pytra_bytearray(pixels));
    }

    static final class deque extends java.util.ArrayList<Object> {
        deque() {
            super();
        }

        deque(Object init) {
            super();
            if (init == null) {
                return;
            }
            addAll(PyRuntime.pyIter(init));
        }

        boolean append(Object value) {
            return add(value);
        }

        void appendleft(Object value) {
            add(0, value);
        }

        Object popleft() {
            if (isEmpty()) {
                throw new RuntimeException("pop from an empty deque");
            }
            return remove(0);
        }

        public Object pop() {
            if (isEmpty()) {
                throw new RuntimeException("pop from an empty deque");
            }
            return remove(size() - 1);
        }
    }

    static deque deque() {
        return new deque();
    }

    static deque deque(Object init) {
        return new deque(init);
    }

    static <T> java.util.ArrayList<T> __pytra_list_concat(java.util.List<? extends T> left, java.util.List<? extends T> right) {
        java.util.ArrayList<T> out = new java.util.ArrayList<T>(left.size() + right.size());
        out.addAll(left);
        out.addAll(right);
        return out;
    }

    static <T> java.util.ArrayList<T> __pytra_list_slice(java.util.List<T> src, long start, long stop) {
        long n = src.size();
        long lo = start;
        long hi = stop;
        if (lo < 0L) {
            lo += n;
        }
        if (hi < 0L) {
            hi += n;
        }
        if (lo < 0L) {
            lo = 0L;
        }
        if (hi < 0L) {
            hi = 0L;
        }
        if (lo > n) {
            lo = n;
        }
        if (hi > n) {
            hi = n;
        }
        if (hi < lo) {
            hi = lo;
        }
        java.util.ArrayList<T> out = new java.util.ArrayList<T>((int) (hi - lo));
        long i = lo;
        while (i < hi) {
            out.add(src.get((int) i));
            i += 1L;
        }
        return out;
    }

    static java.util.HashMap<Object, Object> __pytra_dict_of(Object... kv) {
        java.util.HashMap<Object, Object> out = new java.util.HashMap<Object, Object>();
        int i = 0;
        while (i + 1 < kv.length) {
            out.put(kv[i], kv[i + 1]);
            i += 2;
        }
        return out;
    }

    static Object __pytra_dict_get_default(Object mapObj, Object key, Object defaultValue) {
        if (mapObj instanceof Map<?, ?>) {
            @SuppressWarnings("unchecked")
            Map<Object, Object> map = (Map<Object, Object>) mapObj;
            if (map.containsKey(key)) {
                return map.get(key);
            }
        }
        return defaultValue;
    }

    static <T> T __pytra_pop(Object mapObj, Object key) {
        if (mapObj instanceof Map<?, ?>) {
            @SuppressWarnings("unchecked")
            Map<Object, Object> map = (Map<Object, Object>) mapObj;
            return (T) map.remove(key);
        }
        return null;
    }

    static <T> T __pytra_setdefault(Object mapObj, Object key, T defaultValue) {
        if (mapObj instanceof Map<?, ?>) {
            @SuppressWarnings("unchecked")
            Map<Object, Object> map = (Map<Object, Object>) mapObj;
            if (map.containsKey(key)) {
                return (T) map.get(key);
            }
            map.put(key, defaultValue);
            return defaultValue;
        }
        return defaultValue;
    }

    static <T> java.util.ArrayList<T> __pytra_list_repeat(T value, long count) {
        java.util.ArrayList<T> out = new java.util.ArrayList<T>();
        long i = 0L;
        while (i < count) {
            out.add(value);
            i += 1L;
        }
        return out;
    }

    static <T> java.util.ArrayList<T> __pytra_repeat_list(java.util.List<? extends T> items, long count) {
        java.util.ArrayList<T> out = new java.util.ArrayList<T>();
        if (count <= 0L || items.isEmpty()) {
            return out;
        }
        long i = 0L;
        while (i < count) {
            out.addAll(items);
            i += 1L;
        }
        return out;
    }

    private static void _pngAppendList(java.util.ArrayList<Long> dst, java.util.List<Long> src) {
        dst.addAll(src);
    }

    private static long _crc32(java.util.List<Long> data) {
        java.util.zip.CRC32 crc = new java.util.zip.CRC32();
        int i = 0;
        while (i < data.size()) {
            crc.update((int) (data.get(i) & 0xFFL));
            i += 1;
        }
        return crc.getValue() & 0xFFFFFFFFL;
    }

    private static long _adler32(java.util.List<Long> data) {
        java.util.zip.Adler32 adler = new java.util.zip.Adler32();
        int i = 0;
        while (i < data.size()) {
            adler.update((int) (data.get(i) & 0xFFL));
            i += 1;
        }
        return adler.getValue() & 0xFFFFFFFFL;
    }

    private static java.util.ArrayList<Long> _pngU16le(long value) {
        java.util.ArrayList<Long> out = new java.util.ArrayList<Long>();
        out.add(value & 0xFFL);
        out.add((value >> 8) & 0xFFL);
        return out;
    }

    private static java.util.ArrayList<Long> _pngU32be(long value) {
        java.util.ArrayList<Long> out = new java.util.ArrayList<Long>();
        out.add((value >> 24) & 0xFFL);
        out.add((value >> 16) & 0xFFL);
        out.add((value >> 8) & 0xFFL);
        out.add(value & 0xFFL);
        return out;
    }

    private static java.util.ArrayList<Long> _zlibDeflateStore(java.util.ArrayList<Long> data) {
        java.util.ArrayList<Long> out = new java.util.ArrayList<Long>();
        _pngAppendList(out, new java.util.ArrayList<Long>(java.util.Arrays.asList(0x78L, 0x01L)));
        long n = data.size();
        long pos = 0L;
        while (pos < n) {
            long remain = n - pos;
            long chunkLen = remain > 65535L ? 65535L : remain;
            long isFinal = (pos + chunkLen) >= n ? 1L : 0L;
            out.add(isFinal);
            _pngAppendList(out, _pngU16le(chunkLen));
            _pngAppendList(out, _pngU16le(0xFFFFL ^ chunkLen));
            long i = pos;
            long end = pos + chunkLen;
            while (i < end) {
                out.add(data.get((int) i));
                i += 1L;
            }
            pos += chunkLen;
        }
        _pngAppendList(out, _pngU32be(_adler32(data)));
        return out;
    }

    private static java.util.ArrayList<Long> _pngChunk(java.util.List<Long> chunkType, java.util.ArrayList<Long> data) {
        java.util.ArrayList<Long> crcInput = new java.util.ArrayList<Long>();
        _pngAppendList(crcInput, chunkType);
        _pngAppendList(crcInput, data);
        long crc = _crc32(crcInput);
        java.util.ArrayList<Long> out = new java.util.ArrayList<Long>();
        _pngAppendList(out, _pngU32be(data.size()));
        _pngAppendList(out, chunkType);
        _pngAppendList(out, data);
        _pngAppendList(out, _pngU32be(crc));
        return out;
    }

    static void pyWriteRgbPng(String path, long width, long height, java.util.List<Long> pixels) {
        java.util.ArrayList<Long> raw = new java.util.ArrayList<Long>(pixels);
        long expected = width * height * 3L;
        if (raw.size() != expected) {
            throw new RuntimeException("pixels length mismatch: got=" + raw.size() + " expected=" + expected);
        }
        java.util.ArrayList<Long> scanlines = new java.util.ArrayList<Long>();
        long rowBytes = width * 3L;
        long y = 0L;
        while (y < height) {
            scanlines.add(0L);
            long start = y * rowBytes;
            long end = start + rowBytes;
            long i = start;
            while (i < end) {
                scanlines.add(raw.get((int) i));
                i += 1L;
            }
            y += 1L;
        }
        java.util.ArrayList<Long> ihdr = new java.util.ArrayList<Long>();
        _pngAppendList(ihdr, _pngU32be(width));
        _pngAppendList(ihdr, _pngU32be(height));
        _pngAppendList(ihdr, new java.util.ArrayList<Long>(java.util.Arrays.asList(8L, 2L, 0L, 0L, 0L)));
        java.util.ArrayList<Long> idat = _zlibDeflateStore(scanlines);
        java.util.ArrayList<Long> png = new java.util.ArrayList<Long>();
        _pngAppendList(png, new java.util.ArrayList<Long>(java.util.Arrays.asList(137L, 80L, 78L, 71L, 13L, 10L, 26L, 10L)));
        _pngAppendList(png, _pngChunk(new java.util.ArrayList<Long>(java.util.Arrays.asList(73L, 72L, 68L, 82L)), ihdr));
        _pngAppendList(png, _pngChunk(new java.util.ArrayList<Long>(java.util.Arrays.asList(73L, 68L, 65L, 84L)), idat));
        _pngAppendList(png, _pngChunk(new java.util.ArrayList<Long>(java.util.Arrays.asList(73L, 69L, 78L, 68L)), new java.util.ArrayList<Long>()));
        PyFile file = open(path, "wb");
        try {
            file.write(png);
        } finally {
            file.close();
        }
    }

    static java.util.ArrayList<Object> __pytra_enumerate(Object value) {
        java.util.ArrayList<Object> out = new java.util.ArrayList<Object>();
        List<Object> items = pyIter(value);
        int i = 0;
        while (i < items.size()) {
            java.util.ArrayList<Object> pair = new java.util.ArrayList<Object>(2);
            pair.add((long) i);
            pair.add(items.get(i));
            out.add(pair);
            i += 1;
        }
        return out;
    }

    static boolean __pytra_truthy(Object value) {
        if (value == null) {
            return false;
        }
        if (value instanceof Boolean) {
            return ((Boolean) value);
        }
        if (value instanceof Number) {
            return ((Number) value).doubleValue() != 0.0;
        }
        if (value instanceof String) {
            return !((String) value).isEmpty();
        }
        if (value instanceof java.util.List<?>) {
            return !((java.util.List<?>) value).isEmpty();
        }
        return true;
    }
}

final class os_path {
    os_path() {
    }

    static String join(String a, String b) {
        return PyRuntime.__pytra_join(a, b);
    }

    static ArrayList<Object> splitext(String p) {
        return PyRuntime.__pytra_splitext(p);
    }

    static String basename(String p) {
        return PyRuntime.__pytra_basename(p);
    }

    static String dirname(String p) {
        return PyRuntime.__pytra_dirname(p);
    }

    static boolean exists(String p) {
        return PyRuntime.__pytra_exists(p);
    }

    static String abspath(String p) {
        return Paths.get(p).toAbsolutePath().normalize().toString();
    }
}

final class os {
    static final os_path path = new os_path();

    os() {
    }

    static void makedirs(String path, boolean existOk) {
        PyRuntime.pyMakedirs(path, existOk);
    }
}

final class glob {
    glob() {
    }

    static ArrayList<String> glob(String pattern) {
        return PyRuntime.__pytra_glob(pattern);
    }
}

final class pytra_std_os {
    static final os os = new os();
}

final class pytra_std_glob {
    static final glob glob = new glob();
}

final class pytra_std_collections {
    static PyRuntime.deque deque() {
        return PyRuntime.deque();
    }
}

final class math {
    static final double pi = math_native.pi;
    static final double e = math_native.e;

    math() {
    }

    static double sqrt(double x) {
        return math_native.sqrt(x);
    }

    static double sin(double x) {
        return math_native.sin(x);
    }

    static double cos(double x) {
        return math_native.cos(x);
    }

    static double tan(double x) {
        return math_native.tan(x);
    }

    static double exp(double x) {
        return math_native.exp(x);
    }

    static double log(double x) {
        return math_native.log(x);
    }

    static double log10(double x) {
        return math_native.log10(x);
    }

    static double fabs(double x) {
        return math_native.fabs(x);
    }

    static double floor(double x) {
        return math_native.floor(x);
    }

    static double ceil(double x) {
        return math_native.ceil(x);
    }

    static double pow(double x, double y) {
        return math_native.pow(x, y);
    }
}
