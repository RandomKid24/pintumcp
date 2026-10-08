#!/bin/sh
# Copy the Python sources into the npm package (the npm copy is what npx installs).
cd "$(dirname "$0")/.." && cp server.py notifier.py events.py config.py status.py tray.py hook.py npm/python/ && cp assets/pintumcp-icon.png npm/python/assets/ && mkdir -p npm/python/assets/icons && cp assets/icons/*.png npm/python/assets/icons/ && mkdir -p npm/python/assets/menubar && cp assets/menubar/*.png npm/python/assets/menubar/ && cp README.md npm/README.md
