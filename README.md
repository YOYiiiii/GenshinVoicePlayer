# 原神语音播放器 v2

> 本地全量语音 & 地区音乐播放器 · 全部音频从游戏包**实时解包**，本地零音频存储

[![.NET](https://img.shields.io/badge/.NET-10-512BD4)](https://dotnet.microsoft.com/) [![Inno Setup](https://img.shields.io/badge/Installer-Inno%20Setup%206-blue)](https://jrsoftware.org/isinfo.php) [![Platform](https://img.shields.io/badge/Platform-Windows-0078D6)](#) [![LFS](https://img.shields.io/badge/Git-LFS-F64935)](https://git-lfs.com/)

基于 WPF（.NET 10）的《原神》语音浏览器：**169,463 条语音 + 1,214 首音乐**，按需从本机
`YuanShen_Data\StreamingAssets\AudioAssets` 解包 `.wem` → WAV 实时播放，不预转码、不占额外磁盘
（安装包 70.8 MB，音频零存储）。

---

## 启动

```
app\VoicePlayer.exe                    （自包含，无需安装运行时）

命令行参数：
  --open aino           启动并打开指定条目
  --music 璃月           启动并打开指定音乐分组
  --search 温迪          启动并执行全量搜索
```

## 📥 安装包

- 下载：`dist\原神语音播放器-安装程序-1.0.0.exe` 或 [Releases](https://github.com/YOYiiiii/GenshinVoicePlayer/releases/tag/v1.0.0)（`VoicePlayer-Setup-1.0.0.exe`）
- **70.8 MB**，Inno Setup 6 单文件安装程序（不再使用 MSI/Windows Installer，彻底避开 `Config.Msi` 回滚目录的安全权限问题——D 盘安装/更新/卸载全程零报错）
- 双击进入现代风格中文向导：至冬供奉云母质感侧图；默认路径 `D:\Program Files (x86)\原神语音播放器`（可更改），**无需管理员权限**
- 已安装状态下再次双击 = 维护对话框：
  - **更新/修复（默认）**——重新安装全部文件到原目录
  - **卸载** / **取消**
- 静默安装 `安装程序.exe /VERYSILENT /SUPPRESSMSGBOXES`；静默卸载 `unins000.exe /VERYSILENT`
- 自动创建桌面 + 开始菜单快捷方式；换向导侧图：改 `scripts\make_inno_branding.py` 中 `ART` 一行 → 重跑 → 重新编译
- 旧版 MSI 已弃用；如装过旧 MSI 版，请先在 设置→应用 中卸载旧版

## ✨ 功能

- 🎧 **全量语音**：169,463 条 / **700 个条目**，按 角色 / 剧情角色 / 七圣召唤 / 剧情群像 分组
  （空/荧置顶角色组，派蒙列剧情角色组首位）
- 🎵 **地区音乐**：**1,214 首 / 16 分区**，经 `hk4e.map`(7.1) 映射为 Wwise ID 实时解包播放（首次解码数秒，缓存后秒开）
- 🔍 **全量搜索**：跨全部 169,463 条检索，**匹配 条目名 / 条目 id / 官方幕名 / 台词 / 音频路径**；
  空格分隔多关键词按「与」组合（如 `爱诺 甜`）；全角半角通用；结果按相关度排序（条目名 > 幕名 > 台词 > 路径），
  双击跳转；也可只搜当前角色
- 🔤 **别名检索**：台词里的场景名与条目名不同也能搜到——搜「黑蛋」命中「宁宁·黑蛋」、
  「散兵」命中「流浪者」、「埃德」命中「克洛达尔」、「男主」命中「空」
- 🗂 **官方幕名分类**：`传说任务 · 天下人之章 第二幕 · 涤荡秽浊之光` 这样带**官方中文幕名**的分组
  （取自 `ChapterExcelConfigData` 的 `chapterNumTextMapHash`，非猜测）
- 🖼 **立绘头像**：700 张统一 96×96；本来就是圆的图标（七圣召唤魔物）**原图不动**，
  角色半身图按内容缩放使头顶不被圆框切掉、下缘贴齐圆底；无官方立绘的条目用
  **高级灰单色渐变圆 + 首字**（无描边）
- 📤 导出 WAV（▶ 右键）· 悬停预解码 · 无边框云母质感窗口 · 现代细滚动条
- 🎨 配色与字号对齐 DeepSeek Harness 设计令牌；矢量放大镜图标（不依赖图标字体）

## 📊 数据来源（全部实时，无预转码）

- **音频源**：`…\YuanShen_Data\StreamingAssets\AudioAssets`
  - 语音：`Chinese\*.pck` 按 64 位 FNV-1 哈希定位解包（169,463 条）
  - 音乐：`Music*.pck` 按 32 位 Wwise ID 定位解包（1,214 首，hk4e.map 7.1 映射 + 本机逐条验证）
  - 换机器/换路径：右键【导入数据源…】选择 AudioAssets 目录（写入 `config.json`），
    或手工建 `config.json`：`{ "audioRoot": "你的AudioAssets完整路径" }`
- **元数据**：Voice-Mapping 全量映射表（哈希/路径/pck/台词）
- **官方数据**：[DimbreathBot/AnimeGameData](https://github.com/DimbreathBot/AnimeGameData)（CNRELWin7.1.0，
  与本机客户端同为 48379043 修订）——任务幕名 / 章节名 / 任务名
- **背景**：立绘 = `UI_Gacha_AvatarImg_*` 原图；空/荧 = 官方 CoopImg 全身立绘；
  派蒙 = 官方 TRPG 大图；地区 = 对应神明祈愿立绘（至冬用 7.0 活动大图）
- 更新素材：`py scripts\fetch_original_art.py`（从 `E:\Genshin\Texture2D-classified` 复制）

## 🗂 目录结构

```
VoicePlayer\
├─ app\            播放器（自包含 147 MB，含 vgmstream 解码器）  ← 直接运行 VoicePlayer.exe
├─ data\           index.json + entries\*.json（700 条目 / 169,463 条语音）+ aliases.json
├─ assets\bg\      头像 avatar\（700 张 96×96）+ 地区背景 + 角色模糊背景（无音频）
├─ scripts\        数据构建脚本 + 安装包构建（installer_inno.iss）+ tools\（hk4e.map 等）
├─ app-src\        WPF 源码（dotnet publish -r win-x64 --self-contained true 重建）
├─ installer-ui\   安装向导品牌图（make_inno_branding.py 生成）
├─ dist\           安装包输出（ASCII 名走 Git LFS）
├─ README-说明.txt / 技术栈与架构说明.md
```

## 🔧 构建安装包（一步）

```bat
"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" scripts\installer_inno.iss
```
输出 `dist\原神语音播放器-安装程序-1.0.0.exe`（约 37 s），复制 ASCII 名 `VoicePlayer-Setup-1.0.0.exe` 用于 Release

## 🔄 游戏更新后刷新数据

```bat
powershell -File ..\Voice-Mapping\scripts\update-official-data.ps1
py ..\Voice-Mapping\scripts\build-voice-map.py
py scripts\build_player_data2.py                    :: 基础条目与索引
py scripts\missing_characters.py  --min=20 --apply  :: 找出漏掉的角色
py scripts\add_speaker_entries.py --apply           :: 搬成独立条目
py scripts\build_speaker_aliases.py                 :: 别名表
py scripts\build_quest_codes.py                     :: 任务代码 → 官方中文幕名
py scripts\normalize_avatars.py   --apply           :: 头像
py scripts\build_music_full.py    --apply           :: 曲库（映射表来自 AnimeWwise 仓库 maps\hk4e.map）
py scripts\build_player_data3.py  --apply           :: 分类/标签/统计（最后跑）
```
音频无需重转码：播放时自动从新 pck 解包，仅索引需要刷新。

## 🧱 技术栈

| 层 | 技术 |
|---|---|
| 语言 / 运行时 | C# / .NET 10（WPF，自包含发布） |
| 音频解码 | vgmstream-cli（`.wem` → WAV）+ WPF MediaPlayer |
| 容器解析 | 自研 AKPK 解析器（64 位哈希 / 32 位 Wwise ID 定位） |
| 数据管线 | Python 3（映射表 / 条目 / 别名 / 幕名 / 头像 / 曲库离线构建） |
| 官方数据 | AnimeGameData dump（TextMap + ChapterExcel + Quest + Voice） |
| 安装包 | Inno Setup 6（单文件 exe、维护对话框、静默参数、云母质感向导图） |

> 详细架构（播放链路 / 数据管线 / 分类归属规则 / 头像管线 / 官方取数踩坑 / Inno 架构）见
> [技术栈与架构说明.md](技术栈与架构说明.md)

## 🩺 自检

```
解码链自检（输出 selftest.txt）：
  app\VoicePlayer.exe --selftest 40f0e2d5cfe53acb Chinese\External8.pck    （语音）
  app\VoicePlayer.exe --selftest 30d94e38 Music24.pck                      （音乐）
```

## 📄 说明

- 游戏资源（音频 / 立绘 / 文本）**版权归米哈游（miHoYo / HoYoverse）所有**；
  本工具不附带任何游戏资源文件，数据全部在您本机实时读取
- 少量条目无文字（游戏本身未提供，多为过场/音效条目，非缺失）；已用可读中文标签代替文件名
- 仅供个人学习与本地欣赏使用，请勿用于商业用途或二次分发游戏资源
- 本仓库为**全量备份**（app 运行时 / assets 素材 / 源码 / 安装包），克隆后可直接运行；
  克隆大文件需要 [Git LFS](https://git-lfs.com/)
