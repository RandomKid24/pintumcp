#!/bin/sh
# Copy the Python sources into the npm package (the npm copy is what npx installs).
cd "$(dirname "$0")/.." && cp server.py notifier.py events.py config.py status.py tray.py hook.py panel.html npm/python/ && cp assets/pintumcp-icon.png npm/python/assets/ && mkdir -p npm/python/assets/icons && cp assets/icons/*.png npm/python/assets/icons/ && mkdir -p npm/python/assets/menubar && cp assets/menubar/*.png npm/python/assets/menubar/ && mkdir -p npm/python/assets/pet && cp assets/pet/*.gif npm/python/assets/pet/ && cp README.md npm/README.md
