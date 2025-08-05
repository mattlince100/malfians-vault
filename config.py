"""Configuration settings for MUD Inventory Manager."""

import os
from datetime import datetime

# MUD Connection Settings
MUD_HOST = "realmsofdespair.com"
MUD_PORT = 4000
CONNECTION_TIMEOUT = 30  # seconds
COMMAND_DELAY = 0.1  # seconds between commands
LOGIN_DELAY = 3.0  # seconds after login
RATE_LIMIT_DELAY = 3.0  # seconds between characters

# Inventory Settings
# CONTAINERS now handled dynamically by Smart Inventory Scan - see container_mappings.json
EQUIPMENT_COMMAND = "equipment"
INVENTORY_COMMAND = "inventory"

# House Inventory Settings
HOUSES_FILE = "houses.csv"
HOUSE_MOVEMENT_DELAY = 2.0  # seconds between movement commands
HOUSE_EXAMINE_DELAY = 2.0   # seconds between examining containers

# File Settings
CHARACTERS_FILE = "characters.csv"
GOOGLE_CREDENTIALS_FILE = "credentials.json"
OUTPUT_CSV_FILE = f"inventory_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
LOG_FILE = f"logs/scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Google Sheets Settings
SPREADSHEET_NAME = "MUD Inventory Database"
MAIN_WORKSHEET_NAME = "All Items"
SUMMARY_WORKSHEET_NAME = "Summary"

# Parsing Settings
ITEM_PATTERNS = {
    'quantity': r'^(\d+)\s+(.+)$',  # "3 apples"
    'single': r'^(?:a|an|the)\s+(.+)$',  # "a sword"
    'equipment': r'^<(.+?)>\s*(.+)$',  # "<worn on body> armor"
}

# Retry Settings
MAX_RETRIES = 3
RETRY_DELAY = 5.0  # seconds

# Debug Settings
DEBUG_MODE = os.getenv("DEBUG", "False").lower() == "true"
SAVE_RAW_OUTPUT = True