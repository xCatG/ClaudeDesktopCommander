import os
import pathlib

# Configuration file paths
CONFIG_FILE = os.path.join(os.getcwd(), "config.json")
LOG_FILE = os.path.join(os.getcwd(), "server.log")
ERROR_LOG_FILE = os.path.join(os.getcwd(), "error.log")

# Default settings
DEFAULT_COMMAND_TIMEOUT = 1000  # milliseconds