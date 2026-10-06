# 原神语音播放器

> 本地全量语音 & 地区音乐播放器 · 全部音频从游戏包**实时解包**，本地零音频存储

[![.NET](https://img.shields.io/badge/.NET-10-512BD4)](https://dotnet.microsoft.com/) [![WPF](https://img.shields.io/badge/UI-WPF-512BD4)](#) [![Inno Setup](https://img.shields.io/badge/Installer-Inno%20Setup%206-blue)](https://jrsoftware.org/isinfo.php) [![Platform](https://img.shields.io/badge/Platform-Windows-0078D6)](#) [![Release](https://img.shields.io/badge/Release-v1.0.0-2ea44f)](https://github.com/YOYiiiii/GenshinVoicePlayer/releases/tag/v1.0.0)

基于 WPF（.NET 10）的《原神》语音浏览器：**169,463 条语音 + 1,214 首音乐**，按需从本机
`YuanShen_Data\StreamingAssets\AudioAssets` 解包 `.wem` → WAV 实时播放，不预转码、不占额外磁盘。

---

## 📥 下载使用

从 **[Releases](https://github.com/YOYiiiii/GenshinVoicePlayer/releases/tag/v1.0.0)** 下载
`VoicePlayer-Setup-1.0.0.exe`（**70.7 MB**）：

- Inno Setup 6 单文件安装程序，**无需管理员权限**，可自选安装路径
  （默认 `D:\Program Files (x86)\原神语音播放器`）
- 已安装状态下再次双击 = 维护对话框：**更新 / 修复** · **卸载** · 取消
- 静默安装 `安装程序.exe /VERYSILENT /SUPPRESSMSGBOXES`；静默卸载 `unins000.exe /VERYSILENT`
- **开箱即用**：安装包内含播放器与索引数据；播放时需本机已安装《原神》，
  或通过右键【导入数据源…】指定 `AudioAssets` 目录

### 运行要求

| 项 | 要求 |
|---|---|
| 系统 | Windows 10 / 11（x64） |
| 运行时 | 无需安装（自包含发布） |
| 游戏 | 需本机已安装《原神》，或指定 `AudioAssets` 目录 |

### 命令行参数

```
VoicePlayer.exe                                 直接启动
VoicePlayer.exe --open aino                     启动并打开指定条目
VoicePlayer.exe --music 璃月                     启动并打开指定音乐分组
VoicePlayer.exe --search 温迪                    启动并执行全量搜索

解码链自检（输出 selftest.txt）：
VoicePlayer.exe --selftest 40f0e2d5cfe53acb Chinese\External8.pck    语音
VoicePlayer.exe --selftest 30d94e38 Music24.pck                      音乐
```

---

## ✨ 功能

- 🎧 **全量语音**：169,463 条 / 700 个条目，按 角色 / 剧情角色 / 七圣召唤 / 剧情群像 分组
  （空/荧置顶角色组，派蒙列剧情角色组首位）
- 🎵 **地区音乐**：1,214 首 / 16 分区，经 `hk4e.map`(7.1) 映射为 Wwise ID 实时解包
  （首次解码数秒，缓存后秒开）
- 🔍 **搜索**：匹配 条目名 / 条目 id / 官方幕名 / 台词 / 音频路径；空格分隔多关键词按「与」组合
  （如 `爱诺 甜`）；全角半角通用；按相关度排序（条目名 > 幕名 > 台词 > 路径）；也可只搜当前角色
- 🔤 **别名检索**：台词里的场景名也能搜到条目——搜「黑蛋」命中「宁宁·黑蛋」、「散兵」命中
  「流浪者」、「埃德」命中「克洛达尔」、「男主」命中「空」、「臻冰通话器」命中「凯瑟琳」
- 🗂 **官方中文幕名分类**：`传说任务 · 天下人之章 第二幕 · 涤荡秽浊之光` 这类分组名取自官方
  `ChapterExcelConfigData`，非猜测；无任何裸露的任务代码
- 🖼 **头像**：700 张统一 96×96 圆形；本来就是圆的图标（七圣召唤魔物）原图不动，
  角色半身图按内容缩放使头顶不被圆框切掉、下缘贴齐圆底；无官方立绘的条目用
  高级灰单色渐变圆 + 名字首字
- 📤 导出 WAV（▶ 右键）· 悬停自动预解码 · 无边框云母质感窗口 · 现代细滚动条
- 🎨 配色与字号对齐 DeepSeek Harness 设计令牌；搜索框用矢量放大镜图标（不依赖图标字体）

### 数据规模

| 项 | 数量 |
|---|---:|
| 语音 | **169,463** 条 |
| 条目 | **700** 个（角色 122 / 剧情角色 491 / 七圣召唤 75 / 剧情群像 12） |
| 音乐 | **1,214** 首 / 16 分区 |
| 头像 | 700 张（缺 0） |

---

## 📂 仓库内容

本仓库**只包含代码与构建脚本**，不含游戏素材与台词数据（版权归米哈游，不在本仓库分发）：

```
app-src\        WPF 源码（dotnet publish -r win-x64 --self-contained true 重建）
scripts\        数据管线（Python 3）+ 安装包定义（Inno Setup 6）
  tools\        hk4e.map（Wwise 事件名映射，曲库构建用）
config.json.example   数据源配置样板
README-说明.txt        随安装包分发的使用说明
license.rtf            安装向导的许可页
```

下列内容**仅在本地保留**（已加入 `.gitignore`，可随时由脚本重建，故未纳入仓库）：

| 内容 | 说明 |
|---|---|
| `app\` | 编译产物（由 `app-src\` 发布而来） |
| `assets\` | 头像与背景图（由 `scripts\fetch_original_art.py` 生成） |
| `data\` | 索引与台词文本（由 `scripts\` 管线生成） |
| `dist\` | 安装包输出（成品通过 Releases 分发） |
| `installer-ui\` | 安装向导品牌图 |
| `技术栈与架构说明.md` | 内部架构文档 |

### 安装后的目录结构

```
<安装目录>\
├─ app\           播放器（含 vgmstream 解码器）
├─ data\          index.json + entries\*.json（700 条目）+ aliases.json
├─ assets\bg\     头像 avatar\（700 张）+ 地区背景 + 角色模糊背景
├─ scripts\       数据管线与安装包定义（便于自行重建数据）
├─ config.json    音频数据源（由【导入数据源…】生成）
└─ README-说明.txt / 技术栈与架构说明.md
```

---

## 🔧 从源码重建

```bat
:: 播放器（自包含，免运行时）
dotnet publish app-src\VoicePlayer -c Release -r win-x64 --self-contained true -o app

:: 安装包（需先有 app\ data\ assets\）
"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" scripts\installer_inno.iss
```

## 🔄 重建数据

需要两样外部输入：**官方数据 dump** 与**本机游戏音频**。本仓库不含映射表——
映射表由同目录的 `Voice-Mapping` 工程生成（`..\Voice-Mapping\`）。

```bat
powershell -File ..\Voice-Mapping\scripts\update-official-data.ps1
py ..\Voice-Mapping\scripts\build-voice-map.py
py scripts\build_player_data2.py                    :: 基础条目与索引
py scripts\missing_characters.py  --min=20 --apply  :: 找出漏掉的角色
py scripts\add_speaker_entries.py --apply           :: 搬成独立条目
py scripts\build_speaker_aliases.py                 :: 别名表
py scripts\build_quest_codes.py                     :: 任务代码 → 官方中文幕名
py scripts\normalize_avatars.py   --apply           :: 头像
py scripts\build_music_full.py    --apply           :: 曲库
py scripts\build_player_data3.py  --apply           :: 分类/标签/统计（最后跑）
```

脚本用环境变量覆盖默认路径（默认落在系统临时目录 / 官方安装路径）：

| 变量 | 用途 | 默认 |
|---|---|---|
| `ANIMEGAME_DATA` | AnimeGameData dump 检出目录 | `%TEMP%\opencode\AnimeGameData` |
| `ANIMEGAME_TMP` | dump 的父目录 | `%TEMP%\opencode` |
| `TEXTURE2D_DIR` | 解包素材（Texture2D 分类结果） | `..\Texture2D-classified` |
| `AUDIO_ROOT` | 游戏音频目录 | 官方默认安装路径 |

音频无需重转码：播放时自动从新 pck 解包，仅索引需要刷新。

---

## 🧱 技术栈

| 层 | 技术 |
|---|---|
| 语言 / 运行时 | C# / .NET 10（WPF，自包含发布） |
| 音频解码 | vgmstream-cli（`.wem` → WAV）+ WPF MediaPlayer |
| 容器解析 | 自研 AKPK 解析器（语音按 64 位 FNV-1 哈希 / 音乐按 32 位 Wwise ID 定位） |
| 数据管线 | Python 3（映射表 / 条目 / 别名 / 官方幕名 / 头像 / 曲库离线构建） |
| 官方数据 | [AnimeGameData](https://github.com/DimbreathBot/AnimeGameData)（CNRELWin7.1.0，与本机客户端同为 48379043 修订） |
| 安装包 | Inno Setup 6（单文件 exe、维护对话框、静默参数） |

**播放链路**：条目只存「游戏内路径 + pck + 哈希」→ 定位 AKPK 分区切出 `.wem`
→ vgmstream 解码为 WAV（缓存于 `%TEMP%\VoicePlayerCache`，超 1 GB 或超 5 天自动清理）
→ `MediaPlayer` 播放。

---

## ❓ 常见问题

**Q：为什么仓库里没有 `data\`、`assets\`、安装包？**
这些内容含游戏台词文本与官方立绘素材（版权归米哈游），且都可由 `scripts\` 重建，
因此不在本仓库分发。想直接用请下载 Releases 里的安装包。

**Q：安装后提示找不到音频 / 播放没声音？**
程序默认读取官方安装路径。若游戏装在别处，右键文本 →【导入数据源…】选择
`…\YuanShen_Data\StreamingAssets\AudioAssets`，或手工建 `config.json`：
`{ "audioRoot": "你的AudioAssets完整路径" }`。

**Q：某条语音没有文字？**
少量条目游戏本身未提供字幕（战斗语气词、过场、七圣召唤音效等），程序会用可读中文标签
代替文件名（如 `普通攻击 · 03`）。

**Q：首次播放音乐要等几秒？**
音乐曲目较大，需实时解码；解码结果会缓存，之后同一首秒开。

**Q：能导出吗？**
可以。`▶` 右键 → 导出为 WAV。

---

## 🙏 数据来源与致谢

- 音频：本机《原神》客户端 `AudioAssets`（运行时读取，不分发）
- 官方数据：[DimbreathBot/AnimeGameData](https://github.com/DimbreathBot/AnimeGameData)
  —— 任务幕名 / 章节名 / 任务名 / NPC 名
- 曲名映射：`hk4e.map`（[AnimeWwise](https://github.com/SilentNightSound/AnimeWwise) 仓库，7.1 版）
- 解码器：[vgmstream](https://github.com/vgmstream/vgmstream)
- 安装器：[Inno Setup](https://jrsoftware.org/isinfo.php)（简体中文语言包来自社区维护翻译）

---

## 📄 许可与免责

1. 本软件为免费个人向工具，用于播放本机《原神》客户端内的语音与音乐资源；
   安装包**不附带任何游戏资源文件**。
2. 游戏音频与美术资源版权归**米哈游（miHoYo / HoYoverse）**所有；本软件运行时
   从您本机的游戏目录**实时读取**这些资源。
3. 本软件仅供**个人学习与欣赏**使用，请勿用于任何商业用途，请勿二次分发游戏资源。
4. 本软件按「现状态」提供，不附带任何明示或暗示的担保。

本仓库仅分发**代码**，未附开源许可证；如需引用请注明出处。
