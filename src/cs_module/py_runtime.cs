using System;
using System.Collections;
using System.Collections.Generic;

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
