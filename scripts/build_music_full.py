# -*- coding: utf-8 -*-
"""把地区音乐从历史的 105 首手工清单，重建为**全量**曲库。

背景：原 `build_music_source.py` 只把一份旧的 105 首清单从本地 MP3 升级成从 pck 解包，
**从不发现新曲目**。而本地 `Music*.pck` 有 1,833 个音频 ID，`hk4e.map` 有 1,287 个曲名，
交集 1,214 首——即原来只收了 8.7%。

分组规则（两级，尽量贴合玩家心智）：
  · 曲名里含地区 token → 归到该地区（蒙德/璃月/稻妻/须弥/枫丹/纳塔/至冬…）
  · 否则按事件名前缀的类型（探索/剧情/战斗/秘境/音游/场景/天气/…）
曲名沿用 fix_music_names.display_name（技术前缀剥离 + 有把握的地名还原）。

用法：py scripts/build_music_full.py [--apply]
"""
import io, os, sys, re, json, glob, struct, collections

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(HERE, 'tools')
ROOT = os.path.dirname(HERE)
IDX = os.path.join(ROOT, 'data', 'index.json')
# 游戏音频目录（官方默认安装路径）：可用 AUDIO_ROOT 覆盖
AUDIO = os.environ.get('AUDIO_ROOT') or (
    r'D:\Program Files\miHoYo Launcher\games\Genshin Impact\Genshin Impact Game'
    r'\YuanShen_Data\StreamingAssets\AudioAssets')
APPLY = '--apply' in sys.argv

sys.path.insert(0, TOOLS)
sys.path.insert(0, HERE)
from mapper import Mapper                                    # noqa
from fix_music_names import display_name                     # noqa

# 地区 token -> (分组名, 背景图基名)
REGION = {
    'mengde': ('蒙德', 'region_mengde'), 'mondstadt': ('蒙德', 'region_mengde'),
    'liyue': ('璃月', 'region_liyue'),
    'daoqi': ('稻妻', 'region_inazuma'), 'inazuma': ('稻妻', 'region_inazuma'),
    'xumi': ('须弥', 'region_sumeru'), 'sumeru': ('须弥', 'region_sumeru'),
    'fengdan': ('枫丹', 'region_fontaine'), 'fontaine': ('枫丹', 'region_fontaine'),
    'nata': ('纳塔', 'region_natlan'), 'natlan': ('纳塔', 'region_natlan'),
    'snezhnaya': ('至冬', 'region_snezhnaya'), 'dongzhi': ('至冬', 'region_snezhnaya'),
    # 子地区 token（实测来自曲名，归属明确的才加）
    'mingshendao': ('稻妻', 'region_inazuma'), 'heguan': ('稻妻', 'region_inazuma'),
    'qinglaidao': ('稻妻', 'region_inazuma'), 'haiqidao': ('稻妻', 'region_inazuma'),
    'dariyuyu': ('稻妻', 'region_inazuma'), 'lidao': ('稻妻', 'region_inazuma'),
    'cengyanjuyuan': ('璃月', 'region_liyue'), 'cyjy': ('璃月', 'region_liyue'),
    'qingyunding': ('璃月', 'region_liyue'), 'qunyuge': ('璃月', 'region_liyue'),
    'bishuiyuan': ('璃月', 'region_liyue'), 'guiliyuan': ('璃月', 'region_liyue'),
    'minglin': ('璃月', 'region_liyue'), 'minlin': ('璃月', 'region_liyue'),
}

# 事件名类型前缀 -> (分组名, 背景图基名)
TYPE = {
    'explore': ('探索', 'region_homeworld'),
    'scene': ('场景', 'region_homeworld'), 'city': ('场景', 'region_homeworld'),
    'cutscene': ('剧情', 'region_firmament'), 'chapter': ('剧情', 'region_firmament'),
    'quest': ('剧情', 'region_firmament'), 'specialquest': ('剧情', 'region_firmament'),
    'combat': ('战斗', 'region_dungeon'), 'dungeon': ('秘境', 'region_dungeon'),
    'deadzone': ('战斗', 'region_dungeon'), 'boss': ('战斗', 'region_dungeon'),
    'musicgame': ('音游', 'region_homeworld'),
    'weather': ('天气', 'region_homeworld'),
    'v': ('版本专题', 'region_homeworld'), 'l': ('关卡', 'region_homeworld'),
    'theme': ('主题曲', 'region_firmament'),
    # 以下几类都偏小（3~10 首），单独成组只是碎片：
    #   黄金屋 7 首全是 GoldenHall Qte（Boss 战 QTE 音乐） -> 战斗
    #   OST 3 + 登录 4 + 主题曲 4                          -> 主题曲（共 11 首）
    #   载具 3 首全是水路船音乐                              -> 场景
    #   音效 10 首全是同一族怪物乐器 SFX                      -> 其他
    'goldenhall': ('战斗', 'region_dungeon'),
    'login': ('主题曲', 'region_firmament'),
    'ost': ('主题曲', 'region_firmament'),
    'vehicle': ('场景', 'region_homeworld'),
    'sfx': ('其他', 'region_homeworld'),
}

