// このファイルは自動生成です（Python -> Java native mode）。

// Java ネイティブ変換向け Python 互換ランタイム補助。

import java.io.ByteArrayOutputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.StringJoiner;
import java.util.zip.CRC32;
import java.util.zip.Deflater;

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

    static Object pyMathSqrt(Object v) {
        return Math.sqrt(pyToFloat(v));
    }

    static Object pyMathSin(Object v) {
        return Math.sin(pyToFloat(v));
    }

    static Object pyMathCos(Object v) {
        return Math.cos(pyToFloat(v));
    }

    static Object pyMathExp(Object v) {
        return Math.exp(pyToFloat(v));
    }

    static Object pyMathFloor(Object v) {
        return Math.floor(pyToFloat(v));
    }

    static Object pyMathPi() {
        return Math.PI;
    }

    // --- png/gif ---

    static byte[] pyToBytes(Object v) {
        if (v instanceof byte[] b) {
            return b;
        }
        if (v instanceof List<?> list) {
            byte[] out = new byte[list.size()];
            for (int i = 0; i < list.size(); i++) {
                out[i] = (byte) pyToInt(list.get(i));
            }
            return out;
        }
        if (v instanceof String s) {
            return s.getBytes(StandardCharsets.UTF_8);
        }
        throw new RuntimeException("cannot convert to bytes");
    }

    static byte[] pyChunk(String chunkType, byte[] data) {
        try {
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            int n = data.length;
            out.write((n >>> 24) & 0xff);
            out.write((n >>> 16) & 0xff);
            out.write((n >>> 8) & 0xff);
            out.write(n & 0xff);
            byte[] typeBytes = chunkType.getBytes(StandardCharsets.US_ASCII);
            out.write(typeBytes);
            out.write(data);
            CRC32 crc = new CRC32();
            crc.update(typeBytes);
            crc.update(data);
            long c = crc.getValue();
            out.write((int) ((c >>> 24) & 0xff));
            out.write((int) ((c >>> 16) & 0xff));
            out.write((int) ((c >>> 8) & 0xff));
            out.write((int) (c & 0xff));
            return out.toByteArray();
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

    static void pyWriteRGBPNG(Object path, Object width, Object height, Object pixels) {
        int w = pyToInt(width);
        int h = pyToInt(height);
        byte[] raw = pyToBytes(pixels);
        int expected = w * h * 3;
        if (raw.length != expected) {
            throw new RuntimeException("pixels length mismatch");
        }

        byte[] scan = new byte[h * (1 + w * 3)];
        int rowBytes = w * 3;
        int pos = 0;
        for (int y = 0; y < h; y++) {
            scan[pos++] = 0;
            int start = y * rowBytes;
            System.arraycopy(raw, start, scan, pos, rowBytes);
            pos += rowBytes;
        }

        Deflater deflater = new Deflater(6);
        deflater.setInput(scan);
        deflater.finish();
        byte[] buf = new byte[8192];
        ByteArrayOutputStream zOut = new ByteArrayOutputStream();
        while (!deflater.finished()) {
            int n = deflater.deflate(buf);
            zOut.write(buf, 0, n);
        }
        byte[] idat = zOut.toByteArray();

        byte[] ihdr = new byte[] {
                (byte) (w >>> 24), (byte) (w >>> 16), (byte) (w >>> 8), (byte) w,
                (byte) (h >>> 24), (byte) (h >>> 16), (byte) (h >>> 8), (byte) h,
                8, 2, 0, 0, 0
        };

        try (FileOutputStream fos = new FileOutputStream(pyToString(path))) {
            fos.write(new byte[] { (byte) 0x89, 'P', 'N', 'G', '\r', '\n', 0x1a, '\n' });
            fos.write(pyChunk("IHDR", ihdr));
            fos.write(pyChunk("IDAT", idat));
            fos.write(pyChunk("IEND", new byte[0]));
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

    static byte[] pyLzwEncode(byte[] data, int minCodeSize) {
        if (data.length == 0) {
            return new byte[0];
        }
        int clearCode = 1 << minCodeSize;
        int endCode = clearCode + 1;
        int codeSize = minCodeSize + 1;

        ByteArrayOutputStream out = new ByteArrayOutputStream();
        int bitBuffer = 0;
        int bitCount = 0;
        int[] codes = new int[data.length * 2 + 2];
        int k = 0;
        codes[k++] = clearCode;
        for (byte b : data) {
            codes[k++] = b & 0xff;
            codes[k++] = clearCode;
        }
        codes[k++] = endCode;
        for (int i = 0; i < k; i++) {
            int code = codes[i];
            bitBuffer |= (code << bitCount);
            bitCount += codeSize;
            while (bitCount >= 8) {
                out.write(bitBuffer & 0xff);
                bitBuffer >>>= 8;
                bitCount -= 8;
            }
        }
        if (bitCount > 0) {
            out.write(bitBuffer & 0xff);
        }
        return out.toByteArray();
    }

    static Object pyGrayscalePalette() {
        byte[] p = new byte[256 * 3];
        for (int i = 0; i < 256; i++) {
            p[i * 3] = (byte) i;
            p[i * 3 + 1] = (byte) i;
            p[i * 3 + 2] = (byte) i;
        }
        return p;
    }

    static void pySaveGif(Object path, Object width, Object height, Object frames, Object palette, Object delayCs, Object loop) {
        int w = pyToInt(width);
        int h = pyToInt(height);
        int frameBytes = w * h;
        byte[] pal = pyToBytes(palette);
        if (pal.length != 256 * 3) {
            throw new RuntimeException("palette must be 256*3 bytes");
        }
        int dcs = pyToInt(delayCs);
        int lp = pyToInt(loop);

        List<Object> frs = pyIter(frames);

        try (FileOutputStream fos = new FileOutputStream(pyToString(path))) {
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            out.write("GIF89a".getBytes(StandardCharsets.US_ASCII));
            out.write(w & 0xff);
            out.write((w >>> 8) & 0xff);
            out.write(h & 0xff);
            out.write((h >>> 8) & 0xff);
            out.write(0xF7);
            out.write(0);
            out.write(0);
            out.write(pal);
            out.write(new byte[] { 0x21, (byte) 0xFF, 0x0B });
            out.write("NETSCAPE2.0".getBytes(StandardCharsets.US_ASCII));
            out.write(new byte[] { 0x03, 0x01, (byte) (lp & 0xff), (byte) ((lp >>> 8) & 0xff), 0x00 });

            for (Object frAny : frs) {
                byte[] fr = pyToBytes(frAny);
                if (fr.length != frameBytes) {
                    throw new RuntimeException("frame size mismatch");
                }
                out.write(new byte[] { 0x21, (byte) 0xF9, 0x04, 0x00, (byte) (dcs & 0xff), (byte) ((dcs >>> 8) & 0xff), 0x00, 0x00 });
                out.write(0x2C);
                out.write(0);
                out.write(0);
                out.write(0);
                out.write(0);
                out.write(w & 0xff);
                out.write((w >>> 8) & 0xff);
                out.write(h & 0xff);
                out.write((h >>> 8) & 0xff);
                out.write(0x00);
                out.write(0x08);
                byte[] compressed = pyLzwEncode(fr, 8);
                int pos = 0;
                while (pos < compressed.length) {
                    int len = Math.min(255, compressed.length - pos);
                    out.write(len);
                    out.write(compressed, pos, len);
                    pos += len;
                }
                out.write(0x00);
            }
            out.write(0x3B);
            fos.write(out.toByteArray());
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }
}

class pytra_14_raymarching_light_cycle {
    static Object palette() {
        Object p = PyRuntime.pyBytearray(null);
        Object i = null;
        for (Object __pytra_it_1 : PyRuntime.pyRange(PyRuntime.pyToInt(0), PyRuntime.pyToInt(256), PyRuntime.pyToInt(1))) {
            i = __pytra_it_1;
            Object r = PyRuntime.pyToInt(PyRuntime.pyAdd(20, PyRuntime.pyMul(i, 0.9)));
            if (PyRuntime.pyBool(PyRuntime.pyGt(r, 255))) {
                r = 255;
            }
            Object g = PyRuntime.pyToInt(PyRuntime.pyAdd(10, PyRuntime.pyMul(i, 0.7)));
            if (PyRuntime.pyBool(PyRuntime.pyGt(g, 255))) {
                g = 255;
            }
            Object b = PyRuntime.pyToInt(PyRuntime.pyAdd(30, i));
            if (PyRuntime.pyBool(PyRuntime.pyGt(b, 255))) {
                b = 255;
            }
            ((java.util.List<Object>)p).add(r);
            ((java.util.List<Object>)p).add(g);
            ((java.util.List<Object>)p).add(b);
        }
        return PyRuntime.pyBytes(p);
    }
    static Object scene(Object x, Object y, Object light_x, Object light_y) {
        Object x1 = PyRuntime.pyAdd(x, 0.45);
        Object y1 = PyRuntime.pyAdd(y, 0.2);
        Object x2 = PyRuntime.pySub(x, 0.35);
        Object y2 = PyRuntime.pySub(y, 0.15);
        Object r1 = PyRuntime.pyMathSqrt(PyRuntime.pyAdd(PyRuntime.pyMul(x1, x1), PyRuntime.pyMul(y1, y1)));
        Object r2 = PyRuntime.pyMathSqrt(PyRuntime.pyAdd(PyRuntime.pyMul(x2, x2), PyRuntime.pyMul(y2, y2)));
        Object blob = PyRuntime.pyAdd(PyRuntime.pyMathExp(PyRuntime.pyMul(PyRuntime.pyMul(PyRuntime.pyNeg(7.0), r1), r1)), PyRuntime.pyMathExp(PyRuntime.pyMul(PyRuntime.pyMul(PyRuntime.pyNeg(8.0), r2), r2)));
        Object lx = PyRuntime.pySub(x, light_x);
        Object ly = PyRuntime.pySub(y, light_y);
        Object l = PyRuntime.pyMathSqrt(PyRuntime.pyAdd(PyRuntime.pyMul(lx, lx), PyRuntime.pyMul(ly, ly)));
        Object lit = PyRuntime.pyDiv(1.0, PyRuntime.pyAdd(1.0, PyRuntime.pyMul(PyRuntime.pyMul(3.5, l), l)));
        Object v = PyRuntime.pyToInt(PyRuntime.pyMul(PyRuntime.pyMul(PyRuntime.pyMul(255.0, blob), lit), 5.0));
        if (PyRuntime.pyBool(PyRuntime.pyLt(v, 0))) {
            return 0;
        }
        if (PyRuntime.pyBool(PyRuntime.pyGt(v, 255))) {
            return 255;
        }
        return v;
    }
    static Object run_14_raymarching_light_cycle() {
        Object w = 320;
        Object h = 240;
        Object frames_n = 84;
        Object out_path = "sample/out/14_raymarching_light_cycle.gif";
        Object start = PyRuntime.pyPerfCounter();
        Object frames = PyRuntime.pyList();
        Object t = null;
        for (Object __pytra_it_2 : PyRuntime.pyRange(PyRuntime.pyToInt(0), PyRuntime.pyToInt(frames_n), PyRuntime.pyToInt(1))) {
            t = __pytra_it_2;
            Object frame = PyRuntime.pyBytearray(PyRuntime.pyMul(w, h));
            Object a = PyRuntime.pyMul(PyRuntime.pyMul(PyRuntime.pyDiv(t, frames_n), PyRuntime.pyMathPi()), 2.0);
            Object light_x = PyRuntime.pyMul(0.75, PyRuntime.pyMathCos(a));
            Object light_y = PyRuntime.pyMul(0.55, PyRuntime.pyMathSin(PyRuntime.pyMul(a, 1.2)));
            Object i = 0;
            Object y = null;
            for (Object __pytra_it_3 : PyRuntime.pyRange(PyRuntime.pyToInt(0), PyRuntime.pyToInt(h), PyRuntime.pyToInt(1))) {
                y = __pytra_it_3;
                Object py = PyRuntime.pySub(PyRuntime.pyMul(PyRuntime.pyDiv(y, PyRuntime.pySub(h, 1)), 2.0), 1.0);
                Object x = null;
                for (Object __pytra_it_4 : PyRuntime.pyRange(PyRuntime.pyToInt(0), PyRuntime.pyToInt(w), PyRuntime.pyToInt(1))) {
                    x = __pytra_it_4;
                    Object px = PyRuntime.pySub(PyRuntime.pyMul(PyRuntime.pyDiv(x, PyRuntime.pySub(w, 1)), 2.0), 1.0);
                    PyRuntime.pySet(frame, i, scene(px, py, light_x, light_y));
                    i = PyRuntime.pyAdd(i, 1);
                }
            }
            ((java.util.List<Object>)frames).add(PyRuntime.pyBytes(frame));
        }
        PyRuntime.pySaveGif(out_path, w, h, frames, palette(), 3, 0);
        Object elapsed = PyRuntime.pySub(PyRuntime.pyPerfCounter(), start);
        PyRuntime.pyPrint("output:", out_path);
        PyRuntime.pyPrint("frames:", frames_n);
        PyRuntime.pyPrint("elapsed_sec:", elapsed);
        return null;
    }

    public static void main(String[] args) {
        run_14_raymarching_light_cycle();
    }
}
