# Conda environment setup
$condaEnvName = "mc-agent-env"

# Check if conda is installed
try {
    $null = Get-Command conda -ErrorAction Stop
} catch {
    Write-Host "Conda not found. Please install Miniconda from https://docs.conda.io/en/latest/miniconda.html"
    exit
}

# Check if environment exists
$envExists = conda env list | Select-String -Pattern $condaEnvName -Quiet

if (-not $envExists) {
    Write-Host "Creating conda environment..."
    conda create -n $condaEnvName python=3.11 -y
    
    Write-Host "Installing required packages..."
    
<# NO CONDA YET
    # Install conda packages
    $condaPackages = @(
    )    
    foreach ($package in $condaPackages) {
        conda install -n $condaEnvName $package -y
    }
#>

    # Install pip packages
    $pipPackages = @(
	"google-genai"
        "google-adk"
    ) 
    conda run -n $condaEnvName pip install $pipPackages
}


# Install JRE if not present
if (-not (Test-Path "jre")) {
    Write-Host "Installing JRE..."
    $jreUrl = "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.9%2B10/OpenJDK21U-jre_x64_windows_hotspot_21.0.9_10.zip"
    Invoke-WebRequest -Uri $jreUrl -OutFile "jre.zip"
    Expand-Archive -Path "jre.zip" -DestinationPath "."
    Rename-Item "jdk-21.0.9+10-jre" "jre"
    Remove-Item "jre.zip"
}

$jreExe = Join-Path $PSScriptRoot "jre\bin\java.exe"

# Create server directory
if (-not (Test-Path "server")) {
    New-Item -ItemType Directory -Path "server"
}
Set-Location "server"

# Download server jar if not present
$jarFile = "fabric-server-mc.1.21.10-loader.0.17.3-launcher.1.1.0.jar"
if (-not (Test-Path $jarFile)) {
    Invoke-WebRequest -Uri "https://meta.fabricmc.net/v2/versions/loader/1.21.10/0.17.3/1.1.0/server/jar" -OutFile $jarFile
}

# Run server once to generate eula.txt
& $jreExe -Xmx2G -jar $jarFile -nogui

# Handle EULA
if (Test-Path "eula.txt") {
    Write-Host "`nTo run a Minecraft server, you must agree to the EULA from Microsoft located here: https://aka.ms/MinecraftEULA"
    $response = Read-Host "Do you agree to this EULA? (y/n)"
    
    if ($response -eq 'y') {
        $timestamp = Get-Date -Format "ddd MMM dd HH:mm:ss 'PST' yyyy"
        @"
#By changing the setting below to TRUE you are indicating your agreement to our EULA (https://aka.ms/MinecraftEULA).
#$timestamp
eula=true
"@ | Set-Content "eula.txt"
        
        Write-Host "EULA accepted. Restarting server..."
        & $jreExe -Xmx2G -jar $jarFile -nogui
    } else {
        Write-Host "EULA not accepted. Exiting."
    }
}

