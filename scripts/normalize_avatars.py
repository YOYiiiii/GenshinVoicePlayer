# -*- coding: utf-8 -*-
"""统一头像圆为 90px + 角色图下缘贴圆底。

用户要求：
  1) 所有头像的可见圆统一为 **90px**（当前 gcg_* 是 96px、兜底是 90px、角色图没有烘焙圆 → 三者不一致）
  2) 角色图**下缘对齐圆底**，不要在圆底留黑底

做法（全部从原始备份重处理，避免二次缩放）：
  · 本来就是圆的图标（环覆盖率 >=0.90）→ 整体缩到 90px，居中
  · 角色半身图 → 求一个最大倍率 s，使"头部带顶行的中间 50%"落在 90px 圆内，
    然后把**内容 bbox 的底边**对齐到圆的底边（y=92）、内容 bbox 水平居中
  · 兜底渐变头像 → 直接按 90px 圆重绘
最后统一裁进 90px 圆，圆外填底色 (11,16,26)。

用法：py scripts/normalize_avatars.py [--apply]
"""
import io, os, sys, math, json, colorsys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fallback_avatar_style import render as render_fallback_shared  # noqa

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AV = os.path.join(ROOT, 'assets', 'bg', 'avatar')
DATA = os.path.join(ROOT, 'data')
APPLY = '--apply' in sys.argv
BG = (11, 16, 26)
FONT = r'C:\Windows\Fonts\msyhbd.ttc'
DIAM = 96                      # 目标圆直径：**铺满整帧**
#   之前取 90（内缩 3px）会让"本来就是圆的图标"四周多出一圈深色内缩环，
#   看起来像描边；用户要的是无描边 + 原图不被裁切 → 统一按整帧 96px。
R = DIAM / 2.0                 # 45
CX = CY = 47.5
INSET = (96 - DIAM) / 2.0      # 0.0：圆铺满整帧
BOTTOM_Y = INSET + DIAM - 1    # 92：圆的底边所在行（原来错用了 DIAM-INSET=87）
MARGIN = 2.0                   # 圆内再留一点，避免压线
CIRCULAR_RING = 0.90
MIN_SCALE = 0.72

STORY_GLYPH = {
    'story_lq': '传', 'story_aq': '魔', 'story_coop': '合', 'story_ingame': '界',
    'story_eq': '活', 'story_freetalk': '聊', 'story_wq': '世', 'story_beyd': '星',
    'story_anecdote': '轶', 'story_tower': '塔', 'story_spice': '礼',
    'story_gcg_monster': '牌',
}


def is_bg(p, tol=14):
    return abs(p[0]-BG[0]) <= tol and abs(p[1]-BG[1]) <= tol and abs(p[2]-BG[2]) <= tol


def ring_cov(im, r=44, n=96):
    hit = tot = 0
    for i in range(n):
        a = 2*math.pi*i/n
        x = int(round(47.5 + r*math.cos(a)))
        y = int(round(47.5 + r*math.sin(a)))
        if 0 <= x < im.width and 0 <= y < im.height:
            tot += 1
            if not is_bg(im.getpixel((x, y))):
                hit += 1
    return hit/max(1, tot)


def content_bbox(im):
    px = im.load()
    x0, y0, x1, y1 = im.width, im.height, -1, -1
    for y in range(im.height):
        for x in range(im.width):
            if not is_bg(px[x, y]):
                if x < x0: x0 = x
                if y < y0: y0 = y
                if x > x1: x1 = x
                if y > y1: y1 = y
    return None if x1 < 0 else (x0, y0, x1, y1)


def top_row(im, bb):
    """内容里第一个"够密"的行（跳过只有几像素的呆毛/挂件）。"""
    x0, y0, x1, y1 = bb
    px = im.load()
    for y in range(y0, min(y0 + 20, y1 + 1)):
        if sum(1 for x in range(x0, x1 + 1) if not is_bg(px[x, y])) >= 8:
            return y
    return y0


