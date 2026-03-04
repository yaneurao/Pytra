// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/gif.py
// generated-by: tools/gen_image_runtime_from_canonical.py

import java.io.ByteArrayOutputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

final class GifHelper {
    private GifHelper() {
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

    static ArrayList<Long> pyGrayscalePalette() {
        ArrayList<Long> p = new ArrayList<>(256 * 3);
        for (int i = 0; i < 256; i++) {
            long v = i;
            p.add(v);
            p.add(v);
            p.add(v);
        }
        return p;
    }

    static void pySaveGif(Object path, Object width, Object height, Object frames, Object palette, Object delayCs, Object loop) {
        int w = PyRuntime.pyToInt(width);
        int h = PyRuntime.pyToInt(height);
        int frameBytes = w * h;
        byte[] pal = PngHelper.pyToBytes(palette);
        if (pal.length != 256 * 3) {
            throw new RuntimeException("palette must be 256*3 bytes");
        }
        int dcs = PyRuntime.pyToInt(delayCs);
        int lp = PyRuntime.pyToInt(loop);

        List<Object> frs = PyRuntime.pyIter(frames);

        try (FileOutputStream fos = new FileOutputStream(PyRuntime.pyToString(path))) {
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
                byte[] fr = PngHelper.pyToBytes(frAny);
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
