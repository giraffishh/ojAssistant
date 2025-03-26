#Requires -Version 5.0

# ojAssistant Setup & Update Script
Write-Host "ojAssistant Setup and Update Script" -ForegroundColor Green
Write-Host "This script will set up or update ojAssistant on your system." -ForegroundColor Cyan
Write-Host "--------------------------------------------------" -ForegroundColor DarkGray

# Check if Git is installed
try {
    $gitVersion = git --version
    Write-Host "Git detected: $gitVersion" -ForegroundColor Green
}
catch {
    Write-Host "Git not detected. Please install Git and try again." -ForegroundColor Red
    Write-Host "Download Git from: https://git-scm.com/downloads" -ForegroundColor Yellow
    exit 1
}

# Check if Python is installed
try {
    $pythonVersion = python --version
    Write-Host "Python detected: $pythonVersion" -ForegroundColor Green
}
catch {
    Write-Host "Python not detected. Please install Python and try again." -ForegroundColor Red
    exit 1
}

# Get the script directory
$scriptDir = Join-Path $env:USERPROFILE "Documents\ojAssistant"

# 确保安装目录存在
if (-not (Test-Path $scriptDir)) {
    Write-Host "Creating installation directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $scriptDir -Force | Out-Null
}
$mainPath = Join-Path $scriptDir "main.py"
$configPath = Join-Path $scriptDir "config.py"
$repoUrl = "https://github.com/giraffishh/ojAssistant.git"

Write-Host "Installation directory: $scriptDir" -ForegroundColor Cyan

# Function to read config file and return a hashtable of key-value pairs
function Read-ConfigFile {
    param (
        [string]$configPath
    )

    $configData = @{}

    if (Test-Path $configPath) {
        $configLines = Get-Content $configPath -Encoding UTF8

        foreach ($line in $configLines) {
            # Skip comments and empty lines
            if (-not $line.Trim().StartsWith("#") -and $line.Trim() -ne "") {
                # Try to extract key-value pairs
                if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)\s*$') {
                    $key = $matches[1]
                    $value = $matches[2].Trim()

                    # Remove comments at the end of the line
                    if ($value.Contains("#")) {
                        $value = $value.Substring(0, $value.IndexOf("#")).Trim()
                    }

                    $configData[$key] = $value
                }
            }
        }
    }

    return $configData
}

# Function to extract clean value from config value string (remove quotes, etc)
function Get-CleanValue {
    param (
        [string]$value
    )

    # Remove quotes if present
    if (($value.StartsWith("'") -and $value.EndsWith("'")) -or
        ($value.StartsWith('"') -and $value.EndsWith('"'))) {
        $value = $value.Substring(1, $value.Length - 2)
    }
    # Handle raw string (r"..." or r'...')
    elseif (($value.StartsWith('r"') -and $value.EndsWith('"')) -or
            ($value.StartsWith("r'") -and $value.EndsWith("'"))) {
        $value = $value.Substring(2, $value.Length - 3)
    }

    return $value
}

# Function to backup and read existing config
function Get-ExistingConfig {
    param (
        [string]$configPath
    )

    Write-Host "Reading existing configuration..." -ForegroundColor Yellow
    $configData = Read-ConfigFile -configPath $configPath

    # Create a clean version of the config data (without quotes)
    $cleanConfigData = @{}
    foreach ($key in $configData.Keys) {
        $cleanConfigData[$key] = Get-CleanValue -value $configData[$key]
        Write-Host "  Found config: $key = $($cleanConfigData[$key])" -ForegroundColor DarkGray
    }

    # Create backup of existing config
    if (Test-Path $configPath) {
        $backupPath = "${configPath}.backup"
        Copy-Item -Path $configPath -Destination $backupPath -Force
        Write-Host "Existing config backed up to $backupPath" -ForegroundColor Yellow
    }

    return $cleanConfigData
}

