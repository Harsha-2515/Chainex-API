#!/usr/bin/env bash
set -e

# Train model if no models exist
if [ ! -d "models" ]; then
    echo "Training model..."
    rasa train
fi

cd actions & rasa run actions & cd ..

# Start the main Rasa server only
echo "Starting Rasa server on port $PORT"
rasa run --enable-api --cors "*" --port $PORT