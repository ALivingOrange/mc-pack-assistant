#!/bin/bash

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CONDA_ENV_PATH="$SCRIPT_DIR/conda-env"

if ! command -v conda &> /dev/null; then
    echo "Conda not found. Please install Miniconda from https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

if [ ! -d "$CONDA_ENV_PATH" ]; then
    echo "Creating conda environment..."
    conda create -p "$CONDA_ENV_PATH" python=3.11 -y
    
    echo "Installing required packages..."
    
    pip_packages="google-genai google-adk sentence-transformers numpy gradio"
    conda run -p "$CONDA_ENV_PATH" pip install $pip_packages
fi

if [ ! -d "jre" ]; then
    echo "Installing JRE..."
    # Linux x64 version of the JRE release
    JRE_URL="https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.9%2B10/OpenJDK21U-jre_x64_linux_hotspot_21.0.9_10.tar.gz"
    
    curl -L -o "jre.tar.gz" "$JRE_URL"
    tar -xzf "jre.tar.gz"
    
    if [ -d "jdk-21.0.9+10-jre" ]; then
        mv "jdk-21.0.9+10-jre" "jre"
    fi
    
    rm "jre.tar.gz"
fi

JRE_EXE="$SCRIPT_DIR/jre/bin/java"

if [ ! -d "server" ]; then
    mkdir -p "server"
fi

cd "server"

JAR_FILE="server.jar"
if [ ! -f "$JAR_FILE" ]; then
    curl -L -o "$JAR_FILE" "https://meta.fabricmc.net/v2/versions/loader/1.20.1/0.18.0/1.1.0/server/jar"
fi

# Server must be run once to generate eula.txt; "|| true" due to non-zero exit code from this
"$JRE_EXE" -Xmx2G -jar "$JAR_FILE" -nogui || true

if [ -f "eula.txt" ]; then
    echo -e "\nTo run a Minecraft server, you must agree to the EULA from Microsoft located here: https://aka.ms/MinecraftEULA"
    read -p "Do you agree to this EULA? (y/n) " response
    
    if [ "$response" == "y" ]; then
        TIMESTAMP=$(date)
        
        cat > eula.txt <<EOF
#By changing the setting below to TRUE you are indicating your agreement to our EULA (https://aka.ms/MinecraftEULA).
#$TIMESTAMP
eula=true
EOF
        echo "EULA accepted. Installing KubeJS and restarting server..."

        mkdir -p kubejs/server_scripts
        cp ../kubejs-scripts/dump_recipes.js kubejs/server_scripts

        mkdir -p mods
        cd mods

        # Mod array format: "ProjectId|VersionId|OutFile"
        mods=(
            "lhGA9TYQ|9.2.14+fabric|architectury-9.2.14-fabric.jar"
            "sk9knFPE|2001.2.3-build.10+fabric|rhino-fabric-2001.2.3-build.10.jar"
            "umyGl7zF|2001.6.5-build.16+fabric|kubejs-fabric-2001.6.5-build.16.jar"
            "P7dR8mSH|0.92.6+1.20.1|fabric-api-0.92.6+1.20.1.jar"
        )

        for mod_entry in "${mods[@]}"; do
            # Split the string by pipe delimiter
            IFS='|' read -r ProjectId VersionId OutFile <<< "$mod_entry"

            if [ -f "$OutFile" ]; then
                echo -e "\033[0;33mFile already exists: $OutFile - Skipping download\033[0m"
            else
                echo -e "\033[0;36mFetching download URL for: $OutFile\033[0m"

                # Get version info from Modrinth API
                API_URL="https://api.modrinth.com/v2/project/$ProjectId/version"
                
                # Use python env to parse JSON
                DOWNLOAD_URL=$(conda run -p "$CONDA_ENV_PATH" python3 -c "
import sys, json, urllib.request
try:
    with urllib.request.urlopen('$API_URL') as url:
        data = json.loads(url.read().decode())
        # Find matching version
        match = next((item for item in data if item['version_number'] == '$VersionId'), None)
        if match and match['files']:
            print(match['files'][0]['url'])
        else:
            sys.exit(1)
except Exception as e:
    sys.exit(1)
")

                if [ $? -eq 0 ] && [ ! -z "$DOWNLOAD_URL" ]; then
                    echo -e "\033[0;32mDownloading: $OutFile\033[0m"
                    curl -L -o "$OutFile" "$DOWNLOAD_URL"
                else
                    echo -e "\033[0;31mCould not find version $VersionId for this mod\033[0m"
                fi
            fi
        done
        
        cd ..
        
        # Start server again
        "$JRE_EXE" -Xmx2G -jar "$JAR_FILE" -nogui
        
    else
        echo "EULA not accepted. Exiting."
        exit 1
    fi
fi
