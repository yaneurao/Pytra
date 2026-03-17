using System.IO;

namespace Pytra.CsModule
{
    // Generated std/os_path.cs delegates host bindings through this native seam.
    public static class os_path_native
    {
        public static string join(string a, string b)
        {
            return Path.Combine(a, b).Replace('\\', '/');
        }

        public static string dirname(string p)
        {
            return (Path.GetDirectoryName(p) ?? "").Replace('\\', '/');
        }

        public static string basename(string p)
        {
            return Path.GetFileName(p);
        }

        public static (string, string) splitext(string p)
        {
            string ext = Path.GetExtension(p);
            string stem = p.Substring(0, p.Length - ext.Length);
            return (stem, ext);
        }

        public static string abspath(string p)
        {
            return Path.GetFullPath(p).Replace('\\', '/');
        }

        public static bool exists(string p)
        {
            return File.Exists(p) || Directory.Exists(p);
        }
    }
}