def base_scale(im, bb, top):
    """求最大倍率 s：内容底边贴到圆底(y=92)、内容水平居中时，
    顶行中间 50% 仍落在 90px 圆内。"""
    x0, y0, x1, y1 = bb
    cx = (x0 + x1) / 2.0
    px = im.load()
    xs = [x for x in range(x0, x1 + 1) if not is_bg(px[x, top])]
    if not xs:
        return 1.0
    xl, xr = min(xs), max(xs)
    span = max(1, xr - xl)
    half = max(abs((xl + span*0.25) - cx), abs((xr - span*0.25) - cx))
    limit = R - MARGIN
    s = 1.0
    while s > MIN_SCALE:
        dy = BOTTOM_Y - s * (y1 - top) - CY         # 内容底边=圆底 时顶行的 y 相对圆心
        if (s*half)**2 + dy*dy <= limit*limit:
            return s
        s -= 0.005
    return MIN_SCALE


def circle_mask(d=DIAM):
    m = Image.new('L', (96, 96), 0)
    ImageDraw.Draw(m).ellipse((INSET, INSET, INSET + d - 1, INSET + d - 1), fill=255)
    return m


def paste_clip(canvas, img, x, y):
    canvas.paste(img, (int(round(x)), int(round(y))))
    out = Image.new('RGB', (96, 96), BG)
    out.paste(canvas, (0, 0), circle_mask())
    return out


def main():
    import glob
    backups = sorted(glob.glob(r'E:\AI_Project\deepseek-harness\.backup\avatars-*'))
    if not backups:
        print('!! 找不到原始头像备份'); return
    src = backups[-1]
    print('原始备份: %s' % src)
    idx = json.load(io.open(os.path.join(DATA, 'index.json'), encoding='utf-8'))
    name_of = {c['id']: (c.get('name') or c['id']) for c in idx['characters']}
    fb = set(json.load(io.open(os.path.join(DATA, 'fallback-avatars.json'), encoding='utf-8'))['ids'])
    font = ImageFont.truetype(FONT, 42)

    stat = {'兜底重绘': 0, '原样保留': 0, '角色图下缘对齐': 0, '未变': 0}
    scales = []
    for cid in sorted(name_of):
        p = os.path.join(src, cid + '.png')
        if cid in fb:
            out = render_fallback_shared(cid, name_of[cid], font)
            stat['兜底重绘'] += 1
        elif not os.path.exists(p):
            stat['未变'] += 1
            continue
        else:
            im = Image.open(p).convert('RGB')
            if ring_cov(im) >= CIRCULAR_RING:
                # 本来就是圆的：**原图完全不动**（不缩放、不裁切），
                # 它自带铺满整帧的圆，正好与其它头像的圆一致
                out = im.copy()
                stat['原样保留'] += 1
            else:
                bb = content_bbox(im)
                if not bb:
                    stat['未变'] += 1
                    continue
                top = top_row(im, bb)
                s = base_scale(im, bb, top)
                scales.append((cid, s))
                w = max(1, int(round(96*s)))
                small = im.resize((w, w), Image.LANCZOS)
                x0, y0, x1, y1 = bb
                cx = (x0 + x1)/2.0
                paste_x = CX - cx*s                      # 内容水平居中
                paste_y = BOTTOM_Y - y1*s                 # 内容底边 = 圆底 y=92
                out = paste_clip(Image.new('RGB', (96, 96), BG), small, paste_x, paste_y)
                stat['角色图下缘对齐'] += 1
        if APPLY:
            out.save(os.path.join(AV, cid + '.png'), 'PNG')
    print()
    for k, v in stat.items():
        print('   %-16s %d' % (k, v))
    if scales:
        sc = sorted(s for _, s in scales)
        print('   角色图倍率: 最小 %.3f 中位 %.3f 最大 %.3f' % (sc[0], sc[len(sc)//2], sc[-1]))
    if not APPLY:
        print('\n（试算，未写入。加 --apply）')


if __name__ == '__main__':
    main()
