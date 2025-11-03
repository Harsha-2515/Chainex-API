#!/usr/bin/env bash
set -e

# Train model if no models exist
if [ ! -d "models" ] || [ -z "$(ls -A models 2>/dev/null)" ]; then
    echo "Training model..."
    rasa train
fi

# Start actions server in background
echo "Starting Rasa actions on port 5055"
rasa run actions --port 5055 &

# Start the main Rasa server on Render's assigned $PORT
# To keep it public, use the first line (no token). To protect it, use the second line and set RASA_TOKEN in Render env.
echo "Starting Rasa server on port $PORT"
# Public:
rasa run --enable-api --cors "*" --port $PORT
# Token-protected (uncomment and comment the Public line above):
# rasa run --enable-api --cors "*" --port $PORT --auth-token "$RASA_TOKEN"