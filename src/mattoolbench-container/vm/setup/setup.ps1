$ErrorActionPreference = "Continue" # until downloading from mirrors is more stable

# Section - General Setup
$shortcutShared = "C:\Users\Docker\Desktop\Setup"
$scriptFolder = "\\host.lan\Data"
$toolsFolder = "C:\Users\$env:USERNAME\Tools"

# Load the shared setup-tools module
Import-Module (Join-Path $scriptFolder -ChildPath "setup-tools.psm1")

# Create a shortcut to the shared folder if it doesn't exist
if (-not (Test-Path $shortcutShared)) {
    New-Item -ItemType SymbolicLink -Path $shortcutShared -Value $scriptFolder
}

# Check if profile exists
if (-not (Test-Path $PROFILE)) {
    New-Item -ItemType File -Path $PROFILE -Force
}

# Create a folder where we store all the standalone executables
if (-not (Test-Path $toolsFolder)) {
    New-Item -ItemType Directory -Path $toolsFolder -Force
    $envPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
    $newPath = "$envPath;$toolsFolder"
    [Environment]::SetEnvironmentVariable("PATH", $newPath, "Machine")
}

# Section - Tools Installation

# Set TLS version to 1.2 or higher
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 -bor [Net.SecurityProtocolType]::Tls13

# Load the tools config json listing mirrors and aliases used for installing tools
$toolsConfigJsonPath = Join-Path $scriptFolder -ChildPath "tools_config.json"
$toolsConfigJson = Get-Content -Path $toolsConfigJsonPath -Raw
$toolsList = Get-Tools -toolsConfigJson $toolsConfigJson

## - Python
$pythonToolName = "Python"
$userPythonPath = "$env:LOCALAPPDATA\Programs\Python"
$pythonDetails = Get-ToolDetails -toolsList $toolsList -toolName $pythonToolName
$pythonAlias = $pythonDetails.alias

# Check for Python installation
$pythonExecutablePath = Get-ChildItem -Path $userPythonPath -Filter python.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName

# Force to install Python 3.10 as the pre-installed version on Windows may not work sometimes
Write-Host "Downloading Python $pythonVersion..."
$pythonInstallerFilePath = "$env:TEMP\python_installer.exe"
$downloadResult = Invoke-DownloadFileFromAvailableMirrors -mirrorUrls $pythonDetails.mirrors -outfile $pythonInstallerFilePath
if (-not $downloadResult) {
    Write-Host "Failed to download Python. Please try again later or install manually."
} else {
    Write-Host "Installing Python for current user..."
    Start-Process -FilePath $pythonInstallerFilePath -Args "/quiet InstallAllUsers=0 PrependPath=0" -NoNewWindow -Wait
    $pythonExecutablePath = "$userPythonPath\Python310\python.exe"
    $setAliasExpression = "Set-Alias -Name $pythonAlias -Value `"$pythonExecutablePath`""
    Add-Content -Path $PROFILE -Value $setAliasExpression
    Invoke-Expression $setAliasExpression
}

## - Git
$gitToolName = "git"
$gitToolDetails = Get-ToolDetails -toolsList $toolsList -toolName $gitToolName

# Check for Git installation
try {
    git --version | Out-Null
    Write-Host "Git is already installed."
} catch {
    Write-Host "Git is not installed. Downloading and installing Git..."
    $gitInstallerFilePath = "$env:TEMP\git_installer.exe"
    $downloadResult = Invoke-DownloadFileFromAvailableMirrors -mirrorUrls $gitToolDetails.mirrors -outfile $gitInstallerFilePath
    if (-not $downloadResult) {
        Write-Host "Failed to download Git. Please try again later or install manually."
    } else {
        Start-Process -FilePath $gitInstallerFilePath -Args "/VERYSILENT /NORESTART /NOCANCEL /SP-" -Wait
        Add-ToEnvPath -NewPath "C:\Program Files\Git\bin"

        Write-Host "Git has been installed."
    }
}

# - VLC
$vlcToolName = "VLC"
$vlcToolDetails = Get-ToolDetails -toolsList $toolsList -toolName $vlcToolName
$vlcAlias = $vlcToolDetails.alias
$vlcExecutableFilePath = "C:\Program Files\VideoLAN\VLC\vlc.exe"

# Check if VLC is already installed by checking the VLC command
if (Test-Path $vlcExecutableFilePath) {
    Write-Host "VLC is already installed."
} else {
    # Download the installer to the Temp directory
    $vlcInstallerFilePath = "$env:TEMP\vlc_installer.exe"
    $downloadResult = Invoke-DownloadFileFromAvailableMirrors -mirrorUrls $vlcToolDetails.mirrors -outfile $vlcInstallerFilePath
    if (-not $downloadResult) {
        Write-Host "Failed to download VLC. Please try again later or install manually."
    } else {
        # Execute the installer silently with elevated permissions
        Start-Process -FilePath $vlcInstallerFilePath -ArgumentList "/S" -Verb RunAs -Wait

        # Remove the installer file after installation
        Remove-Item -Path $vlcInstallerFilePath

        # Set alias
        $setAliasExpression = "Set-Alias -Name $vlcAlias -Value `"$vlcExecutableFilePath`""
        Add-Content -Path $PROFILE -Value $setAliasExpression
        Invoke-Expression $setAliasExpression

        # Add VLC to the system PATH environment variable
        Add-ToEnvPath -NewPath "C:\Program Files\VideoLAN\VLC"
    }
}

