using System.IO;

namespace Pytra.CsModule
{
    // Generated std/os.cs delegates host bindings through this native seam.
    public static class os_native
    {
        public static string getcwd()
        {
            return Directory.GetCurrentDirectory().Replace('\\', '/');
        }

        public static void mkdir(string p)
        {
            Directory.CreateDirectory(p);
        }

        public static void makedirs(string p, bool exist_ok = false)
        {
            if (!exist_ok && Directory.Exists(p))
            {
                throw new System.IO.IOException("Directory already exists: " + p);
            }
            Directory.CreateDirectory(p);
        }
    }
}
