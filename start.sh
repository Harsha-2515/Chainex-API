#!/bin/bash
set -e

# Start action server on port 5055
cd actions
rasa run actions --port 5055 --cors "*" &
cd ..

# Use Render's $PORT environment variable (default to 5005)
PORT_TO_USE=${PORT:-5005}

# Start Rasa server
rasa run --enable-api --cors "*" --port $PORT_TO_USE --host 0.0.0.0