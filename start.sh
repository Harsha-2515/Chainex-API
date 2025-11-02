#!/bin/bash
set -e

# Start Rasa action server in the background
cd actions
rasa run actions --port 5055 --cors "*" &
cd ..

# Get Render's PORT or fallback to 5005
PORT_TO_USE=${PORT:-5005}

# Start Rasa server properly
rasa run --enable-api --cors "*" --host 0.0.0.0 --port ${PORT_TO_USE}
