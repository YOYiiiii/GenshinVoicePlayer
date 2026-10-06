# -*- coding: utf-8 -*-
"""兜底头像的配色与绘制（供 make_fallback_avatars / normalize_avatars 共用）。

配色改为**高级灰**：低饱和（莫兰迪灰调）、中低明度，上浅下深做纵向渐变。
之前按 id 哈希取高饱和色相，出来的颜色偏艳、显老气。

统一规则：
  · 96×96、RGB、底色 (11,16,26)
  · 圆铺满整帧（0,0,95,95），**无描边**
  · 纵向渐变：同一色相上浅下深（L ±0.07）
  · 名字首字居中（群像条目用类型字）
"""
import math

from PIL import Image, ImageDraw, ImageFont

BG = (11, 16, 26)
FONT = r'C:\Windows\Fonts\msyhbd.ttc'

# 高级灰 / 莫兰迪灰调：低饱和、中低明度，冷灰与暖灰交替
PALETTE = [
    (0x6B, 0x72, 0x80),   # 冷灰
    (0x7A, 0x72, 0x69),   # 暖褐灰
    (0x6E, 0x7A, 0x79),   # 鼠尾草灰
    (0x75, 0x70, 0x7E),   # 藕灰
    (0x7C, 0x82, 0x88),   # 钢灰
    (0x6F, 0x7B, 0x6E),   # 苔灰
    (0x83, 0x7A, 0x76),   # 玫瑰灰
    (0x6A, 0x71, 0x80),   # 石板灰
    (0x7E, 0x7A, 0x6E),   # 卡其灰
    (0x72, 0x78, 0x79),   # 中性灰
]

STORY_GLYPH = {
    'story_lq': '传', 'story_aq': '魔', 'story_coop': '合', 'story_ingame': '界',
    'story_eq': '活', 'story_freetalk': '聊', 'story_wq': '世', 'story_beyd': '星',
    'story_anecdote': '轶', 'story_tower': '塔', 'story_spice': '礼',
    'story_gcg_monster': '牌',
}

GLYPH_COLOR = (243, 245, 248)     # 近白，压在高级灰上对比足够


def glyph_of(cid, name):
    if cid in STORY_GLYPH:
        return STORY_GLYPH[cid]
    for ch in (name or cid):
        if '\u4e00' <= ch <= '\u9fff':
            return ch
    for ch in (name or cid):
        if ch.isalnum():
            return ch.upper()
    return cid[:1].upper()


def _hash(cid):
    h = 0
    for ch in cid:
        h = (h * 131 + ord(ch)) & 0xFFFFFFFF
    return h


def _shift(rgb, dl):
    """保持色相，只调明度：返回上浅/下深两端颜色。"""
    r, g, b = (c / 255.0 for c in rgb)
    mx, mn = max(r, g, b), min(r, g, b)
    l = (mx + mn) / 2.0
    if mx == mn:
        h = s = 0.0
    else:
        d = mx - mn
        s = d / (2.0 - mx - mn) if l > 0.5 else d / (mx + mn)
        if mx == r:
            h = ((g - b) / d + (6 if g < b else 0)) / 6.0
        elif mx == g:
            h = ((b - r) / d + 2) / 6.0
        else:
            h = ((r - g) / d + 4) / 6.0

    def hls_to_rgb(hh, ll, ss):
        import colorsys
        return colorsys.hls_to_rgb(hh, max(0.0, min(1.0, ll)), ss)

    top = tuple(int(c * 255) for c in hls_to_rgb(h, l + dl, s))
    bot = tuple(int(c * 255) for c in hls_to_rgb(h, l - dl, s))
    return top, bot


def render(cid, name, font=None):
    """画一个 96×96 的高级灰渐变圆形头像（无描边，文字居中）。"""
    if font is None:
        font = ImageFont.truetype(FONT, 42)
    base = PALETTE[_hash(cid) % len(PALETTE)]
    top, bot = _shift(base, 0.07)

    im = Image.new('RGB', (96, 96), BG)
    grad = Image.new('RGB', (96, 96), BG)
    gd = ImageDraw.Draw(grad)
    for y in range(96):
        t = y / 95.0
        gd.line([(0, y), (96, y)],
                fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    mask = Image.new('L', (96, 96), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, 95, 95), fill=255)   # 铺满整帧
    im.paste(grad, (0, 0), mask)

    # 文字精确居中：先量字形 bbox，再按 bbox 中心对齐到 (47.5, 47.5)
    g = glyph_of(cid, name)
    tmp = Image.new('L', (96, 96), 0)
    ImageDraw.Draw(tmp).text((48, 48), g, font=font, fill=255, anchor='mm')
    bb = tmp.getbbox()
    dx = dy = 0
    if bb:
        dx = 47.5 - (bb[0] + bb[2] - 1) / 2.0
        dy = 47.5 - (bb[1] + bb[3] - 1) / 2.0
    ImageDraw.Draw(im).text((48 + dx, 48 + dy), g, font=font,
                            fill=GLYPH_COLOR, anchor='mm')
    return im
