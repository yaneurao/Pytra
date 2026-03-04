// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/png.py
// generated-by: tools/gen_image_runtime_from_canonical.py

import java.io.ByteArrayOutputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.zip.CRC32;

final class PngHelper {
    private PngHelper() {
    }

    static byte[] pyToBytes(Object v) {
        if (v instanceof byte[] b) {
            return b;
        }
        if (v instanceof List<?> list) {
            byte[] out = new byte[list.size()];
            for (int i = 0; i < list.size(); i++) {
                out[i] = (byte) PyRuntime.pyToInt(list.get(i));
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

    static int pyAdler32(byte[] data) {
        final int mod = 65521;
        int s1 = 1;
        int s2 = 0;
        for (byte b : data) {
            s1 += (b & 0xff);
            if (s1 >= mod) {
                s1 -= mod;
            }
            s2 += s1;
            s2 %= mod;
        }
        return (s2 << 16) | s1;
    }

    static byte[] pyZlibDeflateStore(byte[] data) {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        out.write(0x78);
        out.write(0x01);
        int n = data.length;
        int pos = 0;
        while (pos < n) {
            int remain = n - pos;
            int chunkLen = Math.min(remain, 65535);
            int fin = (pos + chunkLen >= n) ? 1 : 0;
            out.write(fin);
            out.write(chunkLen & 0xff);
            out.write((chunkLen >>> 8) & 0xff);
            int nlen = 0xFFFF ^ chunkLen;
            out.write(nlen & 0xff);
            out.write((nlen >>> 8) & 0xff);
            out.write(data, pos, chunkLen);
            pos += chunkLen;
        }
        int adler = pyAdler32(data);
        out.write((adler >>> 24) & 0xff);
        out.write((adler >>> 16) & 0xff);
        out.write((adler >>> 8) & 0xff);
        out.write(adler & 0xff);
        return out.toByteArray();
    }

    static void pyWriteRGBPNG(Object path, Object width, Object height, Object pixels) {
        int w = PyRuntime.pyToInt(width);
        int h = PyRuntime.pyToInt(height);
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

        byte[] idat = pyZlibDeflateStore(scan);

        byte[] ihdr = new byte[] {
                (byte) (w >>> 24), (byte) (w >>> 16), (byte) (w >>> 8), (byte) w,
                (byte) (h >>> 24), (byte) (h >>> 16), (byte) (h >>> 8), (byte) h,
                8, 2, 0, 0, 0
        };

        try (FileOutputStream fos = new FileOutputStream(PyRuntime.pyToString(path))) {
            fos.write(new byte[] { (byte) 0x89, 'P', 'N', 'G', '\r', '\n', 0x1a, '\n' });
            fos.write(pyChunk("IHDR", ihdr));
            fos.write(pyChunk("IDAT", idat));
            fos.write(pyChunk("IEND", new byte[0]));
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

}
