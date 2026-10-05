using System;
using System.IO;

namespace VoicePlayer
{
    public static class Pck
    {
        /// <summary>在 AKPK 包的 sounds 段按 32 位 Wwise ID 定位音乐，返回 (offset, size)</summary>
        public static (long off, int size)? FindSound(string path, string idHex)
        {
            uint target;
            try { target = Convert.ToUInt32(idHex, 16); } catch { return null; }
            using var fs = File.OpenRead(path);
            var head = new byte[0x40];
            if (fs.Read(head, 0, 0x40) < 0x20) return null;
            if (head[0] != (byte)'A' || head[1] != (byte)'K' || head[2] != (byte)'P' || head[3] != (byte)'K') return null;
            uint U(int o) => BitConverter.ToUInt32(head, o);
            uint header = U(4), sec1 = U(12), sec2 = U(16), sec3 = U(20);
            long pos = 0x18;
            if ((long)sec1 + sec2 + sec3 + 0x10 < header) pos = 0x1C;
            var br = new BinaryReader(fs);
            fs.Position = pos;
            uint langs = br.ReadUInt32();
            fs.Position += langs * 8;
            fs.Position = pos + sec1 + sec2;
            uint n = br.ReadUInt32();
            if (n == 0) return null;
            int es = (int)((sec3 - 4) / n);
            if (es != 0x14) return null;
            for (uint i = 0; i < n; i++)
            {
                var e = br.ReadBytes(es);
                uint id = BitConverter.ToUInt32(e, 0);
                uint block = BitConverter.ToUInt32(e, 4);
                uint size = BitConverter.ToUInt32(e, 8);
                uint off = BitConverter.ToUInt32(e, 12);
                if (id == target)
                {
                    long o = block != 0 ? (long)off * block : off;
                    return (o, (int)size);
                }
            }
            return null;
        }

        /// <summary>在 AKPK 包的 externals 段按 64/32 位哈希定位文件，返回 (offset, size)</summary>
        public static (long off, int size)? FindExternal(string path, string hashHex)
        {
            ulong target;
            try { target = Convert.ToUInt64(hashHex, 16); } catch { return null; }
            using var fs = File.OpenRead(path);
            var head = new byte[0x40];
            if (fs.Read(head, 0, 0x40) < 0x20) return null;
            if (head[0] != (byte)'A' || head[1] != (byte)'K' || head[2] != (byte)'P' || head[3] != (byte)'K') return null;
            uint U(int o) => BitConverter.ToUInt32(head, o);
            uint header = U(4), sec1 = U(12), sec2 = U(16), sec3 = U(20), sec4 = 0;
            long pos = 0x18;
            if ((long)sec1 + sec2 + sec3 + 0x10 < header) { sec4 = U(24); pos = 0x1C; }
            var br = new BinaryReader(fs);
            fs.Position = pos;
            uint langs = br.ReadUInt32();
            fs.Position += langs * 8;
            fs.Position = pos + sec1 + sec2 + sec3;
            uint n = br.ReadUInt32();
            if (n == 0 || sec4 == 0) return null;
            int es = (int)((sec4 - 4) / n);
            for (uint i = 0; i < n; i++)
            {
                var e = br.ReadBytes(es);
                ulong id; uint block, size, off;
                if (es == 0x18)
                {
                    uint id2 = BitConverter.ToUInt32(e, 0), id1 = BitConverter.ToUInt32(e, 4);
                    block = BitConverter.ToUInt32(e, 8);
                    size = BitConverter.ToUInt32(e, 12);
                    off = BitConverter.ToUInt32(e, 16);
                    id = ((ulong)id1 << 32) | id2;
                }
                else if (es == 0x14)
                {
                    id = BitConverter.ToUInt32(e, 0);
                    block = BitConverter.ToUInt32(e, 4);
                    size = BitConverter.ToUInt32(e, 8);
                    off = BitConverter.ToUInt32(e, 12);
                }
                else return null;
                if (id == target)
                {
                    long o = block != 0 ? (long)off * block : off;
                    return (o, (int)size);
                }
            }
            return null;
        }
    }
}
