#!/bin/bash
# Move to the project directory
cd /Users/apple/college-bot

echo "🤖 Stopping any existing DBIT server..."
pkill -f "python3 server.py" 2>/dev/null

echo "🚀 Starting DBIT Assistant Server..."
# Run the server in the background
python3 server.py &
SERVER_PID=$!

echo "⏳ Waiting for server to initialize..."
sleep 4

echo "🌐 Opening web application in your default browser..."
open http://localhost:8000

echo "✅ DBIT Assistant is now running!"
echo "⚠️  Keep this window open. If you want to stop the server, press Ctrl+C or close this window."

# Wait for the background process so the terminal stays open
wait $SERVER_PID
