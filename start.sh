#!/bin/bash
set -e

# start action server on port 5055 in background (default actions port)
cd actions || exit 1
# ensure actions run on port 5055 explicitly
rasa run actions -p 5055 &

# return to root and start Rasa API, using Render's $PORT if set (fallback to 5005)
cd ..

PORT_TO_USE=${PORT:-5005}
rasa run --enable-api --cors "*" --port "$PORT_TO_USE" --host "0.0.0.0"