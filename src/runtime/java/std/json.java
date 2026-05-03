import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

public final class json {
    private json() {
    }

    public static final class JsonValue {
        public Object raw;

        public JsonValue(Object raw) {
            this.raw = raw;
        }

        public String as_str() {
            return raw instanceof String ? (String) raw : null;
        }

        public Long as_int() {
            if (raw instanceof Long) {
                return (Long) raw;
            }
            if (raw instanceof Integer) {
                return Long.valueOf(((Integer) raw).longValue());
            }
            return null;
        }

        public Double as_float() {
            if (raw instanceof Double) {
                return (Double) raw;
            }
            if (raw instanceof Long) {
                return Double.valueOf(((Long) raw).doubleValue());
            }
            return null;
        }

        public Boolean as_bool() {
            return raw instanceof Boolean ? (Boolean) raw : null;
        }

        public JsonObj as_obj() {
            return raw instanceof HashMap<?, ?> ? new JsonObj((HashMap<String, Object>) raw) : null;
        }

        public JsonArr as_arr() {
            return raw instanceof ArrayList<?> ? new JsonArr((ArrayList<Object>) raw) : null;
        }
    }

    public static final class JsonArr {
        public ArrayList<Object> raw;

        public JsonArr(ArrayList<Object> raw) {
            this.raw = raw;
        }

        public JsonValue get(long index) {
            int i = (int) index;
            if (i < 0 || i >= raw.size()) {
                return null;
            }
            return new JsonValue(raw.get(i));
        }

        public String get_str(long index) {
            JsonValue value = get(index);
            return value == null ? null : value.as_str();
        }

        public Long get_int(long index) {
            JsonValue value = get(index);
            return value == null ? null : value.as_int();
        }

        public Double get_float(long index) {
            JsonValue value = get(index);
            return value == null ? null : value.as_float();
        }

        public Boolean get_bool(long index) {
            JsonValue value = get(index);
            return value == null ? null : value.as_bool();
        }

        public JsonArr get_arr(long index) {
            JsonValue value = get(index);
            return value == null ? null : value.as_arr();
        }

        public JsonObj get_obj(long index) {
            JsonValue value = get(index);
            return value == null ? null : value.as_obj();
        }
    }

    public static final class JsonObj {
        public HashMap<String, Object> raw;

        public JsonObj(HashMap<String, Object> raw) {
            this.raw = raw;
        }

        public JsonValue get(String key) {
            if (!raw.containsKey(key)) {
                return null;
            }
            return new JsonValue(raw.get(key));
        }

        public String get_str(String key) {
            JsonValue value = get(key);
            return value == null ? null : value.as_str();
        }

        public Long get_int(String key) {
            JsonValue value = get(key);
            return value == null ? null : value.as_int();
        }

        public Double get_float(String key) {
            JsonValue value = get(key);
            return value == null ? null : value.as_float();
        }

        public Boolean get_bool(String key) {
            JsonValue value = get(key);
            return value == null ? null : value.as_bool();
        }

        public JsonArr get_arr(String key) {
            JsonValue value = get(key);
            return value == null ? null : value.as_arr();
        }

        public JsonObj get_obj(String key) {
            JsonValue value = get(key);
            return value == null ? null : value.as_obj();
        }
    }

    private static final class Parser {
        private final String text;
        private int index = 0;

        Parser(String text) {
            this.text = text;
        }

        Object parse() {
            skipWs();
            Object value = parseValue();
            skipWs();
            if (index != text.length()) {
                throw new RuntimeException("invalid json: trailing characters");
            }
            return value;
        }

        private void skipWs() {
            while (index < text.length()) {
                char ch = text.charAt(index);
                if (ch != ' ' && ch != '\n' && ch != '\r' && ch != '\t') {
                    return;
                }
                index += 1;
            }
        }

