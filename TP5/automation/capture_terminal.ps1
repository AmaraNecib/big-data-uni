param([Parameter(Mandatory=$true)][string]$Transcript, [Parameter(Mandatory=$true)][string]$Destination, [string]$CommandConfig = '')
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding
try {
    $Host.UI.RawUI.WindowTitle = 'TP05 evidence - ' + [IO.Path]::GetFileName($Transcript)
    $Host.UI.RawUI.BufferSize = New-Object Management.Automation.Host.Size 140, 1000
    $Host.UI.RawUI.WindowSize = New-Object Management.Automation.Host.Size 140, 34
    Clear-Host
    if ($CommandConfig) {
        Write-Host 'TP05 | Live command execution. Full transcript is included with the report.' -ForegroundColor Cyan
    } else {
        Write-Host 'TP05 | Actual saved execution output. Full transcript is included with the report.' -ForegroundColor Cyan
    }
    Write-Host ('Source: ' + $Transcript)
    Write-Host ''
    $commandExit = 0
    if ($CommandConfig) {
        $config = Get-Content -Raw -Encoding UTF8 $CommandConfig | ConvertFrom-Json
        Set-Location $config.cwd
        $env:PYTHONIOENCODING = 'utf-8'
        $exe = $config.args[0]
        $arguments = @($config.args | Select-Object -Skip 1)
        Write-Host ('$ ' + ($config.args -join ' ')) -ForegroundColor Yellow
        $writer = New-Object IO.StreamWriter $Transcript, $false, ([Text.UTF8Encoding]::new($false))
        $writer.AutoFlush = $true
        try {
            & $exe @arguments 2>&1 | ForEach-Object { $writer.WriteLine($_.ToString()); Write-Host $_ }
            $commandExit = $LASTEXITCODE
        } finally { $writer.Dispose() }
        if ($commandExit -ne 0) { throw "Command exited with code $commandExit. See $Transcript" }
    } else {
        Get-Content -Encoding UTF8 $Transcript | Select-Object -Last 28 | ForEach-Object { Write-Host $_ }
    }
    Add-Type -AssemblyName System.Drawing
    Add-Type @'
using System;
using System.Runtime.InteropServices;
public class TP05Console {
    [DllImport("kernel32.dll")] public static extern IntPtr GetConsoleWindow();
    [DllImport("user32.dll")] public static extern bool GetClientRect(IntPtr h, out Rect r);
    [DllImport("user32.dll")] public static extern bool ClientToScreen(IntPtr h, ref Point p);
    public struct Point { public int X, Y; }
    [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr dc, uint flags);
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
    [DllImport("user32.dll")] public static extern bool MoveWindow(IntPtr h, int x, int y, int w, int hgt, bool repaint);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int n);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    public struct Rect { public int Left, Top, Right, Bottom; }
}
'@
    [TP05Console]::SetProcessDPIAware() | Out-Null
    $handle = [TP05Console]::GetConsoleWindow()
    if ($handle -eq [IntPtr]::Zero) { throw 'No native console window. Run run_all.py from an interactive Windows desktop.' }
    [TP05Console]::ShowWindow($handle, 9) | Out-Null
    $rows = 5
    Get-Content -Encoding UTF8 $Transcript | Select-Object -Last 28 | ForEach-Object { $rows += [Math]::Max(1, [Math]::Ceiling($_.Length / 135)) }
    $captureHeight = [Math]::Min(650, [Math]::Max(220, 45 + $rows * 18))
    [TP05Console]::MoveWindow($handle, 20, 20, 1200, $captureHeight, $true) | Out-Null
    [TP05Console]::SetForegroundWindow($handle) | Out-Null
    Start-Sleep -Seconds 2
    $rect = New-Object TP05Console+Rect
    [TP05Console]::GetClientRect($handle, [ref]$rect) | Out-Null
    $origin = New-Object TP05Console+Point
    [TP05Console]::ClientToScreen($handle, [ref]$origin) | Out-Null
    $width = $rect.Right - $rect.Left
    $height = $rect.Bottom - $rect.Top
    if ($width -lt 200 -or $height -lt 100) { throw 'Console window has no capturable visible surface.' }
    $bitmap = New-Object Drawing.Bitmap $width, $height
    $graphics = [Drawing.Graphics]::FromImage($bitmap)
    try {
        $dc = $graphics.GetHdc()
        try {
            if (-not [TP05Console]::PrintWindow($handle, $dc, 1)) { throw 'Windows could not capture this console window.' }
        } finally { $graphics.ReleaseHdc($dc) }
        $visibleInk = 0
        for ($y = 0; $y -lt [Math]::Min(180, $height); $y += 3) {
            for ($x = 0; $x -lt $width; $x += 3) {
                $pixel = $bitmap.GetPixel($x, $y)
                if ($pixel.R + $pixel.G + $pixel.B -gt 150) { $visibleInk++ }
            }
        }
        if ($visibleInk -lt 20) { throw 'The captured console is blank. No evidence image was accepted.' }
        $bitmap.Save($Destination, [Drawing.Imaging.ImageFormat]::Png)
    } finally { $graphics.Dispose(); $bitmap.Dispose() }
    [IO.File]::WriteAllText($Destination + '.status', 'PASS')
} catch {
    [IO.File]::WriteAllText($Destination + '.status', $_.Exception.Message)
    exit 1
}
