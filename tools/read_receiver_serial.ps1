param([string]$Port, [switch]$ListPorts)
$ErrorActionPreference = 'Stop'
if (-not ('System.IO.Ports.SerialPort' -as [type])) { Add-Type -AssemblyName System.IO.Ports }
if ($ListPorts) {
    [System.IO.Ports.SerialPort]::GetPortNames() | Sort-Object
    exit 0
}
if ($Port -notmatch '^COM[1-9][0-9]*$') { throw 'Choose a local receiver COM port.' }
$root = Split-Path -Parent $PSScriptRoot
$contract = Get-Content -LiteralPath (Join-Path $root 'shared/contract.json') -Raw | ConvertFrom-Json
$serial = [System.IO.Ports.SerialPort]::new($Port, $contract.constants.SERIAL_BAUD, 'None', 8, 'One')
$serial.ReadTimeout = 50
$serial.WriteTimeout = 500
$serial.Handshake = 'None'
$serial.DtrEnable = $true
$serial.RtsEnable = $false
$output = [Console]::OpenStandardOutput()
$buffer = [byte[]]::new($contract.constants.MAX_EVENT_LINE_BYTES)
$timer = [Diagnostics.Stopwatch]::StartNew()
$requested = $false
try {
    $serial.Open()
    while ($true) {
        # Receiver-only HELLO fallback. Opening USB may reset the board.
        if (-not $requested -and $timer.ElapsedMilliseconds -ge 2000) {
            $serial.Write("HELLO`n")
            $requested = $true
        }
        try {
            $count = $serial.Read($buffer, 0, $buffer.Length)
            if ($count -gt 0) {
                $output.Write($buffer, 0, $count)
                $output.Flush()
            }
        } catch [TimeoutException] { }
    }
} finally {
    if ($serial.IsOpen) { $serial.Close() }
    $serial.Dispose()
}
