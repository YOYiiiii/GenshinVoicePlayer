# 修复安装组件错误（错误 5 / 1926：无法设置 D:\Config.Msi 文件安全）
# 用途：安装/卸载被异常中断（断电、强杀进程等）后，D:\Config.Msi 回滚目录可能残留
#       并锁定，导致后续操作结尾弹出"无法设置文件...的文件安全。错误 5"。
# 用法：右键本文件 -> 使用 PowerShell 运行（会自动请求管理员权限），或双击同名 .cmd。
$ErrorActionPreference = 'SilentlyContinue'

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host '需要管理员权限，正在请求提升...' -ForegroundColor Yellow
    Start-Process powershell -Verb RunAs -ArgumentList '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$PSCommandPath`""
    exit
}

Write-Host '=== 修复安装组件错误 ===' -ForegroundColor Cyan
$targets = @('D:\Config.Msi', 'C:\Config.Msi')
$fixed = 0
foreach ($t in $targets) {
    if (Test-Path $t) {
        Write-Host "发现残留: $t，正在清理（大目录可能需要 1-2 分钟）..."
        cmd /c "takeown /F `"$t`" /R /A /D Y >nul 2>&1"
        cmd /c "icacls `"$t`" /reset /T /C /Q >nul 2>&1"
        $empty = Join-Path $env:TEMP 'empty_cleanup_dir'
        New-Item -ItemType Directory -Path $empty -Force | Out-Null
        robocopy $empty $t /MIR /NFL /NDL /NJH /NJS /NC /NS /NP | Out-Null
        cmd /c "rd /s /q `"$t`" 2>nul"
        if (Test-Path $t) {
            cmd /c "attrib -h -s `"$t`" /D"
            cmd /c "rd /s /q `"$t`" 2>nul"
        }
        if (Test-Path $t) {
            Write-Host "[失败] 无法完全删除 $t，请手动处理" -ForegroundColor Red
        } else {
            Write-Host "[成功] 已清理 $t" -ForegroundColor Green
            $fixed++
        }
    } else {
        Write-Host "正常: $t 不存在（无需清理）" -ForegroundColor Gray
    }
}
if ($fixed -gt 0) {
    Write-Host ''
    Write-Host '修复完成！现在可以重新运行安装程序（安装/更新/卸载均可）。' -ForegroundColor Green
} else {
    Write-Host ''
    Write-Host '没有发现需要清理的残留。如果仍然报错，请把报错截图反馈。' -ForegroundColor Yellow
}
Write-Host ''
Read-Host '按回车键退出'
