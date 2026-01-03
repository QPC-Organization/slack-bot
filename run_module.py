#!/usr/bin/env python3
"""
Launcher script to run the Slack bot as a module with proper path handling.
This fixes the Python 3.13 virtual environment path resolution issue on Windows.
"""

import sys
import os

# Add the virtual environment's site-packages to Python path
venv_site_packages = os.path.join(os.getcwd(), 'venv', 'Lib', 'site-packages')
if venv_site_packages not in sys.path:
    sys.path.insert(0, venv_site_packages)

# Now run the module
if __name__ == "__main__":
    import src.app





