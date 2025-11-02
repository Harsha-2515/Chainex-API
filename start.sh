#!/usr/bin/env bash
set -e

# Train the model if no models exist
if [ ! -d "models" ]; then
    rasa train
fi

# Start action server
cd actions && rasa run actions --port 5055 --host 0.0.0.0 &

# Wait for action server
sleep 10

# Start main server
rasa run --enable-api --cors "*" --host 0.0.0.0 --port 5005