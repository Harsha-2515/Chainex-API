#!/usr/bin/env bash
set -e

# Run the action server in background (from /app/actions)
( cd actions && rasa run actions --port 5055 --host 0.0.0.0 & )

# Run the main Rasa server (from /app)
rasa run --enable-api --cors "*" --host 0.0.0.0 --port 5005
