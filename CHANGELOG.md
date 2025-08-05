# Changelog

All notable changes to Malfian's Vault MUD Inventory Management System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.1] - 2025-08-05

### Fixed
- Fixed inventory parsing for characters with exactly 1 item (singular vs plural bug)
- Fixed missing "Prestige Only" dropdown option in class filter
- Cleaned up repository structure (removed nested directories and test files)

### Changed
- Simplified distribution to include only essential files
- Removed v1 house files (v2 is backward compatible)
- Removed all test_*.py files from distribution

---

## [2.0.0] - 2025-08-05

### 🎉 Major Release - Complete System Overhaul

This release represents a complete transformation of the MUD Inventory Manager into "Malfian's Vault" - a comprehensive, production-ready system with massive performance improvements, a stunning web interface, and advanced features.

### ✨ Added

#### Web Interface & User Experience
- **Complete Web Interface Redesign**: Beautiful "Malfian's Vault" theme with authentic MUD styling
- **Dark Theme**: Custom CSS with magical purple/blue color scheme inspired by fantasy aesthetics
- **Responsive Design**: Bootstrap 5 with mobile-friendly layout
- **Character Overview Table**: Sortable, filterable table with pagination support
- **Treasury View**: Consolidated inventory view across all characters and containers
- **Container Management Interface**: Web-based container mapping management
- **Real-time Role Editing**: Edit character roles directly in web interface with auto-save
- **Advanced Filtering System**: Filter by class, race, gender, alignment, equipment needs
- **Prestige Class Support**: "Prestige Only" filter and comprehensive prestige class mapping
- **Visual Indicators**: Class-based color coding, house ownership icons

#### Smart Container System
- **Smart Container Detection**: Automatically detects containers in character inventory
- **Dynamic Container Mapping**: JSON-based system for flexible container management
- **Item Flag Handling**: Properly strips magical item flags like (Glowing), (Magical), etc.
- **Article-Flexible Matching**: Handles "a laundry basket" vs "laundry basket" variations
- **Unknown Container Logging**: Logs potential containers for manual review
- **Web-Based Container Management**: Add/remove container mappings through web interface

#### House Storage Integration
- **Multi-Room House Support**: Scan entire houses with room-by-room container detection
- **House Configuration System**: CSV-based house setup with room and container mappings
- **Seamless Integration**: House containers appear in Treasury alongside personal containers
- **House Character Support**: Special handling for house-owning characters
- **Storage Room Management**: Support for multiple storage rooms with different containers

#### Character Management
- **Custom Role Assignment**: Add personal role/purpose tags to characters
- **Prestige Class Filtering**: Advanced filtering for dual-class and prestige characters
- **Organization Tracking**: Comprehensive org membership (Orders/Sects/Guilds) with roles
- **Equipment Needs Tracking**: Automatically generates equipment needs based on empty slots
- **Character Deduplication**: Smart prevention of duplicate character entries
- **Case-Insensitive Handling**: Proper handling of character name capitalization

#### Performance & Reliability
- **Massive Performance Improvement**: ~9 seconds per character (down from 80+ seconds)
- **Smart Data Management**: Incremental updates, intelligent deduplication
- **Robust Error Handling**: Comprehensive error recovery and logging
- **Memory Efficiency**: Handles hundreds of characters without issues
- **Fast Web Interface**: DataTables with efficient pagination for large datasets

#### Data Management
- **Backup System**: Automatic timestamped backups of all data
- **Data Cleanup Tools**: Scripts for removing duplicates and fixing data issues
- **Archive Management**: Organized storage of historical scan data
- **Export Capabilities**: Multiple export formats for data analysis

### 🔧 Enhanced

#### Scanning Engine
- **Improved MUD Parser**: Better handling of various item formats and edge cases
- **Equipment Slot Detection**: Comprehensive mapping of all equipment slots
- **Quantity Parsing**: Better detection of item quantities in parentheses
- **ANSI Color Handling**: Proper stripping of color codes from MUD output
- **Connection Stability**: Improved telnet connection handling and retry logic

#### Character Statistics
- **Extended Whois Parsing**: Age, gender, honor, rank, organizational memberships
- **Score Command Enhancement**: Level, race, class, alignment, gold, equipment stats
- **Organization Roles**: Leader/Second/Member roles for Orders/Sects/Guilds
- **Bio Status Tracking**: Whether characters have created character biographies
- **Alignment Categorization**: Smart alignment grouping (Devout/Neutral/Evil)

