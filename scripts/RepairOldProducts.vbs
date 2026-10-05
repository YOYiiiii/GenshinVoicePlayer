' 修复旧版本（WIX_UPGRADE_DETECTED 内的全部产品码）
Option Explicit
Dim c, p, sh
c = Session.Property("WIX_UPGRADE_DETECTED")
Set sh = CreateObject("WScript.Shell")
For Each p In Split(c, ";")
  If p <> "" Then sh.Run "msiexec /fomus " & p & " /qn", 0, True
Next
MsgBox "旧版本已修复完成。", 64, "原神语音播放器"
