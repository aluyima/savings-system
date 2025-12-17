#!/bin/bash

# Old Timers Savings Group - Quick Setup Script
# This script will help you set up the application

echo "=========================================="
echo "Old Timers Savings Group - Setup"
echo "=========================================="
echo ""

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Virtual environment not activated!"
    echo "Please run: source venv/bin/activate"
    echo ""
    read -p "Would you like to activate it now? (y/n): " activate_venv
    if [[ $activate_venv == "y" ]]; then
        source venv/bin/activate
        echo "✓ Virtual environment activated"
    else
        echo "Please activate your virtual environment first."
        exit 1
    fi
fi

# Set FLASK_APP
export FLASK_APP=run.py
echo "✓ FLASK_APP set to run.py"
echo ""

# Initialize database
echo "Step 1: Initializing database..."
flask init-db
if [ $? -eq 0 ]; then
    echo ""
else
    echo "✗ Database initialization failed"
    exit 1
fi

# Create admin user
echo "Step 2: Creating Super Admin user..."
flask create-admin

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "To start the application, run:"
echo "  flask run"
echo ""
echo "Then open your browser to: http://127.0.0.1:5000"
echo ""
