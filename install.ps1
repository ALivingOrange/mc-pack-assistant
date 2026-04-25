$condaEnvPath = Join-Path $PSScriptRoot "conda-env"

try {
    $null = Get-Command conda -ErrorAction Stop
} catch {
    Write-Host "Conda not found. Please install Miniconda from https://docs.conda.io/en/latest/miniconda.html"
    exit
}

if (-not (Test-Path $condaEnvPath)) {
    Write-Host "Creating conda environment..."
    conda create -p $condaEnvPath python=3.11 -y
    
    Write-Host "Installing required packages..."
    
<# NO CONDA PACKAGES YET
    # Install conda packages
    $condaPackages = @(
    )    
    foreach ($package in $condaPackages) {
        conda install -n $condaEnvName $package -y
    }
#>

    $pipPackages = @(
	"google-genai"
        "google-adk"
        "sentence-transformers"
        "numpy"
        "gradio"
    ) 
    conda run -p $condaEnvPath pip install $pipPackages
}


if (-not (Test-Path "jre")) {
    Write-Host "Installing JRE..."
    $jreUrl = "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.9%2B10/OpenJDK21U-jre_x64_windows_hotspot_21.0.9_10.zip"
    Invoke-WebRequest -Uri $jreUrl -OutFile "jre.zip"
    Expand-Archive -Path "jre.zip" -DestinationPath "."
    Rename-Item "jdk-21.0.9+10-jre" "jre"
    Remove-Item "jre.zip"
}

$jreExe = Join-Path $PSScriptRoot "jre\bin\java.exe"

if (-not (Test-Path "server")) {
    New-Item -ItemType Directory -Path "server"
}
Set-Location "server"

$jarFile = "server.jar"
if (-not (Test-Path $jarFile)) {
    Invoke-WebRequest -Uri "https://meta.fabricmc.net/v2/versions/loader/1.20.1/0.18.0/1.1.0/server/jar" -OutFile $jarFile
}

# Run server once to generate eula.txt
& $jreExe -Xmx2G -jar $jarFile -nogui

# Handle EULA
if (Test-Path "eula.txt") {
    Write-Host "`nTo run a Minecraft server, you must agree to the EULA from Microsoft located here: https://aka.ms/MinecraftEULA"
    $response = Read-Host "Do you agree to this EULA? (y/n)"
    
    if ($response -eq 'y') {
        $tz = [System.TimeZoneInfo]::Local.StandardName
        $timestamp = Get-Date -Format "ddd MMM dd HH:mm:ss yyyy"
        $timestamp = "$timestamp $tz"
        @"
#By changing the setting below to TRUE you are indicating your agreement to our EULA (https://aka.ms/MinecraftEULA).
#$timestamp
eula=true
"@ | Set-Content "eula.txt"
    Write-Host "EULA accepted. Installing KubeJS and restarting server..."

    $null = New-Item -ItemType Directory -Path "kubejs\server_scripts" -Force
    Copy-Item -Path "..\kubejs-scripts\dump_recipes.js" -Destination "kubejs\server_scripts"


# Install Required Mods (through Modrinth API)
    Set-location mods
    # Load mod list from server-mods.toml using the conda env's Python (tomllib).
    $modsToml = Join-Path $PSScriptRoot "server-mods.toml"
    $modsJson = conda run -p $condaEnvPath python -c @"
import json, tomllib
with open(r'$modsToml', 'rb') as f:
    data = tomllib.load(f)
print(json.dumps(data['mod']))
"@
    $mods = $modsJson | ConvertFrom-Json | ForEach-Object {
        @{
            ProjectId = $_.project_id
            VersionId = $_.version
            OutFile = $_.filename
        }
    }

    foreach ($mod in $mods) {
        if (Test-Path $mod.OutFile) {
            Write-Host "File already exists: $($mod.OutFile) - Skipping download" -ForegroundColor Yellow
        } else {
            Write-Host "Fetching download URL for: $($mod.OutFile)" -ForegroundColor Cyan
            
            # Get version info from Modrinth API
            $apiUrl = "https://api.modrinth.com/v2/project/$($mod.ProjectId)/version"
            $versions = Invoke-RestMethod -Uri $apiUrl
            
            # Find the matching version
            $version = $versions | Where-Object { $_.version_number -eq $mod.VersionId }
            
            if ($version -and $version.files.Count -gt 0) {
                $downloadUrl = $version.files[0].url
                Write-Host "Downloading: $($mod.OutFile)" -ForegroundColor Green
                Invoke-WebRequest -Uri $downloadUrl -OutFile $mod.OutFile
            } else {
                Write-Host "Could not find version $($mod.VersionId) for this mod" -ForegroundColor Red
            }
        }
    }
	Set-Location ..
        & $jreExe -Xmx2G -jar $jarFile -nogui
    } else {
        Write-Host "EULA not accepted. Exiting."
    }
}

