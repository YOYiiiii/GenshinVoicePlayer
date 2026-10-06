# -*- coding: utf-8 -*-
"""为没有头像的条目生成兜底图标，使左列表所有行的节奏一致。

风格（第二版，按反馈调整）：
  · 去掉描边（第一版的浅色圆环显得老气）
  · 改用**单色渐变**：同一色相，上浅下深，纵向渐变
  · 名字首字居中（群像条目用类型字：传/魔/合/界/活/聊/星/轶/塔/礼/牌）

尺寸与底色对齐现有头像：96x96、RGB、底色 (11,16,26)。

用法：py scripts/make_fallback_avatars.py [--apply]
      （重复运行会按 data/fallback-avatars.json 里记录的 id 重新生成）
"""
import io, os, sys, json, colorsys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fallback_avatar_style import render as render_shared, STORY_GLYPH  # noqa

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
AV = os.path.join(ROOT, 'assets', 'bg', 'avatar')
RECORD = os.path.join(DATA, 'fallback-avatars.json')
FONT = r'C:\Windows\Fonts\msyhbd.ttc'
BG = (11, 16, 26)
APPLY = '--apply' in sys.argv

# 群像条目用类型字，比取名字首字更好认
STORY_GLYPH = {
    'story_lq': '传', 'story_aq': '魔', 'story_coop': '合', 'story_ingame': '界',
    'story_eq': '活', 'story_freetalk': '聊', 'story_wq': '世', 'story_beyd': '星',
    'story_anecdote': '轶', 'story_tower': '塔', 'story_spice': '礼',
    'story_gcg_monster': '牌',
}


def main():
    idx = json.load(io.open(os.path.join(DATA, 'index.json'), encoding='utf-8'))
    name_of = {c['id']: (c.get('name') or c['id']) for c in idx['characters']}
    prev = set()
    if os.path.exists(RECORD):
        prev = set(json.load(io.open(RECORD, encoding='utf-8')).get('ids', []))
    have = {os.path.splitext(f)[0].lower() for f in os.listdir(AV)}
    todo = [c['id'] for c in idx['characters']
            if c['id'].lower() not in have or c['id'] in prev]
    print('待生成 %d 个（缺图 %d + 重生成 %d），字体 %s'
          % (len(todo), sum(1 for c in idx['characters'] if c['id'].lower() not in have),
             len([i for i in todo if i in prev]), os.path.exists(FONT)))
    if not todo:
        return
    font = ImageFont.truetype(FONT, 44)
    done = []
    for cid in todo:
        im = render_shared(cid, name_of.get(cid, cid), font)
        done.append(cid)
        if APPLY:
            im.save(os.path.join(AV, cid + '.png'), 'PNG')
        else:
            im.save(os.path.join(r'E:\AI_Project\deepseek-harness\dsh-theme',
                                 'newav-' + cid + '.png'), 'PNG')
    ids = sorted(set(prev) | set(done))
    if APPLY:
        json.dump({'ids': ids}, io.open(RECORD, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('已写入 %d 个头像（记入 %s）' % (len(done), os.path.basename(RECORD)))
    else:
        print('（试算，样例输出到 dsh-theme\\newav-*.png。加 --apply 写入）')


if __name__ == '__main__':
    main()
