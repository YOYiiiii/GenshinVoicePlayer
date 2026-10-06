# 原神语音播放器 v2

> 本地全量语音 & 地区音乐播放器 · 全部音频从游戏包**实时解包**，本地零音频存储

[![.NET](https://img.shields.io/badge/.NET-10-512BD4)](https://dotnet.microsoft.com/) [![WPF](https://img.shields.io/badge/UI-WPF-512BD4)](#) [![Inno Setup](https://img.shields.io/badge/Installer-Inno%20Setup%206-blue)](https://jrsoftware.org/isinfo.php) [![Platform](https://img.shields.io/badge/Platform-Windows-0078D6)](#)

基于 WPF（.NET 10）的《原神》语音浏览器：**169,463 条语音 + 1,214 首音乐**，按需从本机
`YuanShen_Data\StreamingAssets\AudioAssets` 解包 `.wem` → WAV 实时播放，不预转码、不占额外磁盘。

## 📥 下载使用

从 [Releases](https://github.com/YOYiiiii/GenshinVoicePlayer/releases/tag/v1.0.0) 下载
`VoicePlayer-Setup-1.0.0.exe`（**70.7 MB**）：

- Inno Setup 6 单文件安装程序，**无需管理员权限**，可自选安装路径
- 已安装状态下再次双击 = 维护对话框：**更新/修复** · **卸载** · 取消
- 静默安装 `安装程序.exe /VERYSILENT /SUPPRESSMSGBOXES`；静默卸载 `unins000.exe /VERYSILENT`
- 安装包内含播放器与索引数据，**开箱即用**；运行需本机已安装《原神》，或通过
  右键【导入数据源…】指定 `AudioAssets` 目录

## 📂 本仓库内容

本仓库**只包含代码与构建脚本**，不含游戏素材与台词数据（版权归米哈游，不在本仓库分发）：

```
app-src\        WPF 源码（dotnet publish -r win-x64 --self-contained true 重建）
scripts\        数据管线（Python 3）+ 安装包定义（Inno Setup 6）
  tools\        hk4e.map（Wwise 事件名映射，曲库构建用）
config.json.example   数据源配置样板
README-说明.txt        随安装包分发的使用说明
license.rtf            安装向导的许可页
```

下列内容**仅在本地保留**（已加入 `.gitignore`，可随时由脚本重建）：

| 内容 | 说明 |
|---|---|
| `app\` | 编译产物（由 `app-src\` 发布而来） |
| `assets\` | 头像与背景图（由 `scripts\fetch_original_art.py` 生成） |
| `data\` | 索引与台词文本（由 `scripts\` 管线生成） |
| `dist\` | 安装包输出（成品走 Releases） |
| `installer-ui\` | 安装向导品牌图 |
| `技术栈与架构说明.md` | 内部架构文档 |

## 🔧 从源码重建

```bat
:: 播放器（自包含，免运行时）
dotnet publish app-src\VoicePlayer -c Release -r win-x64 --self-contained true -o app

:: 安装包
"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" scripts\installer_inno.iss
```

## 🔄 重建数据（需要官方数据与本机游戏）

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
`ANIMEGAME_DATA`、`ANIMEGAME_TMP`、`TEXTURE2D_DIR`、`AUDIO_ROOT`

音频无需重转码：播放时自动从新 pck 解包，仅索引需要刷新。

## 🧱 技术栈

| 层 | 技术 |
|---|---|
| 语言 / 运行时 | C# / .NET 10（WPF，自包含发布） |
| 音频解码 | vgmstream-cli（`.wem` → WAV）+ WPF MediaPlayer |
| 容器解析 | 自研 AKPK 解析器（语音按 64 位 FNV-1 哈希 / 音乐按 32 位 Wwise ID 定位） |
| 数据管线 | Python 3（映射表 / 条目 / 别名 / 官方幕名 / 头像 / 曲库离线构建） |
| 官方数据 | [AnimeGameData](https://github.com/DimbreathBot/AnimeGameData)（CNRELWin7.1.0，与本机客户端同为 48379043 修订） |
| 安装包 | Inno Setup 6（单文件 exe、维护对话框、静默参数） |

## ✨ 功能

- 🎧 **全量语音**：169,463 条 / 700 个条目，按 角色 / 剧情角色 / 七圣召唤 / 剧情群像 分组
- 🎵 **地区音乐**：1,214 首 / 16 分区，经 `hk4e.map`(7.1) 映射为 Wwise ID 实时解包
- 🔍 **搜索**：匹配 条目名 / 条目 id / 官方幕名 / 台词 / 音频路径；空格多关键词按「与」组合；
  全角半角通用；按相关度排序
- 🔤 **别名检索**：搜「黑蛋」命中「宁宁·黑蛋」、「散兵」命中「流浪者」、「埃德」命中「克洛达尔」
- 🗂 **官方中文幕名分类**：`传说任务 · 天下人之章 第二幕 · 涤荡秽浊之光`（取自官方
  `ChapterExcelConfigData`，非猜测；无裸露任务代码）
- 🖼 **头像**：700 张统一 96×96 圆形；本来是圆的图标原图不动，角色半身图按内容缩放使头顶不被
  圆框切掉；无官方立绘的条目用高级灰单色渐变 + 首字
- 📤 导出 WAV（▶ 右键）· 悬停预解码 · 无边框云母质感窗口

## 📄 说明

- 游戏资源（音频 / 立绘 / 文本）**版权归米哈游（miHoYo / HoYoverse）所有**；
  本工具不附带任何游戏资源文件，数据全部在您本机实时读取
- 本仓库仅分发**代码**；安装包通过 Releases 提供，供已拥有游戏的用户本地使用
- 仅供个人学习与本地欣赏使用，请勿用于商业用途或二次分发游戏资源
