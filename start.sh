#!/bin/bash
set -e

# Start the action server on port 5055 in background
cd actions
rasa run actions --port 5055 &
cd ..

# Start the Rasa API (Render will set $PORT automatically)
PORT_TO_USE=${PORT:-5005}
exec rasa run --enable-api --cors "*" --port "$PORT_TO_USE" --host 0.0.0.0