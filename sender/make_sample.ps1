# Create a local test WAV with an installed Windows voice; no microphone/network.
$ErrorActionPreference = 'Stop'
$sampleDirectory = Join-Path $PSScriptRoot '.local\samples'
New-Item -ItemType Directory -Path $sampleDirectory -Force | Out-Null
$samplePath = Join-Path $sampleDirectory 'demo.wav'
$voice = New-Object -ComObject SAPI.SpVoice
$stream = New-Object -ComObject SAPI.SpFileStream
try {
    $english = @($voice.GetVoices() | Where-Object { $_.GetAttribute('Language') -match '(^|;)0?409($|;)' })
    if ($english.Count -eq 0) { throw 'No installed US-English SAPI voice. Supply a local English WAV and use --audio/--expected instead.' }
    $voice.Voice = $english[0]
    $stream.Open($samplePath, 3, $false)
    $voice.AudioOutputStream = $stream
    $voice.Speak('Spirit, what is your name?') | Out-Null
    $stream.Close()
    [pscustomobject]@{text='Spirit, what is your name?';voice=$voice.Voice.GetDescription();source='Locally generated Windows SAPI test speech, not a real microphone test';sha256=(Get-FileHash -LiteralPath $samplePath).Hash.ToLower()} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $sampleDirectory 'provenance.json')
    Write-Output "Local test audio prepared: $samplePath"
} finally {
    [Runtime.InteropServices.Marshal]::ReleaseComObject($stream) | Out-Null
    [Runtime.InteropServices.Marshal]::ReleaseComObject($voice) | Out-Null
}