        private Object parseValue() {
            if (index >= text.length()) {
                throw new RuntimeException("invalid json: unexpected end");
            }
            char ch = text.charAt(index);
            if (ch == '{') {
                return parseObject();
            }
            if (ch == '[') {
                return parseArray();
            }
            if (ch == '"') {
                return parseString();
            }
            if (text.startsWith("true", index)) {
                index += 4;
                return true;
            }
            if (text.startsWith("false", index)) {
                index += 5;
                return false;
            }
            if (text.startsWith("null", index)) {
                index += 4;
                return null;
            }
            return parseNumber();
        }

        private HashMap<String, Object> parseObject() {
            HashMap<String, Object> out = new HashMap<>();
            index += 1;
            skipWs();
            if (index < text.length() && text.charAt(index) == '}') {
                index += 1;
                return out;
            }
            while (true) {
                skipWs();
                String key = parseString();
                skipWs();
                if (index >= text.length() || text.charAt(index) != ':') {
                    throw new RuntimeException("invalid json object");
                }
                index += 1;
                skipWs();
                out.put(key, parseValue());
                skipWs();
                if (index >= text.length()) {
                    throw new RuntimeException("invalid json object");
                }
                char ch = text.charAt(index);
                index += 1;
                if (ch == '}') {
                    return out;
                }
                if (ch != ',') {
                    throw new RuntimeException("invalid json object separator");
                }
            }
        }

        private ArrayList<Object> parseArray() {
            ArrayList<Object> out = new ArrayList<>();
            index += 1;
            skipWs();
            if (index < text.length() && text.charAt(index) == ']') {
                index += 1;
                return out;
            }
            while (true) {
                skipWs();
                out.add(parseValue());
                skipWs();
                if (index >= text.length()) {
                    throw new RuntimeException("invalid json array");
                }
                char ch = text.charAt(index);
                index += 1;
                if (ch == ']') {
                    return out;
                }
                if (ch != ',') {
                    throw new RuntimeException("invalid json array separator");
                }
            }
        }

        private String parseString() {
            if (index >= text.length() || text.charAt(index) != '"') {
                throw new RuntimeException("invalid json string");
            }
            index += 1;
            StringBuilder out = new StringBuilder();
            while (index < text.length()) {
                char ch = text.charAt(index);
                index += 1;
                if (ch == '"') {
                    return out.toString();
                }
                if (ch != '\\') {
                    out.append(ch);
                    continue;
                }
                if (index >= text.length()) {
                    throw new RuntimeException("invalid json escape");
                }
                char esc = text.charAt(index);
                index += 1;
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
                    if (index + 4 > text.length()) {
                        throw new RuntimeException("invalid json unicode escape");
                    }
                    String hex = text.substring(index, index + 4);
                    out.append((char) Integer.parseInt(hex, 16));
                    index += 4;
                } else {
                    throw new RuntimeException("invalid json escape");
                }
            }
            throw new RuntimeException("invalid json string");
        }

