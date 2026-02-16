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

class pytra_16_glass_sculpture_chaos {
    static Object clamp01(Object v) {
        if (PyRuntime.pyBool(PyRuntime.pyLt(v, 0.0))) {
            return 0.0;
        }
        if (PyRuntime.pyBool(PyRuntime.pyGt(v, 1.0))) {
            return 1.0;
        }
        return v;
    }
    static Object dot(Object ax, Object ay, Object az, Object bx, Object by, Object bz) {
        return PyRuntime.pyAdd(PyRuntime.pyAdd(PyRuntime.pyMul(ax, bx), PyRuntime.pyMul(ay, by)), PyRuntime.pyMul(az, bz));
    }
    static Object length(Object x, Object y, Object z) {
        return PyRuntime.pyMathSqrt(PyRuntime.pyAdd(PyRuntime.pyAdd(PyRuntime.pyMul(x, x), PyRuntime.pyMul(y, y)), PyRuntime.pyMul(z, z)));
    }
    static Object normalize(Object x, Object y, Object z) {
        Object l = length(x, y, z);
        if (PyRuntime.pyBool(PyRuntime.pyLt(l, 1e-09))) {
            return PyRuntime.pyList(0.0, 0.0, 0.0);
        }
        return PyRuntime.pyList(PyRuntime.pyDiv(x, l), PyRuntime.pyDiv(y, l), PyRuntime.pyDiv(z, l));
    }
    static Object reflect(Object ix, Object iy, Object iz, Object nx, Object ny, Object nz) {
        Object d = PyRuntime.pyMul(dot(ix, iy, iz, nx, ny, nz), 2.0);
        return PyRuntime.pyList(PyRuntime.pySub(ix, PyRuntime.pyMul(d, nx)), PyRuntime.pySub(iy, PyRuntime.pyMul(d, ny)), PyRuntime.pySub(iz, PyRuntime.pyMul(d, nz)));
    }
    static Object refract(Object ix, Object iy, Object iz, Object nx, Object ny, Object nz, Object eta) {
        Object cosi = PyRuntime.pyNeg(dot(ix, iy, iz, nx, ny, nz));
        Object sint2 = PyRuntime.pyMul(PyRuntime.pyMul(eta, eta), PyRuntime.pySub(1.0, PyRuntime.pyMul(cosi, cosi)));
        if (PyRuntime.pyBool(PyRuntime.pyGt(sint2, 1.0))) {
            return reflect(ix, iy, iz, nx, ny, nz);
        }
        Object cost = PyRuntime.pyMathSqrt(PyRuntime.pySub(1.0, sint2));
        Object k = PyRuntime.pySub(PyRuntime.pyMul(eta, cosi), cost);
        return PyRuntime.pyList(PyRuntime.pyAdd(PyRuntime.pyMul(eta, ix), PyRuntime.pyMul(k, nx)), PyRuntime.pyAdd(PyRuntime.pyMul(eta, iy), PyRuntime.pyMul(k, ny)), PyRuntime.pyAdd(PyRuntime.pyMul(eta, iz), PyRuntime.pyMul(k, nz)));
    }
    static Object schlick(Object cos_theta, Object f0) {
        Object m = PyRuntime.pySub(1.0, cos_theta);
        return PyRuntime.pyAdd(f0, PyRuntime.pyMul(PyRuntime.pySub(1.0, f0), PyRuntime.pyMul(PyRuntime.pyMul(PyRuntime.pyMul(PyRuntime.pyMul(m, m), m), m), m)));
    }
    static Object sky_color(Object dx, Object dy, Object dz, Object tphase) {
        Object t = PyRuntime.pyMul(0.5, PyRuntime.pyAdd(dy, 1.0));
        Object r = PyRuntime.pyAdd(0.06, PyRuntime.pyMul(0.2, t));
        Object g = PyRuntime.pyAdd(0.1, PyRuntime.pyMul(0.25, t));
        Object b = PyRuntime.pyAdd(0.16, PyRuntime.pyMul(0.45, t));
        Object band = PyRuntime.pyAdd(0.5, PyRuntime.pyMul(0.5, PyRuntime.pyMathSin(PyRuntime.pyAdd(PyRuntime.pyAdd(PyRuntime.pyMul(8.0, dx), PyRuntime.pyMul(6.0, dz)), tphase))));
        r = PyRuntime.pyAdd(r, PyRuntime.pyMul(0.08, band));
        g = PyRuntime.pyAdd(g, PyRuntime.pyMul(0.05, band));
        b = PyRuntime.pyAdd(b, PyRuntime.pyMul(0.12, band));
        return PyRuntime.pyList(clamp01(r), clamp01(g), clamp01(b));
    }
    static Object sphere_intersect(Object ox, Object oy, Object oz, Object dx, Object dy, Object dz, Object cx, Object cy, Object cz, Object radius) {
        Object lx = PyRuntime.pySub(ox, cx);
        Object ly = PyRuntime.pySub(oy, cy);
        Object lz = PyRuntime.pySub(oz, cz);
        Object b = PyRuntime.pyAdd(PyRuntime.pyAdd(PyRuntime.pyMul(lx, dx), PyRuntime.pyMul(ly, dy)), PyRuntime.pyMul(lz, dz));
        Object c = PyRuntime.pySub(PyRuntime.pyAdd(PyRuntime.pyAdd(PyRuntime.pyMul(lx, lx), PyRuntime.pyMul(ly, ly)), PyRuntime.pyMul(lz, lz)), PyRuntime.pyMul(radius, radius));
        Object h = PyRuntime.pySub(PyRuntime.pyMul(b, b), c);
        if (PyRuntime.pyBool(PyRuntime.pyLt(h, 0.0))) {
            return PyRuntime.pyNeg(1.0);
        }
        Object s = PyRuntime.pyMathSqrt(h);
        Object t0 = PyRuntime.pySub(PyRuntime.pyNeg(b), s);
        if (PyRuntime.pyBool(PyRuntime.pyGt(t0, 0.0001))) {
            return t0;
        }
        Object t1 = PyRuntime.pyAdd(PyRuntime.pyNeg(b), s);
        if (PyRuntime.pyBool(PyRuntime.pyGt(t1, 0.0001))) {
            return t1;
        }
        return PyRuntime.pyNeg(1.0);
    }
    static Object palette_332() {
        Object p = PyRuntime.pyBytearray(PyRuntime.pyMul(256, 3));
        Object i = null;
        for (Object __pytra_it_1 : PyRuntime.pyRange(PyRuntime.pyToInt(0), PyRuntime.pyToInt(256), PyRuntime.pyToInt(1))) {
            i = __pytra_it_1;
            Object r = PyRuntime.pyBitAnd(PyRuntime.pyRShift(i, 5), 7);
            Object g = PyRuntime.pyBitAnd(PyRuntime.pyRShift(i, 2), 7);
            Object b = PyRuntime.pyBitAnd(i, 3);
            PyRuntime.pySet(p, PyRuntime.pyAdd(PyRuntime.pyMul(i, 3), 0), PyRuntime.pyToInt(PyRuntime.pyDiv(PyRuntime.pyMul(255, r), 7)));
            PyRuntime.pySet(p, PyRuntime.pyAdd(PyRuntime.pyMul(i, 3), 1), PyRuntime.pyToInt(PyRuntime.pyDiv(PyRuntime.pyMul(255, g), 7)));
            PyRuntime.pySet(p, PyRuntime.pyAdd(PyRuntime.pyMul(i, 3), 2), PyRuntime.pyToInt(PyRuntime.pyDiv(PyRuntime.pyMul(255, b), 3)));
        }
        return PyRuntime.pyBytes(p);
    }
    static Object quantize_332(Object r, Object g, Object b) {
        Object rr = PyRuntime.pyToInt(PyRuntime.pyMul(clamp01(r), 255.0));
        Object gg = PyRuntime.pyToInt(PyRuntime.pyMul(clamp01(g), 255.0));
        Object bb = PyRuntime.pyToInt(PyRuntime.pyMul(clamp01(b), 255.0));
        return PyRuntime.pyAdd(PyRuntime.pyAdd(PyRuntime.pyLShift(PyRuntime.pyRShift(rr, 5), 5), PyRuntime.pyLShift(PyRuntime.pyRShift(gg, 5), 2)), PyRuntime.pyRShift(bb, 6));
    }
    static Object render_frame(Object width, Object height, Object frame_id, Object frames_n) {
        Object t = PyRuntime.pyDiv(frame_id, frames_n);
        Object tphase = PyRuntime.pyMul(PyRuntime.pyMul(2.0, PyRuntime.pyMathPi()), t);
        Object cam_r = 3.0;
        Object cam_x = PyRuntime.pyMul(cam_r, PyRuntime.pyMathCos(PyRuntime.pyMul(tphase, 0.9)));
        Object cam_y = PyRuntime.pyAdd(1.1, PyRuntime.pyMul(0.25, PyRuntime.pyMathSin(PyRuntime.pyMul(tphase, 0.6))));
        Object cam_z = PyRuntime.pyMul(cam_r, PyRuntime.pyMathSin(PyRuntime.pyMul(tphase, 0.9)));
        Object look_x = 0.0;
        Object look_y = 0.35;
        Object look_z = 0.0;
        Object __pytra_tuple_2 = normalize(PyRuntime.pySub(look_x, cam_x), PyRuntime.pySub(look_y, cam_y), PyRuntime.pySub(look_z, cam_z));
        Object fwd_x = PyRuntime.pyGet(__pytra_tuple_2, 0);
        Object fwd_y = PyRuntime.pyGet(__pytra_tuple_2, 1);
        Object fwd_z = PyRuntime.pyGet(__pytra_tuple_2, 2);
        Object __pytra_tuple_3 = normalize(fwd_z, 0.0, PyRuntime.pyNeg(fwd_x));
        Object right_x = PyRuntime.pyGet(__pytra_tuple_3, 0);
        Object right_y = PyRuntime.pyGet(__pytra_tuple_3, 1);
        Object right_z = PyRuntime.pyGet(__pytra_tuple_3, 2);
        Object __pytra_tuple_4 = normalize(PyRuntime.pySub(PyRuntime.pyMul(right_y, fwd_z), PyRuntime.pyMul(right_z, fwd_y)), PyRuntime.pySub(PyRuntime.pyMul(right_z, fwd_x), PyRuntime.pyMul(right_x, fwd_z)), PyRuntime.pySub(PyRuntime.pyMul(right_x, fwd_y), PyRuntime.pyMul(right_y, fwd_x)));
        Object up_x = PyRuntime.pyGet(__pytra_tuple_4, 0);
        Object up_y = PyRuntime.pyGet(__pytra_tuple_4, 1);
        Object up_z = PyRuntime.pyGet(__pytra_tuple_4, 2);
        Object s0x = PyRuntime.pyMul(0.9, PyRuntime.pyMathCos(PyRuntime.pyMul(1.3, tphase)));
        Object s0y = PyRuntime.pyAdd(0.15, PyRuntime.pyMul(0.35, PyRuntime.pyMathSin(PyRuntime.pyMul(1.7, tphase))));
        Object s0z = PyRuntime.pyMul(0.9, PyRuntime.pyMathSin(PyRuntime.pyMul(1.3, tphase)));
        Object s1x = PyRuntime.pyMul(1.2, PyRuntime.pyMathCos(PyRuntime.pyAdd(PyRuntime.pyMul(1.3, tphase), 2.094)));
        Object s1y = PyRuntime.pyAdd(0.1, PyRuntime.pyMul(0.4, PyRuntime.pyMathSin(PyRuntime.pyAdd(PyRuntime.pyMul(1.1, tphase), 0.8))));
        Object s1z = PyRuntime.pyMul(1.2, PyRuntime.pyMathSin(PyRuntime.pyAdd(PyRuntime.pyMul(1.3, tphase), 2.094)));
        Object s2x = PyRuntime.pyMul(1.0, PyRuntime.pyMathCos(PyRuntime.pyAdd(PyRuntime.pyMul(1.3, tphase), 4.188)));
        Object s2y = PyRuntime.pyAdd(0.2, PyRuntime.pyMul(0.3, PyRuntime.pyMathSin(PyRuntime.pyAdd(PyRuntime.pyMul(1.5, tphase), 1.9))));
        Object s2z = PyRuntime.pyMul(1.0, PyRuntime.pyMathSin(PyRuntime.pyAdd(PyRuntime.pyMul(1.3, tphase), 4.188)));
        Object lr = 0.35;
        Object lx = PyRuntime.pyMul(2.4, PyRuntime.pyMathCos(PyRuntime.pyMul(tphase, 1.8)));
        Object ly = PyRuntime.pyAdd(1.8, PyRuntime.pyMul(0.8, PyRuntime.pyMathSin(PyRuntime.pyMul(tphase, 1.2))));
        Object lz = PyRuntime.pyMul(2.4, PyRuntime.pyMathSin(PyRuntime.pyMul(tphase, 1.8)));
        Object frame = PyRuntime.pyBytearray(PyRuntime.pyMul(width, height));
        Object aspect = PyRuntime.pyDiv(width, height);
        Object fov = 1.25;
        Object i = 0;
        Object py = null;
        for (Object __pytra_it_5 : PyRuntime.pyRange(PyRuntime.pyToInt(0), PyRuntime.pyToInt(height), PyRuntime.pyToInt(1))) {
            py = __pytra_it_5;
            Object sy = PyRuntime.pySub(1.0, PyRuntime.pyDiv(PyRuntime.pyMul(2.0, PyRuntime.pyAdd(py, 0.5)), height));
            Object px = null;
            for (Object __pytra_it_6 : PyRuntime.pyRange(PyRuntime.pyToInt(0), PyRuntime.pyToInt(width), PyRuntime.pyToInt(1))) {
                px = __pytra_it_6;
                Object sx = PyRuntime.pyMul(PyRuntime.pySub(PyRuntime.pyDiv(PyRuntime.pyMul(2.0, PyRuntime.pyAdd(px, 0.5)), width), 1.0), aspect);
                Object rx = PyRuntime.pyAdd(fwd_x, PyRuntime.pyMul(fov, PyRuntime.pyAdd(PyRuntime.pyMul(sx, right_x), PyRuntime.pyMul(sy, up_x))));
                Object ry = PyRuntime.pyAdd(fwd_y, PyRuntime.pyMul(fov, PyRuntime.pyAdd(PyRuntime.pyMul(sx, right_y), PyRuntime.pyMul(sy, up_y))));
                Object rz = PyRuntime.pyAdd(fwd_z, PyRuntime.pyMul(fov, PyRuntime.pyAdd(PyRuntime.pyMul(sx, right_z), PyRuntime.pyMul(sy, up_z))));
                Object __pytra_tuple_7 = normalize(rx, ry, rz);
                Object dx = PyRuntime.pyGet(__pytra_tuple_7, 0);
                Object dy = PyRuntime.pyGet(__pytra_tuple_7, 1);
                Object dz = PyRuntime.pyGet(__pytra_tuple_7, 2);
                Object best_t = 1000000000.0;
                Object hit_kind = 0;
                Object r = 0.0;
                Object g = 0.0;
                Object b = 0.0;
                if (PyRuntime.pyBool(PyRuntime.pyLt(dy, PyRuntime.pyNeg(1e-06)))) {
                    Object tf = PyRuntime.pyDiv(PyRuntime.pySub(PyRuntime.pyNeg(1.2), cam_y), dy);
                    if (PyRuntime.pyBool((PyRuntime.pyBool(PyRuntime.pyGt(tf, 0.0001)) && PyRuntime.pyBool(PyRuntime.pyLt(tf, best_t))))) {
                        best_t = tf;
                        hit_kind = 1;
                    }
                }
                Object t0 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s0x, s0y, s0z, 0.65);
                if (PyRuntime.pyBool((PyRuntime.pyBool(PyRuntime.pyGt(t0, 0.0)) && PyRuntime.pyBool(PyRuntime.pyLt(t0, best_t))))) {
                    best_t = t0;
                    hit_kind = 2;
                }
                Object t1 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s1x, s1y, s1z, 0.72);
                if (PyRuntime.pyBool((PyRuntime.pyBool(PyRuntime.pyGt(t1, 0.0)) && PyRuntime.pyBool(PyRuntime.pyLt(t1, best_t))))) {
                    best_t = t1;
                    hit_kind = 3;
                }
                Object t2 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s2x, s2y, s2z, 0.58);
                if (PyRuntime.pyBool((PyRuntime.pyBool(PyRuntime.pyGt(t2, 0.0)) && PyRuntime.pyBool(PyRuntime.pyLt(t2, best_t))))) {
                    best_t = t2;
                    hit_kind = 4;
                }
                if (PyRuntime.pyBool(PyRuntime.pyEq(hit_kind, 0))) {
                    Object __pytra_tuple_8 = sky_color(dx, dy, dz, tphase);
                    r = PyRuntime.pyGet(__pytra_tuple_8, 0);
                    g = PyRuntime.pyGet(__pytra_tuple_8, 1);
                    b = PyRuntime.pyGet(__pytra_tuple_8, 2);
                } else {
                    if (PyRuntime.pyBool(PyRuntime.pyEq(hit_kind, 1))) {
                        Object hx = PyRuntime.pyAdd(cam_x, PyRuntime.pyMul(best_t, dx));
                        Object hz = PyRuntime.pyAdd(cam_z, PyRuntime.pyMul(best_t, dz));
                        Object cx = PyRuntime.pyToInt(PyRuntime.pyMathFloor(PyRuntime.pyMul(hx, 2.0)));
                        Object cz = PyRuntime.pyToInt(PyRuntime.pyMathFloor(PyRuntime.pyMul(hz, 2.0)));
                        Object checker = PyRuntime.pyTernary(PyRuntime.pyBool(PyRuntime.pyEq(PyRuntime.pyMod(PyRuntime.pyAdd(cx, cz), 2), 0)), 0, 1);
                        Object base_r = PyRuntime.pyTernary(PyRuntime.pyBool(PyRuntime.pyEq(checker, 0)), 0.1, 0.04);
                        Object base_g = PyRuntime.pyTernary(PyRuntime.pyBool(PyRuntime.pyEq(checker, 0)), 0.11, 0.05);
                        Object base_b = PyRuntime.pyTernary(PyRuntime.pyBool(PyRuntime.pyEq(checker, 0)), 0.13, 0.08);
                        Object lxv = PyRuntime.pySub(lx, hx);
                        Object lyv = PyRuntime.pySub(ly, PyRuntime.pyNeg(1.2));
                        Object lzv = PyRuntime.pySub(lz, hz);
                        Object __pytra_tuple_9 = normalize(lxv, lyv, lzv);
                        Object ldx = PyRuntime.pyGet(__pytra_tuple_9, 0);
                        Object ldy = PyRuntime.pyGet(__pytra_tuple_9, 1);
                        Object ldz = PyRuntime.pyGet(__pytra_tuple_9, 2);
                        Object ndotl = PyRuntime.pyMax(ldy, 0.0);
                        Object ldist2 = PyRuntime.pyAdd(PyRuntime.pyAdd(PyRuntime.pyMul(lxv, lxv), PyRuntime.pyMul(lyv, lyv)), PyRuntime.pyMul(lzv, lzv));
                        Object glow = PyRuntime.pyDiv(8.0, PyRuntime.pyAdd(1.0, ldist2));
                        r = PyRuntime.pyAdd(PyRuntime.pyAdd(base_r, PyRuntime.pyMul(0.8, glow)), PyRuntime.pyMul(0.2, ndotl));
                        g = PyRuntime.pyAdd(PyRuntime.pyAdd(base_g, PyRuntime.pyMul(0.5, glow)), PyRuntime.pyMul(0.18, ndotl));
                        b = PyRuntime.pyAdd(PyRuntime.pyAdd(base_b, PyRuntime.pyMul(1.0, glow)), PyRuntime.pyMul(0.24, ndotl));
                    } else {
                        Object cx = 0.0;
                        Object cy = 0.0;
                        Object cz = 0.0;
                        Object rad = 1.0;
                        if (PyRuntime.pyBool(PyRuntime.pyEq(hit_kind, 2))) {
                            cx = s0x;
                            cy = s0y;
                            cz = s0z;
                            rad = 0.65;
                        } else {
                            if (PyRuntime.pyBool(PyRuntime.pyEq(hit_kind, 3))) {
                                cx = s1x;
                                cy = s1y;
                                cz = s1z;
                                rad = 0.72;
                            } else {
                                cx = s2x;
                                cy = s2y;
                                cz = s2z;
                                rad = 0.58;
                            }
                        }
                        Object hx = PyRuntime.pyAdd(cam_x, PyRuntime.pyMul(best_t, dx));
                        Object hy = PyRuntime.pyAdd(cam_y, PyRuntime.pyMul(best_t, dy));
                        Object hz = PyRuntime.pyAdd(cam_z, PyRuntime.pyMul(best_t, dz));
                        Object __pytra_tuple_10 = normalize(PyRuntime.pyDiv(PyRuntime.pySub(hx, cx), rad), PyRuntime.pyDiv(PyRuntime.pySub(hy, cy), rad), PyRuntime.pyDiv(PyRuntime.pySub(hz, cz), rad));
                        Object nx = PyRuntime.pyGet(__pytra_tuple_10, 0);
                        Object ny = PyRuntime.pyGet(__pytra_tuple_10, 1);
                        Object nz = PyRuntime.pyGet(__pytra_tuple_10, 2);
                        Object __pytra_tuple_11 = reflect(dx, dy, dz, nx, ny, nz);
                        Object rdx = PyRuntime.pyGet(__pytra_tuple_11, 0);
                        Object rdy = PyRuntime.pyGet(__pytra_tuple_11, 1);
                        Object rdz = PyRuntime.pyGet(__pytra_tuple_11, 2);
                        Object __pytra_tuple_12 = refract(dx, dy, dz, nx, ny, nz, PyRuntime.pyDiv(1.0, 1.45));
                        Object tdx = PyRuntime.pyGet(__pytra_tuple_12, 0);
                        Object tdy = PyRuntime.pyGet(__pytra_tuple_12, 1);
                        Object tdz = PyRuntime.pyGet(__pytra_tuple_12, 2);
                        Object __pytra_tuple_13 = sky_color(rdx, rdy, rdz, tphase);
                        Object sr = PyRuntime.pyGet(__pytra_tuple_13, 0);
                        Object sg = PyRuntime.pyGet(__pytra_tuple_13, 1);
                        Object sb = PyRuntime.pyGet(__pytra_tuple_13, 2);
                        Object __pytra_tuple_14 = sky_color(tdx, tdy, tdz, PyRuntime.pyAdd(tphase, 0.8));
                        Object tr = PyRuntime.pyGet(__pytra_tuple_14, 0);
                        Object tg = PyRuntime.pyGet(__pytra_tuple_14, 1);
                        Object tb = PyRuntime.pyGet(__pytra_tuple_14, 2);
                        Object cosi = PyRuntime.pyMax(PyRuntime.pyNeg(PyRuntime.pyAdd(PyRuntime.pyAdd(PyRuntime.pyMul(dx, nx), PyRuntime.pyMul(dy, ny)), PyRuntime.pyMul(dz, nz))), 0.0);
                        Object fr = schlick(cosi, 0.04);
                        r = PyRuntime.pyAdd(PyRuntime.pyMul(tr, PyRuntime.pySub(1.0, fr)), PyRuntime.pyMul(sr, fr));
                        g = PyRuntime.pyAdd(PyRuntime.pyMul(tg, PyRuntime.pySub(1.0, fr)), PyRuntime.pyMul(sg, fr));
                        b = PyRuntime.pyAdd(PyRuntime.pyMul(tb, PyRuntime.pySub(1.0, fr)), PyRuntime.pyMul(sb, fr));
                        Object lxv = PyRuntime.pySub(lx, hx);
                        Object lyv = PyRuntime.pySub(ly, hy);
                        Object lzv = PyRuntime.pySub(lz, hz);
                        Object __pytra_tuple_15 = normalize(lxv, lyv, lzv);
                        Object ldx = PyRuntime.pyGet(__pytra_tuple_15, 0);
                        Object ldy = PyRuntime.pyGet(__pytra_tuple_15, 1);
                        Object ldz = PyRuntime.pyGet(__pytra_tuple_15, 2);
                        Object ndotl = PyRuntime.pyMax(PyRuntime.pyAdd(PyRuntime.pyAdd(PyRuntime.pyMul(nx, ldx), PyRuntime.pyMul(ny, ldy)), PyRuntime.pyMul(nz, ldz)), 0.0);
                        Object __pytra_tuple_16 = normalize(PyRuntime.pySub(ldx, dx), PyRuntime.pySub(ldy, dy), PyRuntime.pySub(ldz, dz));
                        Object hvx = PyRuntime.pyGet(__pytra_tuple_16, 0);
                        Object hvy = PyRuntime.pyGet(__pytra_tuple_16, 1);
                        Object hvz = PyRuntime.pyGet(__pytra_tuple_16, 2);
                        Object ndoth = PyRuntime.pyMax(PyRuntime.pyAdd(PyRuntime.pyAdd(PyRuntime.pyMul(nx, hvx), PyRuntime.pyMul(ny, hvy)), PyRuntime.pyMul(nz, hvz)), 0.0);
                        Object spec = PyRuntime.pyMul(ndoth, ndoth);
                        spec = PyRuntime.pyMul(spec, spec);
                        spec = PyRuntime.pyMul(spec, spec);
                        spec = PyRuntime.pyMul(spec, spec);
                        Object glow = PyRuntime.pyDiv(10.0, PyRuntime.pyAdd(PyRuntime.pyAdd(PyRuntime.pyAdd(1.0, PyRuntime.pyMul(lxv, lxv)), PyRuntime.pyMul(lyv, lyv)), PyRuntime.pyMul(lzv, lzv)));
                        r = PyRuntime.pyAdd(r, PyRuntime.pyAdd(PyRuntime.pyAdd(PyRuntime.pyMul(0.2, ndotl), PyRuntime.pyMul(0.8, spec)), PyRuntime.pyMul(0.45, glow)));
                        g = PyRuntime.pyAdd(g, PyRuntime.pyAdd(PyRuntime.pyAdd(PyRuntime.pyMul(0.18, ndotl), PyRuntime.pyMul(0.6, spec)), PyRuntime.pyMul(0.35, glow)));
                        b = PyRuntime.pyAdd(b, PyRuntime.pyAdd(PyRuntime.pyAdd(PyRuntime.pyMul(0.26, ndotl), PyRuntime.pyMul(1.0, spec)), PyRuntime.pyMul(0.65, glow)));
                        if (PyRuntime.pyBool(PyRuntime.pyEq(hit_kind, 2))) {
                            r = PyRuntime.pyMul(r, 0.95);
                            g = PyRuntime.pyMul(g, 1.05);
                            b = PyRuntime.pyMul(b, 1.1);
                        } else {
                            if (PyRuntime.pyBool(PyRuntime.pyEq(hit_kind, 3))) {
                                r = PyRuntime.pyMul(r, 1.08);
                                g = PyRuntime.pyMul(g, 0.98);
                                b = PyRuntime.pyMul(b, 1.04);
                            } else {
                                r = PyRuntime.pyMul(r, 1.02);
                                g = PyRuntime.pyMul(g, 1.1);
                                b = PyRuntime.pyMul(b, 0.95);
                            }
                        }
                    }
                }
                r = PyRuntime.pyMathSqrt(clamp01(r));
                g = PyRuntime.pyMathSqrt(clamp01(g));
                b = PyRuntime.pyMathSqrt(clamp01(b));
                PyRuntime.pySet(frame, i, quantize_332(r, g, b));
                i = PyRuntime.pyAdd(i, 1);
            }
        }
        return PyRuntime.pyBytes(frame);
    }
    static Object run_16_glass_sculpture_chaos() {
        Object width = 320;
        Object height = 240;
        Object frames_n = 72;
        Object out_path = "sample/out/16_glass_sculpture_chaos.gif";
        Object start = PyRuntime.pyPerfCounter();
        Object frames = PyRuntime.pyList();
        Object i = null;
        for (Object __pytra_it_17 : PyRuntime.pyRange(PyRuntime.pyToInt(0), PyRuntime.pyToInt(frames_n), PyRuntime.pyToInt(1))) {
            i = __pytra_it_17;
            ((java.util.List<Object>)frames).add(render_frame(width, height, i, frames_n));
        }
        PyRuntime.pySaveGif(out_path, width, height, frames, palette_332(), 6, 0);
        Object elapsed = PyRuntime.pySub(PyRuntime.pyPerfCounter(), start);
        PyRuntime.pyPrint("output:", out_path);
        PyRuntime.pyPrint("frames:", frames_n);
        PyRuntime.pyPrint("elapsed_sec:", elapsed);
        return null;
    }

    public static void main(String[] args) {
        run_16_glass_sculpture_chaos();
    }
}
