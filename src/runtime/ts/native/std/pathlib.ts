// Python pathlib の最小互換実装（Node.js / TypeScript）。

import * as fs from "fs";
import * as nodepath from "path";

export class Path {
  value: string;

  constructor(value: unknown) {
    this.value = String(value ?? "");
  }

  resolve(): Path {
    return new Path(nodepath.resolve(this.value));
  }

  parent(): Path {
    return new Path(nodepath.dirname(this.value));
  }

  name(): string {
    return nodepath.basename(this.value);
  }

  stem(): string {
    return nodepath.parse(this.value).name;
  }

  exists(): boolean {
    return fs.existsSync(this.value);
  }

  read_text(_encoding: string = "utf-8"): string {
    return fs.readFileSync(this.value, "utf8");
  }

  write_text(content: unknown, _encoding: string = "utf-8"): void {
    fs.writeFileSync(this.value, String(content), "utf8");
  }

  mkdir(parents: boolean = false, exist_ok: boolean = false): void {
    if (parents) {
      fs.mkdirSync(this.value, { recursive: true });
      return;
    }
    try {
      fs.mkdirSync(this.value);
    } catch (err: unknown) {
      const e = err as { code?: string };
      if (!(exist_ok && e.code === "EEXIST")) {
        throw err;
      }
    }
  }

  toString(): string {
    return this.value;
  }
}

export function pathJoin(base: unknown, child: unknown): Path {
  return new Path(nodepath.join(String(base), String(child)));
}