        private Object parseNumber() {
            int start = index;
            if (text.charAt(index) == '-') {
                index += 1;
            }
            while (index < text.length() && Character.isDigit(text.charAt(index))) {
                index += 1;
            }
            boolean isFloat = false;
            if (index < text.length() && text.charAt(index) == '.') {
                isFloat = true;
                index += 1;
                while (index < text.length() && Character.isDigit(text.charAt(index))) {
                    index += 1;
                }
            }
            if (index < text.length()) {
                char ch = text.charAt(index);
                if (ch == 'e' || ch == 'E') {
                    isFloat = true;
                    index += 1;
                    if (index < text.length() && (text.charAt(index) == '+' || text.charAt(index) == '-')) {
                        index += 1;
                    }
                    while (index < text.length() && Character.isDigit(text.charAt(index))) {
                        index += 1;
                    }
                }
            }
            String token = text.substring(start, index);
            return isFloat ? Double.valueOf(token) : Long.valueOf(token);
        }
    }

    public static JsonValue loads(String text) {
        return new JsonValue(new Parser(text).parse());
    }

    public static JsonArr loads_arr(String text) {
        Object value = new Parser(text).parse();
        return value instanceof ArrayList<?> ? new JsonArr((ArrayList<Object>) value) : null;
    }

    public static JsonObj loads_obj(String text) {
        Object value = new Parser(text).parse();
        return value instanceof HashMap<?, ?> ? new JsonObj((HashMap<String, Object>) value) : null;
    }

    public static String dumps(Object value) {
        return dumps(value, true, null, null);
    }

    public static String dumps(Object value, boolean ensureAscii, Object indent, Object separators) {
        Integer indentValue = null;
        if (indent instanceof Long) {
            indentValue = Integer.valueOf(((Long) indent).intValue());
        } else if (indent instanceof Integer) {
            indentValue = (Integer) indent;
        }
        return serialize(unwrap(value), ensureAscii, indentValue, 0);
    }

    private static Object unwrap(Object value) {
        if (value instanceof JsonValue) {
            return ((JsonValue) value).raw;
        }
        if (value instanceof JsonArr) {
            return ((JsonArr) value).raw;
        }
        if (value instanceof JsonObj) {
            return ((JsonObj) value).raw;
        }
        return value;
    }

    private static String serialize(Object value, boolean ensureAscii, Integer indent, int depth) {
        if (value == null) {
            return "null";
        }
        if (value instanceof Boolean) {
            return ((Boolean) value).booleanValue() ? "true" : "false";
        }
        if (value instanceof Long || value instanceof Integer) {
            return String.valueOf(value);
        }
        if (value instanceof Double || value instanceof Float) {
            double number = ((Number) value).doubleValue();
            if (Math.rint(number) == number) {
                return String.valueOf((long) number);
            }
            return String.valueOf(number);
        }
        if (value instanceof String) {
            return quote((String) value, ensureAscii);
        }
        if (value instanceof ArrayList<?>) {
            ArrayList<?> items = (ArrayList<?>) value;
            ArrayList<String> parts = new ArrayList<>();
            for (Object item : items) {
                parts.add(serialize(unwrap(item), ensureAscii, indent, depth + 1));
            }
            if (indent != null && indent.intValue() > 0) {
                String pad = " ".repeat(indent.intValue() * (depth + 1));
                String closePad = " ".repeat(indent.intValue() * depth);
                return "[\n" + String.join(",\n", prefix(parts, pad)) + "\n" + closePad + "]";
            }
            return "[" + String.join(", ", parts) + "]";
        }
        if (value instanceof Map<?, ?>) {
            ArrayList<String> parts = new ArrayList<>();
            for (Map.Entry<?, ?> entry : ((Map<?, ?>) value).entrySet()) {
                parts.add(quote(String.valueOf(entry.getKey()), ensureAscii) + ": " + serialize(unwrap(entry.getValue()), ensureAscii, indent, depth + 1));
            }
            if (indent != null && indent.intValue() > 0) {
                String pad = " ".repeat(indent.intValue() * (depth + 1));
                String closePad = " ".repeat(indent.intValue() * depth);
                return "{\n" + String.join(",\n", prefix(parts, pad)) + "\n" + closePad + "}";
            }
            return "{" + String.join(", ", parts) + "}";
        }
        return quote(String.valueOf(value), ensureAscii);
    }

    private static ArrayList<String> prefix(ArrayList<String> parts, String pad) {
        ArrayList<String> out = new ArrayList<>();
        for (String part : parts) {
            out.add(pad + part);
        }
        return out;
    }

    private static String quote(String value, boolean ensureAscii) {
        StringBuilder out = new StringBuilder();
        out.append('"');
        int i = 0;
        while (i < value.length()) {
            char ch = value.charAt(i);
            if (ch == '"' || ch == '\\') {
                out.append('\\').append(ch);
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
            } else if (ensureAscii && ch > 0x7F) {
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
}
