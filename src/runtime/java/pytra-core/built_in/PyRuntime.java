// Java ネイティブ変換向け Python 互換ランタイム補助。
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.StringJoiner;

final class PyRuntime {
    private PyRuntime() {
    }

    static String pyToString(Object v) {
        if (v == null) {
            return "None";
        }
        if (v instanceof Boolean b) {
            return b ? "True" : "False";
        }
        if (v instanceof List<?> list) {
            StringJoiner sj = new StringJoiner(", ", "[", "]");
            for (Object it : list) {
                sj.add(pyToString(it));
            }
            return sj.toString();
        }
        if (v instanceof Map<?, ?> map) {
            StringJoiner sj = new StringJoiner(", ", "{", "}");
            for (Map.Entry<?, ?> e : map.entrySet()) {
                sj.add(pyToString(e.getKey()) + ": " + pyToString(e.getValue()));
            }
            return sj.toString();
        }
        return String.valueOf(v);
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
        if (v instanceof Boolean b) {
            return b;
        }
        if (v instanceof Integer i) {
            return i != 0;
        }
        if (v instanceof Long i) {
            return i != 0L;
        }
        if (v instanceof Double d) {
            return d != 0.0;
        }
        if (v instanceof String s) {
            return !s.isEmpty();
        }
        if (v instanceof List<?> list) {
            return !list.isEmpty();
        }
        if (v instanceof Map<?, ?> map) {
            return !map.isEmpty();
        }
        return true;
    }

