#!/bin/bash
set -e

# Start the action server on port 5055 in the background
cd actions
rasa run actions --port 5055 &
cd ..

# Wait a few seconds to ensure the action server starts
sleep 5

# Start the Rasa main API (Render sets $PORT automatically)
PORT_TO_USE=${PORT:-5005}
echo "Starting Rasa server on port $PORT_TO_USE"
exec rasa run --enable-api --cors "*" --port $PORT_TO_USE --host 0.0.0.0
