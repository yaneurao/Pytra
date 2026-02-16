using System;
using System.Collections.Generic;
using System.IO;

namespace Pytra.CsModule
{
    // Python の py_module.gif_helper 相当実装。
    public static class gif_helper
    {
        private static void EmitCode(List<byte> outv, ref int bitBuffer, ref int bitCount, int code, int codeSize)
        {
            bitBuffer |= (code << bitCount);
            bitCount += codeSize;
            while (bitCount >= 8)
            {
                outv.Add((byte)(bitBuffer & 0xFF));
                bitBuffer >>= 8;
                bitCount -= 8;
            }
        }

        private static byte[] LzwEncode(IReadOnlyList<byte> data, int minCodeSize)
        {
            if (data.Count == 0)
            {
                return Array.Empty<byte>();
            }

            int clearCode = 1 << minCodeSize;
            int endCode = clearCode + 1;
            int codeSize = minCodeSize + 1;

            var outv = new List<byte>();
            int bitBuffer = 0;
            int bitCount = 0;

            EmitCode(outv, ref bitBuffer, ref bitCount, clearCode, codeSize);

            for (int i = 0; i < data.Count; i++)
            {
                EmitCode(outv, ref bitBuffer, ref bitCount, data[i], codeSize);
                EmitCode(outv, ref bitBuffer, ref bitCount, clearCode, codeSize);
            }

            EmitCode(outv, ref bitBuffer, ref bitCount, endCode, codeSize);

            if (bitCount > 0)
            {
                outv.Add((byte)(bitBuffer & 0xFF));
            }

            return outv.ToArray();
        }

        public static List<byte> grayscale_palette()
        {
            var p = new List<byte>(256 * 3);
            for (int i = 0; i < 256; i++)
            {
                byte v = (byte)i;
                p.Add(v);
                p.Add(v);
                p.Add(v);
            }
            return p;
        }

        private static void AppendU16LE(List<byte> outv, int v)
        {
            outv.Add((byte)(v & 0xFF));
            outv.Add((byte)((v >> 8) & 0xFF));
        }

        public static void save_gif(
            string path,
            long width,
            long height,
            List<List<byte>> frames,
            List<byte> palette,
            long delay_cs,
            long loop)
        {
            int w = checked((int)width);
            int h = checked((int)height);
            int delay = checked((int)delay_cs);
            int loopCount = checked((int)loop);

            if (palette.Count != 256 * 3)
            {
                throw new ArgumentException("palette must be 256*3 bytes");
            }
            int frameSize = checked(w * h);
            foreach (List<byte> fr in frames)
            {
                if (fr.Count != frameSize)
                {
                    throw new ArgumentException("frame size mismatch");
                }
            }

            var outv = new List<byte>(1024 + frames.Count * frameSize / 2);

            outv.Add((byte)'G'); outv.Add((byte)'I'); outv.Add((byte)'F'); outv.Add((byte)'8'); outv.Add((byte)'9'); outv.Add((byte)'a');
            AppendU16LE(outv, w);
            AppendU16LE(outv, h);
            outv.Add(0xF7); outv.Add(0x00); outv.Add(0x00);
            outv.AddRange(palette);

            outv.Add(0x21); outv.Add(0xFF); outv.Add(0x0B);
            outv.Add((byte)'N'); outv.Add((byte)'E'); outv.Add((byte)'T'); outv.Add((byte)'S'); outv.Add((byte)'C');
            outv.Add((byte)'A'); outv.Add((byte)'P'); outv.Add((byte)'E'); outv.Add((byte)'2'); outv.Add((byte)'.'); outv.Add((byte)'0');
            outv.Add(0x03); outv.Add(0x01);
            AppendU16LE(outv, loopCount);
            outv.Add(0x00);

            foreach (List<byte> fr in frames)
            {
                outv.Add(0x21); outv.Add(0xF9); outv.Add(0x04); outv.Add(0x00);
                AppendU16LE(outv, delay);
                outv.Add(0x00); outv.Add(0x00);

                outv.Add(0x2C);
                AppendU16LE(outv, 0);
                AppendU16LE(outv, 0);
                AppendU16LE(outv, w);
                AppendU16LE(outv, h);
                outv.Add(0x00);

                outv.Add(0x08);
                byte[] compressed = LzwEncode(fr, 8);
                int pos = 0;
                while (pos < compressed.Length)
                {
                    int len = Math.Min(255, compressed.Length - pos);
                    outv.Add((byte)len);
                    for (int i = 0; i < len; i++)
                    {
                        outv.Add(compressed[pos + i]);
                    }
                    pos += len;
                }
                outv.Add(0x00);
            }

            outv.Add(0x3B);
            File.WriteAllBytes(path, outv.ToArray());
        }

        public static void save_gif(
            string path,
            long width,
            long height,
            List<List<byte>> frames,
            List<byte> palette)
        {
            save_gif(path, width, height, frames, palette, 4, 0);
        }
    }
}
