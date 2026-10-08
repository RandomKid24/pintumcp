#!/bin/sh
# Copy the Python sources into the npm package (the npm copy is what npx installs).
cd "$(dirname "$0")/.." && cp server.py notifier.py events.py config.py npm/python/ && cp assets/pintumcp-icon.png npm/python/assets/ && mkdir -p npm/python/assets/icons && cp assets/icons/*.png npm/python/assets/icons/ && cp README.md npm/README.md
