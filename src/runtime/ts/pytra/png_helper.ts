// PNG 画像出力ヘルパ（TypeScript版）。

import fs from "node:fs";
import path from "node:path";
import zlib from "node:zlib";

function crc32(buf: Buffer): number {
  let crc = 0xffffffff;
  for (let i = 0; i < buf.length; i += 1) {
    crc ^= buf[i];
    for (let j = 0; j < 8; j += 1) {
      if ((crc & 1) !== 0) {
        crc = (crc >>> 1) ^ 0xedb88320;
      } else {
        crc >>>= 1;
      }
    }
  }
  return ~crc;
}

function chunk(chunkType: string, data: Buffer): Buffer {
  const length = Buffer.alloc(4);
  length.writeUInt32BE(data.length, 0);
  const crcInput = Buffer.concat([Buffer.from(chunkType, "ascii"), data]);
  const crc = Buffer.alloc(4);
  crc.writeUInt32BE(crc32(crcInput) >>> 0, 0);
  return Buffer.concat([length, Buffer.from(chunkType, "ascii"), data, crc]);
}

export function write_rgb_png(outPath: string, width: number, height: number, pixels: ArrayLike<number>): void {
  const raw = Buffer.from(Array.from(pixels));
  const expected = width * height * 3;
  if (raw.length !== expected) {
    throw new Error(`pixels length mismatch: got=${raw.length} expected=${expected}`);
  }

  const rowBytes = width * 3;
  const scanlines = Buffer.alloc(height * (rowBytes + 1));
  for (let y = 0; y < height; y += 1) {
    const dst = y * (rowBytes + 1);
    scanlines[dst] = 0;
    raw.copy(scanlines, dst + 1, y * rowBytes, (y + 1) * rowBytes);
  }

  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0);
  ihdr.writeUInt32BE(height, 4);
  ihdr[8] = 8;
  ihdr[9] = 2;
  ihdr[10] = 0;
  ihdr[11] = 0;
  ihdr[12] = 0;

  const idat = zlib.deflateSync(scanlines, { level: 6 });
  const png = Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    chunk("IHDR", ihdr),
    chunk("IDAT", idat),
    chunk("IEND", Buffer.alloc(0)),
  ]);

  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.writeFileSync(outPath, png);
}