    static int pyLen(Object v) {
        if (v instanceof String s) {
            return s.length();
        }
        if (v instanceof List<?> list) {
            return list.size();
        }
        if (v instanceof byte[] bytes) {
            return bytes.length;
        }
        if (v instanceof Map<?, ?> map) {
            return map.size();
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

    static double pyToFloat(Object v) {
        if (v instanceof Integer i) {
            return i;
        }
        if (v instanceof Long i) {
            return i;
        }
        if (v instanceof Double d) {
            return d;
        }
        if (v instanceof Boolean b) {
            return b ? 1.0 : 0.0;
        }
        throw new RuntimeException("cannot convert to float");
    }

    static int pyToInt(Object v) {
        if (v instanceof Integer i) {
            return i;
        }
        if (v instanceof Long i) {
            return (int) i.longValue();
        }
        if (v instanceof Double d) {
            // Python の int() は小数部切り捨て（0方向）なので Java のキャストで合わせる。
            return (int) d.doubleValue();
        }
        if (v instanceof Boolean b) {
            return b ? 1 : 0;
        }
        throw new RuntimeException("cannot convert to int");
    }

    static long pyToLong(Object v) {
        if (v instanceof Integer i) {
            return i.longValue();
        }
        if (v instanceof Long i) {
            return i.longValue();
        }
        if (v instanceof Double d) {
            return (long) d.doubleValue();
        }
        if (v instanceof Boolean b) {
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
        if (container instanceof String s) {
            return s.contains(pyToString(item));
        }
        if (container instanceof List<?> list) {
            for (Object v : list) {
                if (pyEq(v, item)) {
                    return true;
                }
            }
            return false;
        }
        if (container instanceof Map<?, ?> map) {
            return map.containsKey(item);
        }
        return false;
    }

    static List<Object> pyIter(Object value) {
        if (value instanceof List<?> list) {
            return new ArrayList<>((List<Object>) list);
        }
        if (value instanceof byte[] arr) {
            List<Object> out = new ArrayList<>();
            for (byte b : arr) {
                out.add((int) (b & 0xff));
            }
            return out;
        }
        if (value instanceof String s) {
            List<Object> out = new ArrayList<>();
            for (int i = 0; i < s.length(); i++) {
                out.add(String.valueOf(s.charAt(i)));
            }
            return out;
        }
        if (value instanceof Map<?, ?> map) {
            return new ArrayList<>(((Map<Object, Object>) map).keySet());
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
        if (value instanceof String s) {
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
        if (value instanceof List<?> list) {
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
        if (value instanceof List<?> list) {
            int i = pyToInt(key);
            if (i < 0)
                i += list.size();
            return list.get(i);
        }
        if (value instanceof Map<?, ?> map) {
            return ((Map<Object, Object>) map).get(key);
        }
        if (value instanceof String s) {
            int i = pyToInt(key);
            if (i < 0)
                i += s.length();
            return String.valueOf(s.charAt(i));
        }
        throw new RuntimeException("subscript unsupported");
    }

    static void pySet(Object value, Object key, Object newValue) {
        if (value instanceof List<?> list) {
            int i = pyToInt(key);
            List<Object> l = (List<Object>) list;
            if (i < 0)
                i += l.size();
            l.set(i, newValue);
            return;
        }
        if (value instanceof Map<?, ?> map) {
            ((Map<Object, Object>) map).put(key, newValue);
            return;
        }
        throw new RuntimeException("setitem unsupported");
    }

    static Object pyPop(Object value, Object idx) {
        if (value instanceof List<?> list) {
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

    // --- time/math ---

    static Object pyPerfCounter() {
        return System.nanoTime() / 1_000_000_000.0;
    }

    static double pyMathSqrt(Object v) {
        return Math.sqrt(pyToFloat(v));
    }

    static double pyMathSin(Object v) {
        return Math.sin(pyToFloat(v));
    }

    static double pyMathCos(Object v) {
        return Math.cos(pyToFloat(v));
    }

    static double pyMathTan(Object v) {
        return Math.tan(pyToFloat(v));
    }

    static double pyMathExp(Object v) {
        return Math.exp(pyToFloat(v));
    }

    static double pyMathLog(Object v) {
        return Math.log(pyToFloat(v));
    }

    static double pyMathLog10(Object v) {
        return Math.log10(pyToFloat(v));
    }

    static double pyMathFabs(Object v) {
        return Math.abs(pyToFloat(v));
    }

    static double pyMathFloor(Object v) {
        return Math.floor(pyToFloat(v));
    }

    static double pyMathCeil(Object v) {
        return Math.ceil(pyToFloat(v));
    }

    static double pyMathPow(Object a, Object b) {
        return Math.pow(pyToFloat(a), pyToFloat(b));
    }

    static double pyMathPi() {
        return Math.PI;
    }

    static double pyMathE() {
        return Math.E;
    }

    // --- pathlib ---

    static final class Path {
        final String value;
        final Path parent;
        final String name;
        final String stem;

        Path(String value) {
            this(value, false);
        }

        private Path(String value, boolean shallowParent) {
            this.value = value;
            java.nio.file.Path p = Paths.get(value);
            java.nio.file.Path pName = p.getFileName();
            this.name = pName == null ? "" : pName.toString();
            int idx = this.name.lastIndexOf('.');
            this.stem = idx <= 0 ? this.name : this.name.substring(0, idx);
            java.nio.file.Path pParent = p.getParent();
            String parentText = pParent == null ? "" : pParent.toString();
            if (parentText.equals(value)) {
                this.parent = this;
            } else {
                this.parent = shallowParent ? this : new Path(parentText, true);
            }
        }

        @Override
        public String toString() {
            return value;
        }

        boolean exists() {
            return pyBool(pyPathExists(this));
        }

        String read_text() {
            return pyToString(pyPathReadText(this));
        }

        Object write_text(Object content) {
            return pyPathWriteText(this, content);
        }

        Object mkdir(Object parents, Object exist_ok) {
            return pyPathMkdir(this, parents, exist_ok);
        }

        Object mkdir() {
            return pyPathMkdir(this, false, false);
        }

        Path resolve() {
            return (Path) pyPathResolve(this);
        }
    }

    static String pyPathString(Object v) {
        if (v instanceof Path p) {
            return p.value;
        }
        return pyToString(v);
    }

    static Object pyPathNew(Object v) {
        return new Path(pyPathString(v));
    }

    static Object pyPathJoin(Object base, Object child) {
        return new Path(Paths.get(pyPathString(base), pyPathString(child)).toString());
    }

    static Object pyPathResolve(Object v) {
        return new Path(Paths.get(pyPathString(v)).toAbsolutePath().normalize().toString());
    }

    static Object pyPathParent(Object v) {
        java.nio.file.Path p = Paths.get(pyPathString(v)).getParent();
        if (p == null) {
            return new Path("");
        }
        return new Path(p.toString());
    }

    static Object pyPathName(Object v) {
        java.nio.file.Path p = Paths.get(pyPathString(v)).getFileName();
        return p == null ? "" : p.toString();
    }

    static Object pyPathStem(Object v) {
        String base = String.valueOf(pyPathName(v));
        int idx = base.lastIndexOf('.');
        if (idx <= 0) {
            return base;
        }
        return base.substring(0, idx);
    }

    static Object pyPathExists(Object v) {
        return Files.exists(Paths.get(pyPathString(v)));
    }

    static Object pyPathReadText(Object v) {
        try {
            return Files.readString(Paths.get(pyPathString(v)), StandardCharsets.UTF_8);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

    static Object pyPathWriteText(Object v, Object content) {
        try {
            Files.writeString(Paths.get(pyPathString(v)), pyToString(content), StandardCharsets.UTF_8);
            return null;
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

    static Object pyPathMkdir(Object v, Object parents, Object existOk) {
        java.nio.file.Path p = Paths.get(pyPathString(v));
        try {
            if (pyBool(parents)) {
                Files.createDirectories(p);
                return null;
            }
            Files.createDirectory(p);
            return null;
        } catch (IOException e) {
            if (pyBool(existOk) && Files.exists(p)) {
                return null;
            }
            throw new RuntimeException(e);
        }
    }

    // --- json ---

    static String pyJsonDumps(Object v) {
        return jsonStringify(v);
    }

    static Object pyJsonLoads(Object v) {
        return new JsonParser(pyToString(v)).parse();
    }

    private static String jsonStringify(Object v) {
        if (v == null) {
            return "null";
        }
        if (v instanceof Boolean b) {
            return b ? "true" : "false";
        }
        if (v instanceof Integer i) {
            return String.valueOf(i);
        }
        if (v instanceof Long i) {
            return String.valueOf(i);
        }
        if (v instanceof Double d) {
            if (Double.isNaN(d) || Double.isInfinite(d)) {
                throw new RuntimeException("json.dumps: non-finite float");
            }
            return String.valueOf(d);
        }
        if (v instanceof Float f) {
            if (Float.isNaN(f) || Float.isInfinite(f)) {
                throw new RuntimeException("json.dumps: non-finite float");
            }
            return String.valueOf(f);
        }
        if (v instanceof String s) {
            return jsonEscapeString(s);
        }
        if (v instanceof List<?> list) {
            StringJoiner sj = new StringJoiner(",", "[", "]");
            for (Object it : list) {
                sj.add(jsonStringify(it));
            }
            return sj.toString();
        }
        if (v instanceof Map<?, ?> map) {
            StringJoiner sj = new StringJoiner(",", "{", "}");
            for (Map.Entry<?, ?> e : map.entrySet()) {
                String key = pyToString(e.getKey());
                sj.add(jsonEscapeString(key) + ":" + jsonStringify(e.getValue()));
            }
            return sj.toString();
        }
        return jsonEscapeString(pyToString(v));
    }

    private static String jsonEscapeString(String s) {
        StringBuilder out = new StringBuilder();
        out.append('"');
        int i = 0;
        while (i < s.length()) {
            char ch = s.charAt(i);
            if (ch == '"') {
                out.append("\\\"");
            } else if (ch == '\\') {
                out.append("\\\\");
            } else if (ch == '\b') {
                out.append("\\b");
            } else if (ch == '\f') {
                out.append("\\f");
            } else if (ch == '\n') {
                out.append("\\n");
            } else if (ch == '\r') {
                out.append("\\r");
            } else if (ch == '\t') {
                out.append("\\t");
            } else if (ch < 0x20) {
                String hex = Integer.toHexString(ch);
                while (hex.length() < 4) {
                    hex = "0" + hex;
                }
                out.append("\\u").append(hex);
            } else {
                out.append(ch);
            }
            i += 1;
        }
        out.append('"');
        return out.toString();
    }

    private static final class JsonParser {
        private final String text;
        private final int n;
        private int i;

        JsonParser(String text) {
            this.text = text;
            this.n = text.length();
            this.i = 0;
        }

        Object parse() {
            skipWs();
            Object out = parseValue();
            skipWs();
            if (i != n) {
                throw new RuntimeException("invalid json: trailing characters");
            }
            return out;
        }

        private void skipWs() {
            while (i < n) {
                char ch = text.charAt(i);
                if (ch == ' ' || ch == '\t' || ch == '\r' || ch == '\n') {
                    i += 1;
                    continue;
                }
                return;
            }
        }

        private Object parseValue() {
            if (i >= n) {
                throw new RuntimeException("invalid json: unexpected end");
            }
            char ch = text.charAt(i);
            if (ch == '{') {
                return parseObject();
            }
            if (ch == '[') {
                return parseArray();
            }
            if (ch == '"') {
                return parseString();
            }
            if (matchLiteral("true")) {
                i += 4;
                return true;
            }
            if (matchLiteral("false")) {
                i += 5;
                return false;
            }
            if (matchLiteral("null")) {
                i += 4;
                return null;
            }
            return parseNumber();
        }

        private boolean matchLiteral(String lit) {
            if (i + lit.length() > n) {
                return false;
            }
            return text.startsWith(lit, i);
        }

        private Map<Object, Object> parseObject() {
            Map<Object, Object> out = new HashMap<>();
            i += 1; // {
            skipWs();
            if (i < n && text.charAt(i) == '}') {
                i += 1;
                return out;
            }
            while (true) {
                skipWs();
                if (i >= n || text.charAt(i) != '"') {
                    throw new RuntimeException("invalid json object key");
                }
                String key = parseString();
                skipWs();
                if (i >= n || text.charAt(i) != ':') {
                    throw new RuntimeException("invalid json object: missing ':'");
                }
                i += 1;
                skipWs();
                out.put(key, parseValue());
                skipWs();
                if (i >= n) {
                    throw new RuntimeException("invalid json object: unexpected end");
                }
                char delim = text.charAt(i);
                i += 1;
                if (delim == '}') {
                    return out;
                }
                if (delim != ',') {
                    throw new RuntimeException("invalid json object separator");
                }
            }
        }

        private List<Object> parseArray() {
            List<Object> out = new ArrayList<>();
            i += 1; // [
            skipWs();
            if (i < n && text.charAt(i) == ']') {
                i += 1;
                return out;
            }
            while (true) {
                skipWs();
                out.add(parseValue());
                skipWs();
                if (i >= n) {
                    throw new RuntimeException("invalid json array: unexpected end");
                }
                char delim = text.charAt(i);
                i += 1;
                if (delim == ']') {
                    return out;
                }
                if (delim != ',') {
                    throw new RuntimeException("invalid json array separator");
                }
            }
        }

        private String parseString() {
            if (i >= n || text.charAt(i) != '"') {
                throw new RuntimeException("invalid json string");
            }
            i += 1; // opening quote
            StringBuilder out = new StringBuilder();
            while (i < n) {
                char ch = text.charAt(i);
                i += 1;
                if (ch == '"') {
                    return out.toString();
                }
                if (ch == '\\') {
                    if (i >= n) {
                        throw new RuntimeException("invalid json string escape");
                    }
                    char esc = text.charAt(i);
                    i += 1;
                    if (esc == '"' || esc == '\\' || esc == '/') {
                        out.append(esc);
                    } else if (esc == 'b') {
                        out.append('\b');
                    } else if (esc == 'f') {
                        out.append('\f');
                    } else if (esc == 'n') {
                        out.append('\n');
                    } else if (esc == 'r') {
                        out.append('\r');
                    } else if (esc == 't') {
                        out.append('\t');
                    } else if (esc == 'u') {
                        out.append(parseUnicodeEscape());
                    } else {
                        throw new RuntimeException("invalid json escape");
                    }
                    continue;
                }
                out.append(ch);
            }
            throw new RuntimeException("unterminated json string");
        }

        private char parseUnicodeEscape() {
            if (i + 4 > n) {
                throw new RuntimeException("invalid json unicode escape");
            }
            int value = 0;
            int j = 0;
            while (j < 4) {
                char ch = text.charAt(i + j);
                int digit = Character.digit(ch, 16);
                if (digit < 0) {
                    throw new RuntimeException("invalid json unicode escape");
                }
                value = (value << 4) | digit;
                j += 1;
            }
            i += 4;
            return (char) value;
        }

        private Object parseNumber() {
            int start = i;
            if (text.charAt(i) == '-') {
                i += 1;
            }
            if (i >= n) {
                throw new RuntimeException("invalid json number");
            }
            if (text.charAt(i) == '0') {
                i += 1;
            } else {
                if (!isDigit(text.charAt(i))) {
                    throw new RuntimeException("invalid json number");
                }
                while (i < n && isDigit(text.charAt(i))) {
                    i += 1;
                }
            }
            boolean isFloat = false;
            if (i < n && text.charAt(i) == '.') {
                isFloat = true;
                i += 1;
                if (i >= n || !isDigit(text.charAt(i))) {
                    throw new RuntimeException("invalid json number");
                }
                while (i < n && isDigit(text.charAt(i))) {
                    i += 1;
                }
            }
            if (i < n && (text.charAt(i) == 'e' || text.charAt(i) == 'E')) {
                isFloat = true;
                i += 1;
                if (i < n && (text.charAt(i) == '+' || text.charAt(i) == '-')) {
                    i += 1;
                }
                if (i >= n || !isDigit(text.charAt(i))) {
                    throw new RuntimeException("invalid json exponent");
                }
                while (i < n && isDigit(text.charAt(i))) {
                    i += 1;
                }
            }
            String token = text.substring(start, i);
            try {
                if (isFloat) {
                    return Double.parseDouble(token);
                }
                return Long.parseLong(token);
            } catch (NumberFormatException ex) {
                throw new RuntimeException("invalid json number");
            }
        }

        private boolean isDigit(char ch) {
            return ch >= '0' && ch <= '9';
        }
    }

    // --- png/gif bridge (pytra-gen) ---

    static void pyWriteRGBPNG(Object path, Object width, Object height, Object pixels) {
        PngHelper.pyWriteRGBPNG(path, width, height, pixels);
    }

    static ArrayList<Long> pyGrayscalePalette() {
        return GifHelper.pyGrayscalePalette();
    }

    static void pySaveGif(Object path, Object width, Object height, Object frames, Object palette, Object delayCs, Object loop) {
        GifHelper.pySaveGif(path, width, height, frames, palette, delayCs, loop);
    }

    // ---- legacy java emitter helper compatibility ----
    static void __pytra_noop(Object... args) {
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

    static <T> java.util.ArrayList<T> __pytra_list_repeat(T value, long count) {
        java.util.ArrayList<T> out = new java.util.ArrayList<T>();
        long i = 0L;
        while (i < count) {
            out.add(value);
            i += 1L;
        }
        return out;
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
