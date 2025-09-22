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
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg

# --- Phase 2: Install Python 3.9 if not present ---
echo ""
echo "🐍 Phase 2: Ensuring Python 3.9 is installed..."

if ! command -v python3.9 &> /dev/null; then
    echo "Python 3.9 not found. Installing from deadsnakes PPA..."
    
    # Add the repository that provides older Python versions
    sudo add-apt-repository ppa:deadsnakes/ppa -y
    sudo apt-get update -y
    
    # Install Python 3.9 and the virtual environment module
    sudo apt-get install -y python3.9 python3.9-venv python3.9-dev
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
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg

    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    sudo apt-get update -y
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin
    
    # Add the current user to the docker group to run commands without sudo
    sudo usermod -aG docker $USER
    echo "✅ Docker installed. Note: You may need to logout and back in for group changes to apply."
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

# --- Phase 4: Refresh Docker Group Permissions ---
echo ""
echo "🔄 Refreshing group membership..."

# Try to refresh group membership without requiring logout
if ! docker ps &> /dev/null; then
    echo "Attempting to refresh Docker group permissions..."
    sudo su - $USER -c "docker ps" || true
    # Use sudo for the rest of the script if still needed
    DOCKER_CMD="sudo docker"
else
    DOCKER_CMD="docker"
fi

# --- Phase 5: Build and Start the Docker Stack ---
echo ""
echo "🏗️ Phase 5: Building and Launching the Application Stack with Docker Compose..."

# Stop any existing containers to avoid conflicts
echo "Stopping any existing containers..."
$DOCKER_CMD compose down || true

# Build the images with progress output
echo "Building Docker images..."
$DOCKER_CMD compose build --progress plain

# Start the services in detached mode
echo "Starting containers..."
$DOCKER_CMD compose up -d

# Wait for containers to be fully started
echo "Waiting for containers to start up..."
sleep 10

# --- Phase 6: Verify Deployment ---
echo ""
echo "🔍 Phase 6: Verifying Deployment..."

# Check container status
echo "Container status:"
$DOCKER_CMD compose ps

# Check if the app container is running
if $DOCKER_CMD compose ps app | grep -q "Up"; then
    echo "✅ Application container is running"
else
    echo "❌ Application container failed to start"
    echo "Checking logs..."
    $DOCKER_CMD compose logs app
    exit 1
fi

# Test the application health endpoint (adjust endpoint as needed)
echo "Testing application health..."
if curl -f http://localhost:8000/health > /dev/null 2>&1 || \
   curl -f http://localhost:8000/docs > /dev/null 2>&1 || \
   curl -f http://localhost:8000/ > /dev/null 2>&1; then
    echo "✅ Application is responding on port 8000"
else
    echo "⚠️ Application might still be starting up..."
    echo "Current logs:"
    $DOCKER_CMD compose logs app --tail=20
fi

# --- Phase 7: Display Final Information ---
echo ""
echo "🎉 Deployment Complete!"
echo ""
echo "📊 Services Status:"
$DOCKER_CMD compose ps
echo ""
echo "🌐 Application URLs:"
echo "   - FastAPI Server: http://$(curl -s ifconfig.me):8000"
echo "   - API Documentation: http://$(curl -s ifconfig.me):8000/docs"
echo "   - MS SQL Server: localhost:1433"
echo ""
echo "📋 Useful Commands:"
echo "   View all logs:        $DOCKER_CMD compose logs -f"
echo "   View app logs:        $DOCKER_CMD compose logs app -f"
echo "   View database logs:   $DOCKER_CMD compose logs db -f"
echo "   Stop application:     $DOCKER_CMD compose down"
echo "   Restart application:  $DOCKER_CMD compose restart"
echo ""
echo "⏰ Application is starting up. It might take a few moments to be fully ready."
echo "   Check the logs with: $DOCKER_CMD compose logs app -f"