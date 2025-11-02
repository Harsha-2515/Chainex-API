#!/bin/bash

cd actions
rasa run actions &
cd ..

rasa run --enable-api --cors "*" --port 5005
wait