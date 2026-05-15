# Run this script as Administrator in PowerShell
param()

$ErrorActionPreference = "Stop"

# Read config
$configPath = Join-Path $PSScriptRoot "config.json"
$config = Get-Content -Raw $configPath | ConvertFrom-Json

# Resolve Python and script paths
$pythonPath = (Get-Command python -ErrorAction Stop).Source
$scriptPath = Join-Path $PSScriptRoot "clocker.py"

# Parse times from config
$clockInTime  = [datetime]::ParseExact($config.clock_in_time,  "HH:mm", $null)
$clockOutTime = [datetime]::ParseExact($config.clock_out_time, "HH:mm", $null)

function Register-SproutTask {
    param(
        [string]$Name,
        [int]$Hour,
        [int]$Minute,
        [string]$Argument
    )

    $action   = New-ScheduledTaskAction -Execute $pythonPath `
                    -Argument "`"$scriptPath`" $Argument" `
                    -WorkingDirectory $PSScriptRoot
    $trigger  = New-ScheduledTaskTrigger -Daily -At ("{0:D2}:{1:D2}" -f $Hour, $Minute)
    $settings = New-ScheduledTaskSettingsSet `
                    -StartWhenAvailable `
                    -RunOnlyIfNetworkAvailable `
                    -ExecutionTimeLimit (New-TimeSpan -Minutes 5)

    Unregister-ScheduledTask -TaskName $Name -Confirm:$false -ErrorAction SilentlyContinue
    Register-ScheduledTask -TaskName $Name -Action $action -Trigger $trigger -Settings $settings -RunLevel Highest -Force
    Write-Host "Registered: $Name"
}

Register-SproutTask -Name "SproutClockIn"        -Hour $clockInTime.Hour  -Minute $clockInTime.Minute  -Argument "--action clock_in"
Register-SproutTask -Name "SproutClockOut"       -Hour $clockOutTime.Hour -Minute $clockOutTime.Minute -Argument "--action clock_out"
Register-SproutTask -Name "SproutDailyReport"    -Hour 20                 -Minute 0                   -Argument "--report"
Register-SproutTask -Name "SproutMorningReport"  -Hour 8                  -Minute 0                   -Argument "--report-browser"

Write-Host ""
Write-Host "All 4 tasks registered. Run 'python clocker.py --setup' next to save your credentials."
