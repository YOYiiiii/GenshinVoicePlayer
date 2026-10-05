# MSI 字体统一补丁（wix build 后运行）
# 把 WixUI 的 Tahoma 样式统一改为 Microsoft YaHei UI，并让默认文本控件
# （按钮/编辑框/单选等）也使用该字体（DefaultUIFont=WixUI_Font_Normal）。
# 值：
#   Normal  9pt  常规（正文/描述/按钮/输入框）
#   Title  11pt  （原有 Style=1 保持粗体）深蓝 → 内页大标题，与正文区分
#   Bigger 15pt  深蓝 → 欢迎/完成页特大标题
# 注意：SQL 中不能出现 Style 列名（MSI SQL 解析器拒绝），只改 FaceName/Size/Color。
# 用法：powershell -File scripts\patch_installer_fonts.ps1 [msi路径]
param(
    [string]$msi = 'E:\Genshin\Collections\VoicePlayer\dist\原神语音播放器-Setup-1.0.0.msi'
)
$ErrorActionPreference = 'Stop'
$inst = New-Object -ComObject WindowsInstaller.Installer
$db = $inst.GetType().InvokeMember('OpenDatabase', 'InvokeMethod', $null, $inst, @($msi, 1))

function ExecSql($sql) {
    $view = $db.GetType().InvokeMember('OpenView', 'InvokeMethod', $null, $db, @($sql))
    $view.GetType().InvokeMember('Execute', 'InvokeMethod', $null, $view, $null)
    $view.GetType().InvokeMember('Close', 'InvokeMethod', $null, $view, $null)
    "OK: $sql"
}

ExecSql "UPDATE TextStyle SET FaceName='Microsoft YaHei UI', Size=9 WHERE TextStyle='WixUI_Font_Normal'"
ExecSql "UPDATE TextStyle SET FaceName='Microsoft YaHei UI', Size=11, Color='1F3864' WHERE TextStyle='WixUI_Font_Title'"
ExecSql "UPDATE TextStyle SET FaceName='Microsoft YaHei UI', Size=15, Color='1F3864' WHERE TextStyle='WixUI_Font_Bigger'"

# 进度页排版安全间距：文本行加高、进度条下移，避免高 DPI/长文本时与进度条挤压
ExecSql "UPDATE Control SET Height=13 WHERE Dialog_='ProgressDlg' AND Control='ActionText'"
ExecSql "UPDATE Control SET Height=13 WHERE Dialog_='ProgressDlg' AND Control='StatusLabel'"
ExecSql "UPDATE Control SET Y=124 WHERE Dialog_='ProgressDlg' AND Control='ProgressBar'"

$exists = $false
$view = $db.GetType().InvokeMember('OpenView', 'InvokeMethod', $null, $db, @("SELECT Value FROM Property WHERE Property='DefaultUIFont'"))
$view.GetType().InvokeMember('Execute', 'InvokeMethod', $null, $view, $null)
$rec = $view.GetType().InvokeMember('Fetch', 'InvokeMethod', $null, $view, $null)
if ($null -ne $rec) { $exists = $true }
$view.GetType().InvokeMember('Close', 'InvokeMethod', $null, $view, $null)
if ($exists) {
    ExecSql "UPDATE Property SET Value='WixUI_Font_Normal' WHERE Property='DefaultUIFont'"
} else {
    ExecSql "INSERT INTO Property (Property, Value) VALUES ('DefaultUIFont', 'WixUI_Font_Normal')"
}

$db.GetType().InvokeMember('Commit', 'InvokeMethod', $null, $db, $null)

# 回读验证
$view = $db.GetType().InvokeMember('OpenView', 'InvokeMethod', $null, $db, @("SELECT * FROM TextStyle"))
$view.GetType().InvokeMember('Execute', 'InvokeMethod', $null, $view, $null)
while ($true) {
    $rec = $view.GetType().InvokeMember('Fetch', 'InvokeMethod', $null, $view, $null)
    if ($null -eq $rec) { break }
    $n = $rec.GetType().InvokeMember('FieldCount', 'GetProperty', $null, $rec, $null)
    $out = @()
    for ($i = 1; $i -le $n; $i++) {
        try { $out += [string]$rec.GetType().InvokeMember('StringData', 'GetProperty', $null, $rec, @($i)) } catch { $out += '' }
    }
    "ROW: $($out -join ' | ')"
}
"PATCH DONE"
