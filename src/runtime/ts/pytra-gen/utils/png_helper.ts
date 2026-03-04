// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/png.py
// generated-by: tools/gen_image_runtime_from_canonical.py
// PNG 画像出力ヘルパ（TypeScript版）。

import fs from "node:fs";
import path from "node:path";

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
  return (~crc) >>> 0;
}

function adler32(buf: Buffer): number {
  const mod = 65521;
  let s1 = 1;
  let s2 = 0;
  for (let i = 0; i < buf.length; i += 1) {
    s1 += buf[i];
    if (s1 >= mod) {
      s1 -= mod;
    }
    s2 += s1;
    s2 %= mod;
  }
  return (((s2 << 16) >>> 0) | (s1 & 0xffff)) >>> 0;
}

function u16le(v: number): Buffer {
  return Buffer.from([v & 0xff, (v >>> 8) & 0xff]);
}

function u32be(v: number): Buffer {
  return Buffer.from([(v >>> 24) & 0xff, (v >>> 16) & 0xff, (v >>> 8) & 0xff, v & 0xff]);
}

function zlibDeflateStore(data: Buffer): Buffer {
  const out: Buffer[] = [];
  out.push(Buffer.from([0x78, 0x01]));
  let pos = 0;
  while (pos < data.length) {
    const remain = data.length - pos;
    const chunkLen = remain > 65535 ? 65535 : remain;
    const final = pos + chunkLen >= data.length ? 1 : 0;
    out.push(Buffer.from([final]));
    out.push(u16le(chunkLen));
    out.push(u16le((0xffff ^ chunkLen) & 0xffff));
    out.push(data.subarray(pos, pos + chunkLen));
    pos += chunkLen;
  }
  out.push(u32be(adler32(data)));
  return Buffer.concat(out);
}

function chunk(chunkType: string, data: Buffer): Buffer {
  const crcInput = Buffer.concat([Buffer.from(chunkType, "ascii"), data]);
  return Buffer.concat([u32be(data.length >>> 0), Buffer.from(chunkType, "ascii"), data, u32be(crc32(crcInput))]);
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

  const idat = zlibDeflateStore(scanlines);
  const png = Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    chunk("IHDR", ihdr),
    chunk("IDAT", idat),
    chunk("IEND", Buffer.alloc(0)),
  ]);

  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.writeFileSync(outPath, png);
}
