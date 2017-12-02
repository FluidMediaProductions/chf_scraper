#!/usr/bin/env bash

echo Starting Gunicorn.
exec gunicorn server:app \
    --bind 0.0.0.0:80 \
    --workers 3