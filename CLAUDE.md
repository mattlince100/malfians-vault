# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
Malfian's Vault is a Python-based inventory management system for Realms of Despair MUD players. It connects to the game server via telnet, scans character inventories/equipment/houses, and presents data through a Flask web interface.

## Essential Commands

### Run the Application
```bash
# Main scanner with web interface
python main.py

# Scan specific characters
python main.py --characters "CharName1,CharName2"

# Web viewer only (no scanning)
python web_viewer.py
```

### Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Setup configuration files
cp characters.csv.example characters.csv
cp houses_v2.csv.example houses_v2.csv
# Edit these files with actual character/house data
```

## Architecture Overview

### Core Data Flow
1. **main.py** orchestrates character scanning with pause/resume/cancel controls
2. **mud_client.py** establishes telnet connections to MUD server
3. **inventory_scanner.py** parses MUD responses and extracts item/equipment data
4. **data_manager.py** processes and stores data in CSV format
5. **web_viewer.py** serves Flask web interface on port 5000

### Key Design Patterns
- **Container Detection**: Dynamic keyword mapping system in `container_mappings.json` that learns new container types
- **Deduplication**: Smart duplicate prevention using item fingerprints (name + keywords + location)
- **Rate Limiting**: 0.5 second delays between commands to avoid server overload
- **House Scanning**: Multi-room navigation with configurable room paths in `houses_v2.csv`

### Configuration Management
- **config.py**: Central configuration with all settings, paths, and constants
- **Environment Variables**: Optional `.env` file for sensitive credentials
- **CSV-based configs**: Character credentials and house configurations stored in CSV

### Web Interface Architecture
- **Templates**: Jinja2 templates in `templates/` with Bootstrap 5 and DataTables
- **Dark Theme**: CSS custom properties for MUD-inspired styling
- **AJAX Features**: Real-time role editing with auto-save
- **Responsive Tables**: DataTables integration for sorting/filtering/pagination

## Important Implementation Details

### Telnet Connection Handling
- Uses `telnetlib3` for async telnet operations
- Automatic reconnection on failures
- Command queue with response parsing
- Special handling for MUD prompts and ANSI codes

### Data Storage
- CSV files in root directory for inventory data
- Character stats stored separately from items
- Incremental updates preserve existing data
- Archive system for old scan files

### Container System
- Automatic container detection via keyword matching
- Learning system updates `container_mappings.json`
- Handles nested containers (bags within lockers)
- Special handling for house storage containers

### Performance Optimizations
- Fast scanning mode (~9 seconds per character)
- Batch processing with configurable batch sizes
- Smart caching of container mappings
- Efficient CSV operations with pandas

## Testing & Quality
Note: No formal testing framework is currently implemented. When adding new features:
- Test with sample character data first
- Verify MUD response parsing with actual game output
- Check web interface rendering across browsers
- Monitor scan logs in `logs/` directory for errors

## Common Development Tasks

### Adding New Features
- Scanner modifications: Update `inventory_scanner.py` and `data_manager.py`
- Web interface changes: Modify templates and `web_viewer.py` routes
- New data fields: Update CSV headers in `config.py` and data processing

### Debugging
- Enable debug logging in `config.py`
- Check `logs/` directory for scan logs
- Use `--test` flag for dry runs without server connection
- Monitor Flask debug output for web issues