# - Thunderbird
$thunderbirdToolName = "Thunderbird"
$thunderbirdToolDetails = Get-ToolDetails -toolsList $toolsList -toolName $thunderbirdToolName
$thunderbirdAlias = $thunderbirdToolDetails.alias
$thunderbirdExecutablePath = "C:\Program Files\Mozilla Thunderbird\thunderbird.exe"

# Check if Thunderbird is already installed by checking the Thunderbird executable path
if (Test-Path $thunderbirdExecutablePath) {
    Write-Host "Thunderbird is already installed."
} else {
    # Download the installer to the Temp directory
    $thunderbirdInstallerFilePath = "$env:TEMP\ThunderbirdSetup.exe"
    $downloadResult = Invoke-DownloadFileFromAvailableMirrors -mirrorUrls $thunderbirdToolDetails.mirrors -outfile $thunderbirdInstallerFilePath
    if (-not $downloadResult) {
        Write-Host "Failed to download Thunderbird. Please try again later or install manually."
    } else {
        # Execute the installer silently with elevated permissions
        Start-Process -FilePath $thunderbirdInstallerFilePath -ArgumentList "/S" -Verb RunAs -Wait

        # Remove the installer file after installation
        Remove-Item -Path $thunderbirdInstallerFilePath

        # Set alias
        $setAliasExpression = "Set-Alias -Name $thunderbirdAlias -Value `"$thunderbirdExecutablePath`""
        Add-Content -Path $PROFILE -Value $setAliasExpression
        Invoke-Expression $setAliasExpression

        # Add Thunderbird to the system PATH environment variable
        Add-ToEnvPath -NewPath "C:\Program Files\Mozilla Thunderbird"
    }
}

# - Caddy Proxy
$caddyProxyToolName = "Caddy Proxy"
$caddyProxyToolDetails = Get-ToolDetails -toolsList $toolsList -toolName $caddyProxyToolName
$caddyProxyAlias = $caddyProxyToolDetails.alias
$caddyProxyExecutablePath = "C:\Users\$env:USERNAME\caddy_windows_amd64.exe"

# Check if Caddy is already installed by checking the Caddy executable path
if (Test-Path $caddyProxyExecutablePath) {
    Write-Host "Caddy Server is already installed."
} else {
    # Download the installer to the Temp directory
    $downloadResult = Invoke-DownloadFileFromAvailableMirrors -mirrorUrls $caddyProxyToolDetails.mirrors -outfile $caddyProxyExecutablePath
    if (-not $downloadResult) {
        Write-Host "Failed to download Caddy Proxy. Please try again later or install manually."
    } else {
        # Set alias
        $setAliasExpression = "Set-Alias -Name $caddyProxyAlias -Value `"$caddyProxyExecutablePath`""
        Add-Content -Path $PROFILE -Value $setAliasExpression
        Invoke-Expression $setAliasExpression
    }
}

# Disable Edge Auto Updates
Stop-Process -Name "MicrosoftEdgeUpdate" -Force -ErrorAction SilentlyContinue
$edgeUpdatePath = "${env:ProgramFiles(x86)}\Microsoft\EdgeUpdate"
Remove-Item -Path $edgeUpdatePath -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "Edge Update processes terminated and directory removed."

# - Windows Arena Server Setup 

$pythonServerPort = 5000
$onLogonTaskName = "mattoolbench_OnLogon"
$requirementsFile = "$scriptFolder\server\requirements.txt"

# Ensure pip is updated to the latest version
Install-PythonPackages -Package "pip" -Arguments "--upgrade"

Install-PythonPackages -Package "wheel"
Install-PythonPackages -Package "pywinauto"

# Install Python packages from requirements.txt using Python's pip module
if (Test-Path $requirementsFile) {
    Write-Host "Installing required Python packages using pip from requirements file..."
    Install-PythonPackages -RequirementsPath $requirementsFile
} else {
    Write-Error "Requirements file not found: $requirementsFile"
    exit
}

# Add a firewall rule to allow incoming connections on the specified port for the Python executable
$pythonServerRuleName = "PythonHTTPServer-$pythonServerPort"
if (-not (Get-NetFirewallRule -Name $pythonServerRuleName -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -DisplayName $pythonServerRuleName -Direction Inbound -Program $pythonExecutablePath -Protocol TCP -LocalPort $pythonServerPort -Action Allow -Profile Any
    Write-Host "Firewall rule added to allow traffic on port $pythonServerPort for Python"
} else {
    Write-Host "Firewall rule already exists. $pythonServerRuleName "
}

# Add a firewall rule to allow incoming connections on the specified port for the Python executable
$caddyProxyRuleName = "Allow-Caddy-Proxy"
if (-not (Get-NetFirewallRule -Name $caddyProxyRuleName -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -DisplayName $caddyProxyRuleName -Direction Inbound -Program $caddyProxyExecutablePath -Action Allow -Profile Any
    Write-Host "Firewall rule added to allow traffic on port $caddyProxyRuleName"
} else {
    Write-Host "Firewall rule already exists. $caddyProxyRuleName "
}

$onLogonScriptPath = "$scriptFolder\on-logon.ps1"
# Check if the scheduled task exists before unregistering it
if (Get-ScheduledTask -TaskName $onLogonTaskName -ErrorAction SilentlyContinue) {
    Write-Host "Scheduled task $onLogonTaskName already exists."
} else {
    Write-Host "Registering new task $onLogonTaskName..."
    Register-LogonTask -TaskName $onLogonTaskName -ScriptPath $onLogonScriptPath -LocalUser "Docker"
}

Start-Sleep -Seconds 10
Start-ScheduledTask -TaskName $onLogonTaskName