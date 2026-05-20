#!/bin/bash

# E-Learning Portal - Automatic Setup and Run Script for Mac/Linux

echo ""
echo "============================================"
echo "  Faculty of Computing E-Learning Portal"
echo "  Setup and Launcher"
echo "============================================"
echo ""

# Check if Python3 is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 is not installed"
    echo ""
    echo "Please install Python 3.8+ from: https://www.python.org/"
    echo ""
    echo "Or using Homebrew (Mac):"
    echo "  brew install python3"
    echo ""
    echo "Or using apt (Ubuntu):"
    echo "  sudo apt-get install python3 python3-venv"
    exit 1
fi

echo "[1/5] Python detected:"
python3 --version

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "[2/5] Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        exit 1
    fi
else
    echo ""
    echo "[2/5] Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "[3/5] Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo ""
echo "[4/5] Installing dependencies..."
pip install -q -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi
echo "Dependencies installed successfully"

# Initialize database if it doesn't exist
if [ ! -f "elearning.db" ]; then
    echo ""
    echo "[5/5] Initializing database with sample data..."
    python init_db.py
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to initialize database"
        exit 1
    fi
else
    echo ""
    echo "[5/5] Database already exists, skipping initialization"
fi

echo ""
echo "============================================"
echo "  ✓ Setup Complete!"
echo "============================================"
echo ""
echo "Starting E-Learning Portal..."
echo ""
echo "Expected output:"
echo "  * Running on http://127.0.0.1:5000"
echo ""
echo "Open your browser and visit:"
echo "  → http://localhost:5000"
echo ""
echo "Test Credentials:"
echo "  Admin:   admin@elearning.local / admin123"
echo "  Teacher: john.smith@faculty.local / teacher123"
echo "  Student: student1@faculty.local / student123"
echo ""
echo "Press CTRL+C to stop the server"
echo "============================================"
echo ""

# Run the application
python main_enhanced.py
