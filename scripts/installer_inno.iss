; 原神语音播放器 - Inno Setup 安装脚本
; 编译: "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" scripts\installer_inno.iss
; 设计要点:
;  - 不使用 MSI/Windows Installer（避免 Config.Msi 回滚安全问题）
;  - PrivilegesRequired=lowest: 无需管理员权限（per-user 安装）
;  - 检测到已安装时弹出「更新/修复 / 卸载 / 取消」维护对话框
;  - 支持静默: /VERYSILENT /SUPPRESSMSGBOXES /DIR="路径"

#define MyAppName "原神语音播放器"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "VoicePlayer"
#define MyAppExeName "VoicePlayer.exe"
#define UninstKey "{E3B7F2A1-9C4D-4E8B-A6F2-5D1C8E7B3A90}_is1"

[Setup]
AppId={{E3B7F2A1-9C4D-4E8B-A6F2-5D1C8E7B3A90}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName=D:\Program Files (x86)\原神语音播放器
DisableProgramGroupPage=yes
LicenseFile=..\license.rtf
OutputDir=..\dist
OutputBaseFilename=原神语音播放器-安装程序-{#MyAppVersion}
SetupIconFile=..\app-src\VoicePlayer\app.ico
UninstallDisplayIcon={app}\app\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardImageFile=..\installer-ui\inno-wizard-164x314.bmp
PrivilegesRequired=lowest
AllowNoIcons=yes

[Languages]
Name: "chinese"; MessagesFile: "ChineseSimplified.isl"

[Messages]
SetupAppTitle={#MyAppName} 安装程序
SetupWindowTitle={#MyAppName} 安装程序
UninstallAppTitle={#MyAppName} 卸载
UninstallAppFullTitle={#MyAppName} 卸载
WelcomeLabel2=即将安装 [name/ver] 到你的电脑。%n%n原神全量语音 &amp; 地区音乐本地播放器（169,463 条语音 + 105 首音乐）。%n%n继续前请关闭正在运行的 原神语音播放器。

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加任务："; Flags: checkedonce

[Files]
Source: "..\app\*"; DestDir: "{app}\app"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "__pycache__,*.log,config.json,selftest.txt"
Source: "..\data\*"; DestDir: "{app}\data"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "__pycache__"
Source: "..\assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "__pycache__,bg\orig,bg\orig\*"
Source: "..\scripts\*"; DestDir: "{app}\scripts"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "__pycache__,*.iss,*.isl,*.bak-*,*.prev"
Source: "..\README-说明.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\技术栈与架构说明.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\config.json.example"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\原神语音播放器"; Filename: "{app}\app\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{autoprograms}\卸载 原神语音播放器"; Filename: "{uninstallexe}"
Name: "{autodesktop}\原神语音播放器"; Filename: "{app}\app\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\app\{#MyAppExeName}"; Description: "运行 原神语音播放器"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
function InitializeSetup(): Boolean;
var
  sUninst: String;
  ResultCode: Integer;
  MaintResult: Integer;
begin
  Result := True;
  if RegQueryStringValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#UninstKey}', 'UninstallString', sUninst) then
  begin
    MaintResult := TaskDialogMsgBox(
      '检测到已安装「原神语音播放器」',
      '选择操作：' + #13#10 + #13#10 +
      '・更新/修复：重新安装全部文件到原目录（推荐）' + #13#10 +
      '・卸载：移除已安装的 原神语音播放器（保留安装包）',
      mbConfirmation, MB_YESNOCANCEL, ['更新/修复', '卸载', '取消'], 0);
    if MaintResult = mrNo then
    begin
      { 卸载现有安装后退出安装程序 }
      if Exec(RemoveQuotes(sUninst), '/SILENT', '', SW_SHOW, ewWaitUntilTerminated, ResultCode) then
      begin
        { 卸载完成 }
      end;
      Result := False;
    end
    else if MaintResult = mrCancel then
      Result := False;
  end;
end;