# 分组展示顺序
ORDER = ['蒙德', '璃月', '稻妻', '须弥', '枫丹', '纳塔', '至冬',
         '探索', '场景', '剧情', '战斗', '秘境', '音游', '天气',
         '版本专题', '关卡', '主题曲', '其他']


def parse_sounds(path):
    with io.open(path, 'rb') as f:
        head = f.read(0x40)
        header_size, flag, sec1, sec2, sec3 = struct.unpack_from('<IIIII', head, 4)
        pos = 0x18
        if sec1 + sec2 + sec3 + 0x10 < header_size:
            pos = 0x1C
        f.seek(pos)
        langcnt = struct.unpack('<I', f.read(4))[0]
        f.seek(langcnt * 8, 1)
        f.seek(pos + sec1 + sec2)
        n = struct.unpack('<I', f.read(4))[0]
        es = (sec3 - 4) // n if n else 0
        out = {}
        for _ in range(n):
            e = f.read(es)
            if es == 0x14:
                fid, blk, sz, off, lang = struct.unpack('<IIIII', e)
                out[fid] = (off * blk if blk else off, sz)
        return out


def family(name):
    """事件名的类型家族。去掉结尾数字，让 chapter01..06 归成 chapter、v50/v52/v53 归成 v。"""
    s = re.sub(r'^(M\d+_)?', '', name, flags=re.I)
    parts = s.split('_')
    p0 = parts[0].lower()
    f = parts[1].lower() if (p0 == 'music' and len(parts) > 1) else p0
    return re.sub(r'\d+$', '', f) or f


def main():
    print('[1/3] 读 hk4e.map …')
    m = Mapper(os.path.join(TOOLS, 'hk4e.map'))
    id2name = {int(k): v.split('\\')[-1] for k, v in m.music_keys.items()}
    print('      曲名 %d' % len(id2name))

    print('[2/3] 扫本地 Music*.pck …')
    id2pck = {}
    for p in sorted(glob.glob(os.path.join(AUDIO, 'Music*.pck'))):
        try:
            for fid in parse_sounds(p):
                id2pck.setdefault(fid, os.path.basename(p))
        except Exception as e:
            print('      解析失败 %s: %s' % (os.path.basename(p), e))
    print('      本地音频 ID %d' % len(id2pck))

    print('[3/3] 组装曲库 …')
    groups = collections.OrderedDict()
    used_names = {}
    total = 0
    for mid in sorted(id2pck):
        if mid not in id2name:
            continue
        raw = id2name[mid]
        low = raw.lower()
        fam = family(raw)
        gname, bg = None, 'region_homeworld'
        for tok, (rn, rb) in REGION.items():
            if tok in low:
                gname, bg = rn, rb
                break
        if gname is None:
            gname, bg = TYPE.get(fam, ('其他', 'region_homeworld'))
        label = display_name(raw, gname)
        # 同名消歧：1,214 首里难免撞名，撞了就带上级号
        base = label
        if label in used_names:
            used_names[base] += 1
            label = '%s (%d)' % (base, used_names[base])
        else:
            used_names[base] = 1
        g = groups.setdefault(gname, {'group': gname, 'bg': 'bg/%s.jpg' % bg,
                                      'bg_blur': 'bg/%s_blur.jpg' % bg, 'tracks': []})
        g['tracks'].append({'name': label, 'pck': id2pck[mid], 'id': '%08x' % mid})
        total += 1

    out = sorted(groups.values(), key=lambda g: ORDER.index(g['group']) if g['group'] in ORDER else 99)
    print()
    print('曲库合计 %d 首，分组 %d 个：' % (total, len(out)))
    for g in out:
        print('   %-8s %4d 首   %s' % (g['group'], len(g['tracks']), g['bg']))
    print()
    print('样例（每个分组前 3 首）:')
    for g in out:
        print('   [%s]' % g['group'])
        for t in g['tracks'][:3]:
            print('        %-34s %s' % (t['name'], t['pck']))
    dup = {k: v for k, v in used_names.items() if v > 1}
    print()
    print('同名消歧 %d 组' % len(dup))

    if not APPLY:
        print('\n（试算，未写入。加 --apply）')
        return
    idx = json.load(io.open(IDX, encoding='utf-8'))
    idx['music'] = out
    json.dump(idx, io.open(IDX, 'w', encoding='utf-8'), ensure_ascii=False)
    print('\n已写回 %s：音乐 %d 首' % (IDX, total))


if __name__ == '__main__':
    main()
