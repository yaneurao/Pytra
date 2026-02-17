using System;
using System.IO;

namespace Pytra.CsModule
{
    // Python pathlib の最小互換。
    public class py_path
    {
        private readonly string _value;

        public py_path(string value)
        {
            _value = value ?? string.Empty;
        }

        public py_path resolve()
        {
            return new py_path(Path.GetFullPath(_value));
        }

        public py_path parent()
        {
            string? dir = Path.GetDirectoryName(_value);
            return new py_path(dir ?? string.Empty);
        }

        public string name()
        {
            return Path.GetFileName(_value);
        }

        public string stem()
        {
            return Path.GetFileNameWithoutExtension(_value);
        }

        public bool exists()
        {
            return File.Exists(_value) || Directory.Exists(_value);
        }

        public string read_text(string encoding = "utf-8")
        {
            return File.ReadAllText(_value);
        }

        public void write_text(string content, string encoding = "utf-8")
        {
            File.WriteAllText(_value, content ?? string.Empty);
        }

        public void mkdir(bool parents_flag = false, bool exist_ok = false)
        {
            try
            {
                if (parents_flag)
                {
                    Directory.CreateDirectory(_value);
                    return;
                }
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

        public static py_path operator /(py_path lhs, string rhs)
        {
            return new py_path(Path.Combine(lhs._value, rhs));
        }

        public override string ToString()
        {
            return _value;
        }
    }
}
