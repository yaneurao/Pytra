using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;

namespace Pytra.CsModule
{
    // Python の print 相当を提供する最小ランタイム。
    public static class py_runtime
    {
        private static int NormalizeSliceIndex(long index, int length)
        {
            long v = index;
            if (v < 0)
            {
                v += length;
            }
            if (v < 0)
            {
                return 0;
            }
            if (v > length)
            {
                return length;
            }
            return (int)v;
        }

        private static int NormalizeIndex(long index, int length)
        {
            long v = index;
            if (v < 0)
            {
                v += length;
            }
            if (v < 0 || v >= length)
            {
                throw new ArgumentOutOfRangeException(nameof(index));
            }
            return (int)v;
        }

        public static List<T> py_slice<T>(List<T> source, long? start, long? stop)
        {
            if (source == null)
            {
                throw new ArgumentNullException(nameof(source));
            }
            int length = source.Count;
            int s = start.HasValue ? NormalizeSliceIndex(start.Value, length) : 0;
            int e = stop.HasValue ? NormalizeSliceIndex(stop.Value, length) : length;
            if (e < s)
            {
                return new List<T>();
            }
            return source.GetRange(s, e - s);
        }

        public static string py_slice(string source, long? start, long? stop)
        {
            if (source == null)
            {
                throw new ArgumentNullException(nameof(source));
            }
            int length = source.Length;
            int s = start.HasValue ? NormalizeSliceIndex(start.Value, length) : 0;
            int e = stop.HasValue ? NormalizeSliceIndex(stop.Value, length) : length;
            if (e < s)
            {
                return string.Empty;
            }
            return source.Substring(s, e - s);
        }

        public static List<byte> py_bytearray(object countLike)
        {
            int n = Convert.ToInt32(countLike);
            if (n < 0)
            {
                throw new ArgumentOutOfRangeException(nameof(countLike));
            }
            var outv = new List<byte>(n);
            for (int i = 0; i < n; i++)
            {
                outv.Add(0);
            }
            return outv;
        }

        public static List<byte> py_bytes(List<byte> source)
        {
            return new List<byte>(source);
        }

        public static T py_get<T>(List<T> source, object indexLike)
        {
            int idx = NormalizeIndex(Convert.ToInt64(indexLike), source.Count);
            return source[idx];
        }

        public static string py_get(string source, object indexLike)
        {
            int idx = NormalizeIndex(Convert.ToInt64(indexLike), source.Length);
            return source[idx].ToString();
        }

        public static V py_get<K, V>(Dictionary<K, V> source, K key)
        {
            return source[key];
        }

        public static void py_set<T>(List<T> source, object indexLike, object value)
        {
            int idx = NormalizeIndex(Convert.ToInt64(indexLike), source.Count);
            if (typeof(T) == typeof(byte))
            {
                source[idx] = (T)(object)Convert.ToByte(value);
                return;
            }
            source[idx] = (T)value;
        }

        public static void py_set<K, V>(Dictionary<K, V> source, K key, V value)
        {
            source[key] = value;
        }

        public static void py_append<T>(List<T> source, object value)
        {
            if (typeof(T) == typeof(byte))
            {
                byte b = Convert.ToByte(value);
                source.Add((T)(object)b);
                return;
            }
            source.Add((T)value);
        }

        public static T py_pop<T>(List<T> source)
        {
            if (source.Count == 0)
            {
                throw new ArgumentOutOfRangeException(nameof(source));
            }
            int last = source.Count - 1;
            T value = source[last];
            source.RemoveAt(last);
            return value;
        }

        public static T py_pop<T>(List<T> source, object indexLike)
        {
            int idx = NormalizeIndex(Convert.ToInt64(indexLike), source.Count);
            T value = source[idx];
            source.RemoveAt(idx);
            return value;
        }

        public static long py_len<T>(List<T> source)
        {
            return source.Count;
        }

        public static long py_len(string source)
        {
            return source.Length;
        }

        public static bool py_bool(object value)
        {
            if (value == null)
            {
                return false;
            }
            if (value is bool b)
            {
                return b;
            }
            if (value is long l)
            {
                return l != 0;
            }
            if (value is int i)
            {
                return i != 0;
            }
            if (value is double d)
            {
                return d != 0.0;
            }
            if (value is string s)
            {
                return s.Length != 0;
            }
            if (value is ICollection c)
            {
                return c.Count != 0;
            }
            return true;
        }

        public static bool py_isdigit(string value)
        {
            if (string.IsNullOrEmpty(value))
            {
                return false;
            }
            foreach (char ch in value)
            {
                if (!char.IsDigit(ch))
                {
                    return false;
                }
            }
            return true;
        }

        public static bool py_isalpha(string value)
        {
            if (string.IsNullOrEmpty(value))
            {
                return false;
            }
            foreach (char ch in value)
            {
                if (!char.IsLetter(ch))
                {
                    return false;
                }
            }
            return true;
        }

        public static long py_ord(string value)
        {
            if (string.IsNullOrEmpty(value) || value.Length != 1)
            {
                throw new ArgumentException("ord() expected a character");
            }
            return value[0];
        }

        public static long py_int(object value)
        {
            if (value == null)
            {
                throw new ArgumentException("int() argument must not be null");
            }
            if (value is string s)
            {
                string t = s.Trim();
                if (!long.TryParse(t, NumberStyles.Integer, CultureInfo.InvariantCulture, out long parsed))
                {
                    throw new ArgumentException("invalid literal for int()");
                }
                return parsed;
            }
            return Convert.ToInt64(value);
        }

        public static long py_floordiv(object left, object right)
        {
            long a = Convert.ToInt64(left);
            long b = Convert.ToInt64(right);
            if (b == 0)
            {
                throw new DivideByZeroException();
            }
            long q = a / b;
            long r = a % b;
            if (r != 0 && ((r > 0) != (b > 0)))
            {
                q -= 1;
            }
            return q;
        }

        public static long py_mod(object left, object right)
        {
            long a = Convert.ToInt64(left);
            long b = Convert.ToInt64(right);
            if (b == 0)
            {
                throw new DivideByZeroException();
            }
            long r = a % b;
            if (r != 0 && ((r > 0) != (b > 0)))
            {
                r += b;
            }
            return r;
        }

        public static void print(params object[] args)
        {
            if (args == null || args.Length == 0)
            {
                Console.WriteLine();
                return;
            }
            Console.WriteLine(string.Join(" ", args));
        }

        // Python の `x in y` に相当する最小判定ヘルパ。
        public static bool py_in(object needle, object haystack)
        {
            if (haystack == null)
            {
                return false;
            }

            string text = haystack as string;
            if (text != null)
            {
                return text.Contains(Convert.ToString(needle));
            }

            IDictionary dict = haystack as IDictionary;
            if (dict != null)
            {
                return dict.Contains(needle);
            }

            IEnumerable enumerable = haystack as IEnumerable;
            if (enumerable != null)
            {
                foreach (object item in enumerable)
                {
                    if (Equals(item, needle))
                    {
                        return true;
                    }
                }
            }

            return false;
        }
    }
}
