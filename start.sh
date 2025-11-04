#!/usr/bin/env bash
set -e

# Use Render's assigned port or default for local dev
APP_PORT="${PORT:-5005}"

# Check if model exists
if [ ! -d "models" ] || [ -z "$(ls -A models/*.tar.gz 2>/dev/null)" ]; then
    echo "ERROR: No model .tar.gz found in ./models/"
    echo "Please train locally (rasa train) and copy the .tar.gz into ChainEX-API/models/"
    exit 1
fi

# Find the latest model
LATEST_MODEL=$(ls -t models/*.tar.gz 2>/dev/null | head -1)
if [ -z "$LATEST_MODEL" ]; then
    echo "ERROR: No valid model found in models/"
    exit 1
fi

echo "Found model: $LATEST_MODEL"

# Start actions server in background (from root - it finds actions/ automatically)
echo "Starting Rasa actions on port 5055"
cd actions & rasa run actions --port 5055 & cd..

# Start the main Rasa server (from root - it needs config.yml, domain.yml here)
echo "Starting Rasa server on port ${APP_PORT} with model: ${LATEST_MODEL}"
rasa run --enable-api --cors "*" -i 0.0.0.0 --port "${APP_PORT}" -m "${LATEST_MODEL}"