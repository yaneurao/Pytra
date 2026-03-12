// Python pathlib の最小互換実装（Node.js）。

const fs = require("fs");
const path = require("path");

class Path {
  constructor(value) {
    this.value = String(value ?? "");
  }

  resolve() {
    return new Path(path.resolve(this.value));
  }

  parent() {
    return new Path(path.dirname(this.value));
  }

  name() {
    return path.basename(this.value);
  }

  stem() {
    return path.parse(this.value).name;
  }

  exists() {
    return fs.existsSync(this.value);
  }

  read_text(_encoding = "utf-8") {
    return fs.readFileSync(this.value, "utf8");
  }

  write_text(content, _encoding = "utf-8") {
    fs.writeFileSync(this.value, String(content), "utf8");
  }

  mkdir(parents = false, exist_ok = false) {
    if (parents) {
      fs.mkdirSync(this.value, { recursive: true });
      return;
    }
    try {
      fs.mkdirSync(this.value);
    } catch (err) {
      if (!(exist_ok && err && err.code === "EEXIST")) {
        throw err;
      }
    }
  }

  toString() {
    return this.value;
  }
}

function pathJoin(base, child) {
  return new Path(path.join(String(base), String(child)));
}

module.exports = { Path, pathJoin };
