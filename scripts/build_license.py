# -*- coding: utf-8 -*-
import io

TEXT = """「原神语音播放器」用户须知与许可

1. 本软件为免费个人向工具，用于播放本机《原神》客户端内的语音与音乐资源，安装后不附带任何游戏资源文件。
2. 游戏音频与美术资源版权归米哈游（miHoYo / HoYoverse）所有；本软件运行时从您本机的游戏目录实时读取这些资源。
3. 本软件仅供个人学习与欣赏使用，请勿用于任何商业用途，请勿二次分发游戏资源。
4. 本软件按“现状”提供，不附带任何明示或暗示的担保。

点击“我接受”后继续安装；若不同意，请点击“我不接受”退出安装。
"""

def esc(s):
    out = []
    for ch in s:
        o = ord(ch)
        if o < 128:
            if ch in '\\{}':
                out.append('\\' + ch)
            elif ch == '\n':
                out.append('\\par\n')
            else:
                out.append(ch)
        else:
            out.append('\\u%d?' % (o if o < 32768 else o - 65536))
    return ''.join(out)

rtf = r'{\rtf1\ansi\ansicpg936\deff0{\fonttbl{\f0\fnil\fcharset134 Microsoft YaHei;}}' + '\n' + \
      r'\viewkind4\uc1\pard\f0\fs20 ' + esc(TEXT) + '}'

io.open(r'E:\Genshin\Collections\VoicePlayer\license.rtf', 'w', encoding='ascii').write(rtf)
print('license.rtf written')
