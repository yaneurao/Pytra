using System;
using System.Collections.Generic;
using System.IO;

namespace Pytra.CsModule
{
    // Python の png_helper.write_rgb_png 相当実装。
    public static class png_helper
    {
        public static void write_rgb_png(string path, int width, int height, List<byte> pixels)
        {
            if (width <= 0 || height <= 0)
            {
                throw new ArgumentException("png: width/height must be positive");
            }

            int expected = checked(width * height * 3);
            if (pixels.Count != expected)
            {
                throw new ArgumentException("png: pixels length mismatch");
            }

            byte[] raw = BuildRawScanlines(width, height, pixels);
            byte[] idat = ZlibStore(raw);

            using (var fs = new FileStream(path, FileMode.Create, FileAccess.Write))
            {
                WriteBytes(fs, new byte[] { 137, 80, 78, 71, 13, 10, 26, 10 });

                byte[] ihdr = new byte[13];
                WriteU32BE(ihdr, 0, (uint)width);
                WriteU32BE(ihdr, 4, (uint)height);
                ihdr[8] = 8;   // bit depth
                ihdr[9] = 2;   // color type RGB
                ihdr[10] = 0;  // compression
                ihdr[11] = 0;  // filter
                ihdr[12] = 0;  // interlace

                WriteChunk(fs, "IHDR", ihdr);
                WriteChunk(fs, "IDAT", idat);
                WriteChunk(fs, "IEND", new byte[0]);
            }
        }

        private static byte[] BuildRawScanlines(int width, int height, List<byte> pixels)
        {
            int rowBytes = checked(width * 3);
            byte[] raw = new byte[checked(height * (rowBytes + 1))];
            int src = 0;
            int dst = 0;
            for (int y = 0; y < height; y++)
            {
                raw[dst++] = 0; // filter type 0
                for (int i = 0; i < rowBytes; i++)
                {
                    raw[dst++] = pixels[src++];
                }
            }
            return raw;
        }

        private static byte[] ZlibStore(byte[] raw)
        {
            using (var ms = new MemoryStream())
            {
                // zlib header (CMF/FLG)
                ms.WriteByte(0x78);
                ms.WriteByte(0x01);

                int pos = 0;
                while (pos < raw.Length)
                {
                    int remain = raw.Length - pos;
                    ushort len = (ushort)(remain > 65535 ? 65535 : remain);
                    bool finalBlock = (pos + len) == raw.Length;

                    ms.WriteByte((byte)(finalBlock ? 0x01 : 0x00));
                    ms.WriteByte((byte)(len & 0xFF));
                    ms.WriteByte((byte)((len >> 8) & 0xFF));
                    ushort nlen = (ushort)~len;
                    ms.WriteByte((byte)(nlen & 0xFF));
                    ms.WriteByte((byte)((nlen >> 8) & 0xFF));
                    ms.Write(raw, pos, len);
                    pos += len;
                }

                uint adler = Adler32(raw);
                WriteU32BE(ms, adler);
                return ms.ToArray();
            }
        }

        private static uint Adler32(byte[] data)
        {
            const uint Mod = 65521;
            uint a = 1;
            uint b = 0;
            foreach (byte ch in data)
            {
                a = (a + ch) % Mod;
                b = (b + a) % Mod;
            }
            return (b << 16) | a;
        }

        private static void WriteChunk(Stream s, string type, byte[] payload)
        {
            WriteU32BE(s, (uint)payload.Length);
            byte[] typeBytes = System.Text.Encoding.ASCII.GetBytes(type);
            WriteBytes(s, typeBytes);
            WriteBytes(s, payload);

            byte[] crcInput = new byte[typeBytes.Length + payload.Length];
            Buffer.BlockCopy(typeBytes, 0, crcInput, 0, typeBytes.Length);
            Buffer.BlockCopy(payload, 0, crcInput, typeBytes.Length, payload.Length);
            WriteU32BE(s, Crc32(crcInput));
        }

        private static uint Crc32(byte[] data)
        {
            uint crc = 0xFFFFFFFF;
            foreach (byte b in data)
            {
                crc ^= b;
                for (int i = 0; i < 8; i++)
                {
                    if ((crc & 1) != 0)
                    {
                        crc = (crc >> 1) ^ 0xEDB88320;
                    }
                    else
                    {
                        crc >>= 1;
                    }
                }
            }
            return ~crc;
        }

        private static void WriteU32BE(Stream s, uint v)
        {
            s.WriteByte((byte)((v >> 24) & 0xFF));
            s.WriteByte((byte)((v >> 16) & 0xFF));
            s.WriteByte((byte)((v >> 8) & 0xFF));
            s.WriteByte((byte)(v & 0xFF));
        }

        private static void WriteU32BE(byte[] dst, int off, uint v)
        {
            dst[off] = (byte)((v >> 24) & 0xFF);
            dst[off + 1] = (byte)((v >> 16) & 0xFF);
            dst[off + 2] = (byte)((v >> 8) & 0xFF);
            dst[off + 3] = (byte)(v & 0xFF);
        }

        private static void WriteBytes(Stream s, byte[] data)
        {
            s.Write(data, 0, data.Length);
        }
    }
}
