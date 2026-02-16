// GIF 画像出力ヘルパ（TypeScript版）。

import fs from "node:fs";
import path from "node:path";

export function grayscale_palette(): number[] {
  const p = new Array<number>(256 * 3);
  for (let i = 0; i < 256; i += 1) {
    p[i * 3] = i;
    p[i * 3 + 1] = i;
    p[i * 3 + 2] = i;
  }
  return p;
}

function lzwEncode(data: ArrayLike<number>, minCodeSize: number): number[] {
  if (data.length === 0) {
    return [];
  }
  const clearCode = 1 << minCodeSize;
  const endCode = clearCode + 1;
  const codeSize = minCodeSize + 1;
  const out: number[] = [];

  let bitBuffer = 0;
  let bitCount = 0;

  const emit = (code: number): void => {
    bitBuffer |= code << bitCount;
    bitCount += codeSize;
    while (bitCount >= 8) {
      out.push(bitBuffer & 0xff);
      bitBuffer >>>= 8;
      bitCount -= 8;
    }
  };

  emit(clearCode);
  for (let i = 0; i < data.length; i += 1) {
    emit(data[i]);
    emit(clearCode);
  }
  emit(endCode);
  if (bitCount > 0) {
    out.push(bitBuffer & 0xff);
  }
  return out;
}

function pushU16LE(out: number[], v: number): void {
  out.push(v & 0xff);
  out.push((v >>> 8) & 0xff);
}

export function save_gif(
  outPath: string,
  width: number,
  height: number,
  frames: ArrayLike<ArrayLike<number>>,
  palette: ArrayLike<number>,
  delay_cs = 4,
  loop = 0,
): void {
  if (palette.length !== 256 * 3) {
    throw new Error("palette must be 256*3 bytes");
  }

  const frameBytes = width * height;
  for (const frame of Array.from(frames)) {
    if (frame.length !== frameBytes) {
      throw new Error("frame size mismatch");
    }
  }

  const chunks: Buffer[] = [];
  const writeByte = (v: number): void => {
    chunks.push(Buffer.from([v & 0xff]));
  };
  const writeU16 = (v: number): void => {
    const b = Buffer.allocUnsafe(2);
    b[0] = v & 0xff;
    b[1] = (v >>> 8) & 0xff;
    chunks.push(b);
  };
  const writeBytes = (arr: ArrayLike<number>): void => {
    chunks.push(Buffer.from(Array.from(arr)));
  };

  chunks.push(Buffer.from("GIF89a", "ascii"));
  writeU16(width);
  writeU16(height);
  writeByte(0xf7);
  writeByte(0);
  writeByte(0);
  writeBytes(palette);

  writeBytes([0x21, 0xff, 0x0b]);
  chunks.push(Buffer.from("NETSCAPE2.0", "ascii"));
  writeBytes([0x03, 0x01]);
  writeU16(loop);
  writeByte(0x00);

  for (const frame of Array.from(frames)) {
    writeBytes([0x21, 0xf9, 0x04, 0x00]);
    writeU16(delay_cs);
    writeByte(0x00);
    writeByte(0x00);

    writeByte(0x2c);
    writeU16(0);
    writeU16(0);
    writeU16(width);
    writeU16(height);
    writeByte(0x00);

    writeByte(8);
    const compressed = lzwEncode(frame, 8);
    let pos = 0;
    while (pos < compressed.length) {
      const len = Math.min(255, compressed.length - pos);
      writeByte(len);
      writeBytes(compressed.slice(pos, pos + len));
      pos += len;
    }
    writeByte(0x00);
  }

  writeByte(0x3b);
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.writeFileSync(outPath, Buffer.concat(chunks));
}
