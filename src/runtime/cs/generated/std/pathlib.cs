// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/pathlib.py
// generated-by: tools/gen_runtime_from_manifest.py


using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

namespace Pytra.CsModule
{
    public class py_path
    {
        public static readonly long PYTRA_TYPE_ID = py_runtime.py_register_class_type(py_runtime.PYTRA_TID_OBJECT);
        private readonly string _value;

        public py_path(string value)
        {
            _value = value ?? string.Empty;
        }

        private static string NormalizeParentText(string value)
        {
            return string.IsNullOrEmpty(value) ? "." : value;
        }

        private static Encoding ResolveEncoding(string encoding)
        {
            if (string.IsNullOrEmpty(encoding) || encoding == "utf-8")
            {
                return new UTF8Encoding(false);
            }
            return Encoding.GetEncoding(encoding);
        }

        public string __str__()
        {
            return _value;
        }

        public string __repr__()
        {
            return "Path(" + _value + ")";
        }

        public string __fspath__()
        {
            return _value;
        }

        public static py_path operator /(py_path lhs, string rhs)
        {
            string basePath = lhs == null ? string.Empty : lhs._value;
            return new py_path(Path.Combine(basePath, rhs ?? string.Empty));
        }

        public py_path __truediv__(string rhs)
        {
            return this / rhs;
        }

        public py_path parent()
        {
            return new py_path(NormalizeParentText(Path.GetDirectoryName(_value)));
        }

        public List<py_path> parents()
        {
            List<py_path> py_out = new List<py_path>();
            string current = NormalizeParentText(Path.GetDirectoryName(_value));
            while (true)
            {
                py_out.Add(new py_path(current));
                string nextCurrent = NormalizeParentText(Path.GetDirectoryName(current));
                if (nextCurrent == current)
                {
                    break;
                }
                current = nextCurrent;
            }
            return py_out;
        }

        public string name()
        {
            return Path.GetFileName(_value) ?? string.Empty;
        }

        public string suffix()
        {
            return Path.GetExtension(name()) ?? string.Empty;
        }

        public string stem()
        {
            return Path.GetFileNameWithoutExtension(name()) ?? string.Empty;
        }

        public py_path resolve()
        {
            string target = string.IsNullOrEmpty(_value) ? "." : _value;
            return new py_path(Path.GetFullPath(target));
        }

        public bool exists()
        {
            return File.Exists(_value) || Directory.Exists(_value);
        }

        public void mkdir(bool parents = false, bool exist_ok = false)
        {
            try
            {
                Directory.CreateDirectory(_value);
            }
            catch
            {
                if (!exist_ok)
                {
                    throw;
                }
            }
        }

        public string read_text(string encoding = "utf-8")
        {
            return File.ReadAllText(_value, ResolveEncoding(encoding));
        }

        public long write_text(string text, string encoding = "utf-8")
        {
            string body = text ?? string.Empty;
            File.WriteAllText(_value, body, ResolveEncoding(encoding));
            return Convert.ToInt64(body.Length);
        }

        public List<py_path> glob(string pattern)
        {
            List<py_path> py_out = new List<py_path>();
            string baseDir = string.IsNullOrEmpty(_value) ? "." : _value;
            if (!Directory.Exists(baseDir))
            {
                return py_out;
            }
            string searchPattern = string.IsNullOrEmpty(pattern) ? "*" : pattern;
            foreach (string item in Directory.GetFileSystemEntries(baseDir, searchPattern))
            {
                py_out.Add(new py_path(item));
            }
            return py_out;
        }

        public static py_path cwd()
        {
            return new py_path(Directory.GetCurrentDirectory());
        }

        public override string ToString()
        {
            return _value;
        }
    }
}
