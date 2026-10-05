# -*- coding: utf-8 -*-
"""生成安装向导图像（背景 = 最新祈愿角色立绘）：
   installer-ui\\banner.bmp       493x58   内页顶部横幅
   installer-ui\\dialog.bmp       493x312  欢迎/完成页
   installer-ui\\background.bmp   493x312  其余内页背景"""
import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = r'E:\Genshin\Collections\VoicePlayer'
OUT = os.path.join(ROOT, 'installer-ui')
os.makedirs(OUT, exist_ok=True)
ART = os.path.join(ROOT, 'assets', 'bg', 'orig', 'vodyanitsa.png')   # 7.1 祈愿（沃雅妮莎）
ICO = os.path.join(ROOT, 'app-src', 'VoicePlayer', 'app.ico')
FONT_B = r'C:\Windows\Fonts\msyhbd.ttc'
FONT_R = r'C:\Windows\Fonts\msyh.ttc'

NAVY = (14, 22, 42)
NAVY2 = (26, 38, 68)
GOLD = (222, 186, 110)
WHITE = (247, 248, 252)

art = Image.open(ART).convert('RGBA')
a = art.getchannel('A').point(lambda v: 255 if v >= 8 else 0)
bbox = a.getbbox()
art = art.crop(bbox) if bbox else art
AW, AH = art.size

def fit_box(im, w, h):
    r = max(w / im.width, h / im.height)
    im2 = im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)
    x = (im2.width - w) // 2
    y = (im2.height - h) // 2
    return im2.crop((x, y, x + w, y + h))

def over(base, top, pos):
    base.alpha_composite(top, pos)

# ---------- banner 493x58 ----------
W, H = 493, 58
ban = Image.new('RGBA', (W, H), NAVY + (255,))
g = Image.new('RGBA', (W, H))
gd = ImageDraw.Draw(g)
for x in range(W):
    t = x / W
    c = tuple(int(NAVY[i] + (NAVY2[i] - NAVY[i]) * t) for i in range(3))
    gd.line([(x, 0), (x, H)], fill=c + (255,))
ban = g
# 右侧立绘切片（头部区域）
head = art.crop((int(AW * 0.18), 0, int(AW * 0.82), int(AH * 0.30)))
strip = fit_box(head, 190, H)
strip = strip.filter(ImageFilter.GaussianBlur(0.4))
mask = Image.new('L', (190, H), 0)
md = ImageDraw.Draw(mask)
for x in range(190):
    md.line([(x, 0), (x, H)], fill=int(255 * min(1, x / 90)))
strip.putalpha(mask)
over(ban, strip, (W - 190, 0))
# 图标 + 标题
ico = Image.open(ICO).convert('RGBA')
ico = ico.resize((36, 36), Image.LANCZOS)
over(ban, ico, (14, (H - 36) // 2))
d = ImageDraw.Draw(ban)
d.text((60, 8), '原神语音播放器', font=ImageFont.truetype(FONT_B, 20), fill=(255, 255, 255))
d.text((61, 33), '全量语音 · 地区音乐 · 本地播放', font=ImageFont.truetype(FONT_R, 12), fill=(196, 206, 226))
d.rectangle([0, H - 3, W, H], fill=GOLD)
ban.convert('RGB').save(os.path.join(OUT, 'banner.bmp'))
ban.convert('RGB').resize((493, 58)).save(os.path.join(OUT, 'preview-banner.png'))

# ---------- dialog 493x312（左侧立绘栏 + 右侧浅色文字区）----------
W, H = 493, 312
dlg = Image.new('RGBA', (W, H), WHITE + (255,))
LW = 168
left = Image.new('RGBA', (LW, H))
ld = ImageDraw.Draw(left)
for y in range(H):
    t = y / H
    c = tuple(int(NAVY[i] + (NAVY2[i] - NAVY[i]) * t) for i in range(3))
    ld.line([(0, y), (LW, y)], fill=c + (255,))
body = fit_box(art, LW + 40, H)
body = body.resize((int(body.width * 1.0), int(body.height * 1.0)))
x0 = (body.width - LW) // 2
body = body.crop((x0, 0, x0 + LW, H))
# 底部渐隐进深色
fm = Image.new('L', (LW, H), 255)
fd = ImageDraw.Draw(fm)
for y in range(H - 70, H):
    fd.line([(0, y), (LW, y)], fill=int(255 * (1 - (y - (H - 70)) / 70 * 0.55)))
body.putalpha(body.getchannel('A').point(lambda v: v).point(lambda v: v))  # keep
body_rgba = body
left.alpha_composite(body_rgba)
dlg.alpha_composite(left, (0, 0))
d = ImageDraw.Draw(dlg)
d.rectangle([LW, 0, LW + 2, H], fill=GOLD)
# 右侧浅色区右下角淡雅水印
wm = fit_box(art, 150, 190)
wm = wm.copy()
alpha = wm.getchannel('A').point(lambda v: int(v * 0.10))
wm.putalpha(alpha)
dlg.alpha_composite(wm, (W - 150, H - 190))
dlg.convert('RGB').save(os.path.join(OUT, 'dialog.bmp'))
dlg.convert('RGB').save(os.path.join(OUT, 'preview-dialog.png'))

# ---------- background 493x312（浅色，右下淡立绘）----------
bg = Image.new('RGBA', (W, H), WHITE + (255,))
bd = ImageDraw.Draw(bg)
for y in range(H):
    t = y / H
    c = tuple(int(WHITE[i] + ((232, 236, 246)[i] - WHITE[i]) * t) for i in range(3))
    bd.line([(0, y), (W, y)], fill=c + (255,))
wm = fit_box(art, 240, 300)
alpha = wm.getchannel('A').point(lambda v: int(v * 0.12))
wm.putalpha(alpha)
bg.alpha_composite(wm, (W - 235, H - 295))
bd.rectangle([0, 0, W, 3], fill=GOLD)
bg.convert('RGB').save(os.path.join(OUT, 'background.bmp'))
bg.convert('RGB').save(os.path.join(OUT, 'preview-background.png'))

print('banner:', Image.open(os.path.join(OUT, 'banner.bmp')).size)
print('dialog:', Image.open(os.path.join(OUT, 'dialog.bmp')).size)
print('background:', Image.open(os.path.join(OUT, 'background.bmp')).size)