# Function to handle installation or update
function Install-OjAssistant {
    param (
        [switch]$Update,
        [hashtable]$ExistingConfig
    )

    if ($Update) {
        # For update, clone to a temporary directory then move files
        $tempDir = Join-Path $env:TEMP "ojAssistant_update"
        if (Test-Path $tempDir) {
            Remove-Item $tempDir -Recurse -Force
        }

        Write-Host "Cloning latest version to temporary directory..." -ForegroundColor Yellow
        git clone $repoUrl $tempDir

        if ($LASTEXITCODE -ne 0) {
            Write-Host "Failed to clone repository. Please check your internet connection and try again." -ForegroundColor Red
            exit 1
        }

        # First, get and store the new config structure to be analyzed later
        $newConfigPath = Join-Path $tempDir "config.py"

        # Copy files from temp to installation directory - FIX: Improved directory handling
        Write-Host "Updating files..." -ForegroundColor Yellow

        # Get all files and directories in the source directory, excluding .git, setup.ps1, config.py
        $sourceItems = Get-ChildItem -Path $tempDir -Exclude @(".git", "setup.ps1", "config.py")

        foreach ($item in $sourceItems) {
            $relativePath = $item.FullName.Substring($tempDir.Length + 1)
            $destination = Join-Path $scriptDir $relativePath

            # Handle directories specially to prevent nested copies
            if ($item.PSIsContainer) {
                # If the destination directory exists, don't copy the directory itself
                # but copy its contents instead
                if (Test-Path $destination) {
                    # Get all files within the source directory
                    $subItems = Get-ChildItem -Path $item.FullName -Recurse
                    foreach ($subItem in $subItems) {
                        # Calculate the relative path from the source directory
                        $subRelativePath = $subItem.FullName.Substring($item.FullName.Length + 1)
                        $subDestination = Join-Path $destination $subRelativePath

                        # Skip directories, we only want to copy files
                        if (-not $subItem.PSIsContainer) {
                            # Create the parent directory structure if it doesn't exist
                            $subDestinationDir = Split-Path -Parent $subDestination
                            if (-not (Test-Path $subDestinationDir)) {
                                New-Item -ItemType Directory -Path $subDestinationDir -Force | Out-Null
                            }

                            # Copy the file
                            Copy-Item -Path $subItem.FullName -Destination $subDestination -Force
                            Write-Host "  - Updated: $($relativePath)/$($subRelativePath)" -ForegroundColor Green
                        }
                    }
                }
                # If directory doesn't exist, simply copy it
                else {
                    Copy-Item -Path $item.FullName -Destination $destination -Recurse -Force
                    Write-Host "  - Added new directory: $relativePath" -ForegroundColor Green
                }
            }
            # For files, just copy directly
            else {
                Copy-Item -Path $item.FullName -Destination $destination -Force
                Write-Host "  - Updated: $relativePath" -ForegroundColor Green
            }
        }

        # Now, merge config.py by preserving existing values and adding new keys
        $updatedConfig = @()
        $newConfigLines = Get-Content -Path $newConfigPath -Encoding UTF8

        foreach ($line in $newConfigLines) {
            # Skip comments and empty lines
            if ($line.Trim().StartsWith("#") -or $line.Trim() -eq "") {
                $updatedConfig += $line
                continue
            }

            # Check if this is a config key line
            if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)\s*$') {
                $key = $matches[1]

                # If we have this key in existing config and it's not REMOVE/empty, use that value
                if ($ExistingConfig.ContainsKey($key) -and
                    $ExistingConfig[$key] -ne "REMOVE" -and
                    $ExistingConfig[$key] -ne "REMOVED" -and
                    $ExistingConfig[$key] -ne "") {

                    $value = $ExistingConfig[$key]

                    # Format according to the key type
                    if ($key -eq "WORK_DIRECTORY") {
                        # Windows path needs special handling
                        $updatedConfig += "$key = r`"$value`""
                    }
                    elseif ($value -eq "True" -or $value -eq "False" -or $value -match "^\d+$") {
                        # Boolean or number values
                        $updatedConfig += "$key = $value"
                    }
                    else {
                        # String values
                        $updatedConfig += "$key = '$value'"
                    }

                    Write-Host "  - Preserved existing value for $key" -ForegroundColor Green
                }
                else {
                    # Use the default value from the new config
                    $updatedConfig += $line
                }
            }
            else {
                $updatedConfig += $line
            }
        }

        # Write the updated config to the file
        $utf8WithoutBom = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllLines($configPath, $updatedConfig, $utf8WithoutBom)

        # Clean up temp directory
        Remove-Item $tempDir -Recurse -Force
    }
    else {
        # For fresh install, just clone directly to current directory
        Write-Host "Cloning repository..." -ForegroundColor Yellow

        # Get parent directory of current script
        $parentDir = Split-Path -Parent $scriptDir
        $repoName = "ojAssistant"
        $targetDir = Join-Path $parentDir $repoName

        # Clone repository
        git clone $repoUrl $targetDir

        if ($LASTEXITCODE -ne 0) {
            Write-Host "Failed to clone repository. Please check your internet connection and try again." -ForegroundColor Red
            exit 1
        }

        Write-Host "Repository cloned successfully!" -ForegroundColor Green
    }
}

# Determine if this is an update or fresh install
$isUpdate = Test-Path (Join-Path $scriptDir "main.py")

# If updating, backup existing config values
$existingConfig = @{}
if ($isUpdate) {
    $existingConfig = Get-ExistingConfig -configPath $configPath
}

# Install or update based on current state
if ($isUpdate) {
    Write-Host "`nUpdating ojAssistant..." -ForegroundColor Cyan
    Install-OjAssistant -Update -ExistingConfig $existingConfig
}
else {
    Write-Host "`nInstalling ojAssistant..." -ForegroundColor Cyan
    Install-OjAssistant
    # Update script path after installation
    $scriptDir = Join-Path (Split-Path -Parent $scriptDir) "ojAssistant"
    $mainPath = Join-Path $scriptDir "main.py"
    $configPath = Join-Path $scriptDir "config.py"
}

# Install required packages
Write-Host "`nInstalling required packages..." -ForegroundColor Yellow
python -m pip install requests
Write-Host "Packages installed successfully" -ForegroundColor Green

# Now check if we need to prompt for any values
$currentConfig = Read-ConfigFile -configPath $configPath
$needUsername = $false
$needPassword = $false
$needWorkDir = $false

# Check essential values
foreach ($key in $currentConfig.Keys) {
    $value = Get-CleanValue -value $currentConfig[$key]

    if ($key -eq "USERNAME" -and ($value -eq "REMOVE" -or $value -eq "REMOVED" -or $value -eq "")) {
        $needUsername = $true
    }
    elseif ($key -eq "PASSWORD" -and ($value -eq "REMOVE" -or $value -eq "REMOVED" -or $value -eq "")) {
        $needPassword = $true
    }
    elseif ($key -eq "WORK_DIRECTORY" -and $value -eq "") {
        $needWorkDir = $true
    }
}

# Get user input if needed
if ($needUsername -or $needPassword -or $needWorkDir) {
    Write-Host "`nConfiguring essential settings:" -ForegroundColor Cyan
    $configLines = Get-Content $configPath -Encoding UTF8
    $updatedConfigLines = @()

    foreach ($line in $configLines) {
        if ($needUsername -and $line -match '^\s*USERNAME\s*=') {
            $username = Read-Host "Enter your CAS username"
            $updatedConfigLines += "USERNAME = '$username'"
        }
        elseif ($needPassword -and $line -match '^\s*PASSWORD\s*=') {
            $securePassword = Read-Host "Enter your CAS password" -AsSecureString
            $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
            $password = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
            [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)
            $updatedConfigLines += "PASSWORD = '$password'"
        }
        elseif ($needWorkDir -and $line -match '^\s*WORK_DIRECTORY\s*=') {
            $workDir = Read-Host "Enter the directory where your Java assignments are stored"

            # Validate work directory
            if (-not (Test-Path $workDir)) {
                $createDir = Read-Host "Directory does not exist. Create it? (y/n)"
                if ($createDir -eq "y") {
                    New-Item -ItemType Directory -Path $workDir -Force | Out-Null
                    Write-Host "Directory created at $workDir" -ForegroundColor Green
                }
                else {
                    Write-Host "Please provide a valid directory path and run the script again." -ForegroundColor Yellow
                    exit 0
                }
            }

            $updatedConfigLines += "WORK_DIRECTORY = r`"$workDir`""
        }
        else {
            $updatedConfigLines += $line
        }
    }

    # Save updated config
    $utf8WithoutBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllLines($configPath, $updatedConfigLines, $utf8WithoutBom)

    Write-Host "Configuration updated successfully" -ForegroundColor Green
}

# Set up PowerShell profile
Write-Host "`nSetting up PowerShell profile..." -ForegroundColor Yellow

# Create profile directory if it doesn't exist
$profileDir = Split-Path -Parent $PROFILE
if (-not (Test-Path $profileDir)) {
    New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
}

# Check if profile exists, if not create it
if (-not (Test-Path $PROFILE)) {
    New-Item -ItemType File -Path $PROFILE -Force | Out-Null
}

# Check if oja function already exists in profile
$profileContent = Get-Content $PROFILE -Raw -ErrorAction SilentlyContinue
if ($null -eq $profileContent -or -not $profileContent.Contains("function oja")) {
    # Add oja function to profile
    $ojaFunction = @"

# ojAssistant function
function oja {
    python "$mainPath"
}
"@
    Add-Content -Path $PROFILE -Value $ojaFunction
    Write-Host "PowerShell profile updated with oja function" -ForegroundColor Green
}
else {
    Write-Host "oja function already exists in PowerShell profile" -ForegroundColor Green
}

# Reload profile
Write-Host "`nReloading PowerShell profile..." -ForegroundColor Yellow
try {
    . $PROFILE
    Write-Host "PowerShell profile reloaded" -ForegroundColor Green
}
catch {
    Write-Host "Unable to reload profile automatically. Please restart your PowerShell session." -ForegroundColor Yellow
}

# Final output message
if ($isUpdate) {
    Write-Host "`nojAssistant has been successfully updated!" -ForegroundColor Green
}
else {
    Write-Host "`nojAssistant has been successfully installed!" -ForegroundColor Green
}

Write-Host "You can now use the 'oja' command in PowerShell to start ojAssistant." -ForegroundColor Cyan
Write-Host "If the command is not available, please restart your PowerShell session." -ForegroundColor Cyan