#### User Interface
- **Column Sorting**: All table columns are sortable with intelligent data type handling
- **Filter Persistence**: Filter states remembered across sessions
- **Search Functionality**: Global search across all character data
- **Pagination Controls**: Flexible page size options (25/50/100/250/500/All)
- **Responsive Filters**: Real-time filter application without page refresh
- **Status Indicators**: Clear feedback on filter state and record counts

### 🐛 Fixed

#### Data Integrity
- **Character Duplication**: Eliminated duplicate character entries through case-insensitive matching
- **Item Duplication**: Fixed MUD sending duplicate item lines causing data bloat
- **Container Detection**: Fixed container names with item flags not being recognized
- **House Container Integration**: Fixed house containers not appearing in Treasury
- **Equipment Parsing**: Fixed equipment slots not being properly categorized

#### Web Interface
- **Dropdown Population**: Fixed "Prestige Only" option not appearing in class filter
- **Template Errors**: Fixed Jinja2 template errors with match/search filters
- **ANSI Color Codes**: Fixed color codes appearing in web interface
- **Container Filtering**: Fixed hardcoded container lists preventing dynamic detection
- **Role Column Sorting**: Made Role column properly sortable alphabetically

#### Performance Issues
- **Scan Speed**: Optimized from 80+ seconds to ~9 seconds per character
- **Memory Usage**: Fixed memory leaks during large batch scans
- **Web Response Time**: Optimized data loading and table rendering
- **Database Efficiency**: Improved data storage and retrieval mechanisms

### 🔄 Changed

#### Architecture
- **Modular Design**: Separated concerns into focused modules (scanner, manager, viewer)
- **JSON Configuration**: Moved container mappings from code to JSON configuration
- **CSV-Based Setup**: Simplified character and house configuration with CSV files
- **Template System**: Complete template reorganization with consistent styling

#### User Experience
- **Simplified Commands**: Streamlined command-line interface with clear options
- **Better Defaults**: Sensible default settings that work out of the box
- **Improved Documentation**: Comprehensive README with setup and usage instructions
- **Error Messages**: More helpful error messages with actionable solutions

#### Data Format
- **Extended Character Fields**: Added new fields for organizations, roles, equipment stats
- **Container Location Format**: Standardized container location naming (my.*, house:*)
- **Timestamp Format**: ISO format timestamps for better sorting and parsing
- **Backup Naming**: Consistent naming convention for backup files

### 📚 Documentation

#### Comprehensive Documentation
- **README Overhaul**: Complete rewrite with step-by-step setup instructions
- **Feature Documentation**: Detailed explanation of all features and capabilities
- **Configuration Guide**: Clear examples for characters.csv, houses.csv, containers.json
- **Troubleshooting Section**: Common issues and solutions
- **Development Guide**: Instructions for extending and customizing the system

#### Code Documentation
- **Inline Comments**: Comprehensive code comments explaining complex logic
- **Function Documentation**: Docstrings for all major functions and classes
- **Type Hints**: Added type hints throughout the codebase for better maintainability
- **Architecture Overview**: High-level system architecture documentation

### 🛠️ Technical Improvements

#### Code Quality
- **Error Handling**: Comprehensive try/catch blocks with meaningful error messages
- **Logging System**: Detailed logging with configurable levels and rotation
- **Code Organization**: Modular architecture with clear separation of concerns
- **Configuration Management**: Centralized configuration with environment variable support

#### Testing & Reliability
- **Input Validation**: Robust validation of user inputs and MUD responses
- **Edge Case Handling**: Comprehensive handling of unusual MUD output formats
- **Connection Recovery**: Automatic retry and recovery from connection issues
- **Data Validation**: Integrity checks to prevent corrupted data storage

### 🎯 Migration Notes

#### Upgrading from v1.x
1. **Backup existing data** - Archive your old CSV files
2. **Update configuration** - New format for characters.csv and houses.csv
3. **Container mappings** - Convert any hardcoded containers to container_mappings.json
4. **Web interface** - Launch web_viewer.py to access the new interface
5. **Data migration** - Run a fresh scan to populate the new data format

#### Breaking Changes
- Configuration file format changed from hardcoded Python to CSV/JSON
- Container detection moved from hardcoded list to dynamic JSON mapping
- Web interface completely redesigned (old templates not compatible)
- Command-line arguments updated (see --help for new options)

---

## [1.0.0] - 2025-08-01

### Initial Release
- Basic MUD inventory scanning
- CSV export functionality
- Simple character management
- Hardcoded container scanning
- Basic web interface

---

**Note**: This changelog follows semantic versioning. Given the massive scope of changes in v2.0.0, this represents a major version bump with significant new features, performance improvements, and breaking changes.