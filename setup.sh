#!/bin/bash

set -e # Exit immediately if any command fails

echo "🚀 Starting Automated Deployment for AI Image Generator"
echo "Target: $(lsb_release -ds || cat /etc/*release || uname -om) 2>/dev/null"

# --- Phase 1: System Update and Prerequisites ---
echo ""
echo "🔧 Phase 1: Updating System and Installing Prerequisites..."
sudo apt-get update -y
sudo apt-get install -y \
    curl \
    wget \
    git \
    software-properties-common

# --- Phase 2: Install Python 3.9 if not present ---
echo ""
echo "🐍 Phase 2: Ensuring Python 3.9 is installed..."

if ! command -v python3.9 &> /dev/null; then
    echo "Python 3.9 not found. Installing from deadsnakes PPA..."
    
    # Add the repository that provides older Python versions
    sudo add-apt-repository ppa:deadsnakes/ppa -y
    sudo apt-get update -y
    
    # Install Python 3.9 and the virtual environment module
    sudo apt-get install -y python3.9 python3.9-venv
    echo "✅ Python 3.9 installed."
else
    echo "✅ Python 3.9 is already installed."
fi

# --- Phase 3: Install Docker and Docker Compose ---
echo ""
echo "🐳 Phase 3: Ensuring Docker and Docker Compose are installed..."

if ! command -v docker &> /dev/null; then
    echo "Docker not found. Installing..."
    
    # Add Docker's official GPG key and repository
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    sudo apt-get update -y
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io
    
    # Add the current user to the docker group to run commands without sudo
    sudo usermod -aG docker $USER
    echo "✅ Docker installed. Note: You may need to logout and back in for group changes to apply, or run 'newgrp docker'."
else
    echo "✅ Docker is already installed."
fi

# Check for Docker Compose Plugin
if ! docker compose version &> /dev/null; then
    echo "Docker Compose plugin not found. Installing..."
    sudo apt-get update -y
    sudo apt-get install -y docker-compose-plugin
    echo "✅ Docker Compose plugin installed."
else
    echo "✅ Docker Compose plugin is already installed."
fi

# --- Phase 4: Activate group membership without logout ---
# This attempts to apply the group change for the current session.
# It's not 100% reliable but works in many cases.
echo ""
echo "🔄 Refreshing group membership..."
newgrp docker <<EONG || true
echo "Inside new shell for group activation."
EONG
# Alternatively, just use sudo for the rest of the script if newgrp is problematic.

# --- Phase 5: Build and Start the Docker Stack ---
echo ""
echo "🏗️ Phase 4: Building and Launching the Application Stack with Docker Compose..."

# Use sudo if the user isn't yet in the docker group, otherwise don't.
# The script detects if 'docker ps' works without sudo.
if docker ps &> /dev/null; then
    DOCKER_CMD="docker"
else
    echo "Using sudo for Docker commands as current user lacks permissions."
    DOCKER_CMD="sudo docker"
fi

# Build the images
echo "Building Docker images..."
$DOCKER_CMD compose build

# Start the services in detached mode
echo "Starting containers..."
$DOCKER_CMD compose up -d

echo ""
echo "🎉 Deployment Complete!"
echo "   - Your FastAPI server should be running on port 8000."
echo "   - The MS SQL Server is running on port 1433."
echo ""
echo "📋 Check the status of your containers:"
echo "   $DOCKER_CMD compose ps"
echo ""
echo "📜 View the logs for the app service:"
echo "   $DOCKER_CMD compose logs app -f"
echo ""
echo "🛑 To stop the application:"
echo "   $DOCKER_CMD compose down"