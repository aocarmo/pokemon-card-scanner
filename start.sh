#!/bin/bash
# Pokemon Card Scanner - Start Script for macOS/Linux
# Run: chmod +x start.sh && ./start.sh

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "🚀 Starting Pokemon Card Scanner..."

# Backend
echo "📦 Setting up Backend..."
cd "$PROJECT_ROOT/backend"

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install fastapi uvicorn python-multipart opencv-python easyocr numpy --quiet

echo "Starting Backend on http://localhost:8000"
cd src
python -m uvicorn api.app:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Frontend
# echo "📦 Setting up Frontend..."
# cd "$PROJECT_ROOT/frontend"

# if [ ! -d "node_modules" ]; then
#     echo "Installing npm packages..."
#     npm install
# fi

# echo "Starting Frontend on http://localhost:3000"
# npm start &
# FRONTEND_PID=$!

# echo ""
# echo "✅ Services running:"
# echo "   Backend:  http://localhost:8000"
# echo "   Frontend: http://localhost:3000"
# echo ""
# echo "Press Ctrl+C to stop all services"

trap "kill $BACKEND_PID 2>/dev/null; exit" SIGINT SIGTERM
wait
