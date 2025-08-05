# Malfian's Vault - MUD Inventory Management System

A comprehensive Python-based inventory management system for Realms of Despair MUD players. Track your characters, inventory, equipment, and house storage with a beautiful web interface.

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-green.svg)
![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)

## 🌟 Features

### Character Management
- **Multi-Character Support**: Scan 270+ characters efficiently (~9 seconds per character)
- **Complete Character Profiles**: Level, class, race, alignment, organizations, equipment stats
- **Smart Character Deduplication**: Prevents duplicate entries with case-insensitive matching
- **Custom Role Assignment**: Add personal role/purpose tags to characters
- **Prestige Class Support**: Full support for dual-class and prestige characters

### Inventory & Equipment Scanning
- **Smart Container Detection**: Automatically detects and scans containers in inventory
- **Dynamic Container Mapping**: JSON-based system for flexible container keyword management
- **Equipment Tracking**: Comprehensive equipment scanning with empty slot detection
- **House Storage Integration**: Scan multi-room house storage with container support
- **Item Flag Handling**: Properly handles magical item flags like (Glowing), (Magical), etc.
- **Deduplication**: Prevents duplicate items from being recorded multiple times

### Web Interface
- **Malfian's Vault Theme**: Beautiful dark theme with authentic MUD styling
- **Character Table**: Sortable, filterable table with class-based color coding
- **Treasury View**: Consolidated inventory view across all characters and containers
- **Advanced Filtering**: Filter by class (including prestige), race, gender, alignment, equipment needs
- **Real-time Role Editing**: Edit character roles directly in the web interface
- **Responsive Design**: Bootstrap 5 with custom MUD-themed styling

### House & Storage Management
- **Multi-Room House Support**: Scan entire houses with room-by-room container detection
- **House Configuration**: CSV-based house setup with room and container mappings
- **Storage Character Support**: Special handling for storage/mule characters
- **Container Management Interface**: Web interface for managing container mappings

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Git (for cloning the repository)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/malfians-vault.git
   cd malfians-vault
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your characters**
   ```bash
   cp characters.csv.example characters.csv
   # Edit characters.csv with your character credentials
   ```

4. **Configure houses (optional)**
   ```bash
   cp houses_v2.csv.example houses_v2.csv
   # Edit houses_v2.csv with your house configurations
   ```

### Usage

#### Full Character Scan
```bash
python main.py
```

#### Single Character Scan
```bash
python main.py --single CharacterName
```

#### House Scan (for homeowner characters)
```bash
python main.py --house --single CharacterName
```

#### Start Web Interface
```bash
python web_viewer.py
```
Then visit `http://localhost:5000` in your browser.

## 📁 File Structure

```
malfians-vault/
├── main.py                    # Main scanning application
├── web_viewer.py             # Flask web interface
├── config.py                 # Configuration settings
├── requirements.txt          # Python dependencies
├── characters.csv.example    # Example character configuration
├── houses_v2.csv.example     # Example house configuration  
├── container_mappings.json   # Smart container detection mappings
├── inventory_scanner.py      # Core inventory scanning logic
├── container_manager.py      # Container detection and management
├── data_manager.py          # Data processing and storage
├── mud_client.py            # MUD telnet connection handling
├── house_scanner_v2.py      # Multi-room house scanning
├── house_manager_v2.py      # House configuration management
├── templates/               # Web interface templates
│   ├── character_table.html # Main character overview
│   ├── consolidated_inventory.html # Treasury view
│   └── container_management.html # Container management
├── static/                  # Web assets
├── logs/                    # Scan log files
└── archive/                 # Backup data files
```

## 🔧 Configuration

### Character Setup (`characters.csv`)
```csv
username,password,notes
MyCharacter,MyPassword,Main character
AltCharacter,AltPassword,Storage alt
```

### House Setup (`houses_v2.csv`)
```csv
character,room_name,containers
Kaan,North Storage,"cabinet,wardrobe,chest"
Kaan,South Storage,"shelf,trunk"
```

### Container Mappings (`container_mappings.json`)
```json
{
  "container_mappings": {
    "a laundry basket": "my.basket",
    "a Gnomish crafted metal potion container": "my.metal-container"
  }
}
```

## 🎨 Web Interface Features

### Character Overview
- **Sortable Columns**: Click column headers to sort by any field
- **Advanced Filtering**: Filter by class, race, gender, alignment, equipment needs
- **Prestige Class Support**: "Prestige Only" filter shows all prestige classes
- **Role Management**: Edit character roles with auto-save functionality
- **Visual Indicators**: Class-based color coding, house ownership icons

### Treasury (Consolidated Inventory)
- **Cross-Character Search**: Find items across all characters and storage
- **Container Grouping**: Items organized by location and container
- **Item Flag Toggle**: Show/hide magical item flags for cleaner display
- **Advanced Filters**: Filter by character, location, item type

### Container Management
- **Smart Detection**: Automatically suggests new containers found in inventory
- **Easy Mapping**: Web interface for adding container keyword mappings
- **Real-time Updates**: Changes take effect immediately

## 📈 Performance

- **Optimized Scanning**: ~9 seconds per character (down from 80+ seconds)
- **Efficient Data Storage**: Incremental updates, deduplication
- **Fast Web Interface**: DataTables with pagination for large datasets  
- **Memory Efficient**: Processes hundreds of characters without issues

## 🔍 Advanced Features

### Smart Container Detection
The system automatically detects containers in character inventory and attempts to scan them. If a container isn't recognized, it's logged for manual mapping.

### Prestige Class Filtering
Advanced filtering system that understands the relationship between base classes and their prestige variations:
- Mage → Mage-Cleric, Mage-Thief, Mage-Warrior, Mage-Druid
- Nephandi → Infernalist
- Paladin → Knight
- And more...

### Equipment Needs Tracking
Automatically generates equipment needs lists based on empty equipment slots, helping you identify what gear your characters still need.

### House Storage Integration
Seamlessly integrates house storage into your inventory system, treating house containers as extensions of character inventory.

## 🛠️ Development

### Adding New Container Types
1. Use the Container Management web interface, or
2. Manually edit `container_mappings.json`
3. Run a test scan to verify the mapping works

### Extending Character Data
Character statistics are parsed from MUD score and whois commands. Additional fields can be added by modifying the parsing logic in `inventory_scanner.py`.

### Custom Themes
The web interface uses CSS custom properties for easy theme customization. Modify the `:root` variables in the templates to create your own theme.

## 🐛 Troubleshooting

### Common Issues

**Container not detected**: Check if the container name includes item flags like "(Magical)". The system strips these automatically, but the mapping should use the clean name.

**Character duplicates**: Run the cleanup scripts in the repository to merge duplicate character data.

**House scanning fails**: Verify the house configuration in `houses_v2.csv` matches the actual room names and container keywords.

### Logging
All scans are logged to the `logs/` directory with detailed timestamps and error information.

## 📊 Data Management

### Backup and Restore
The system automatically creates timestamped backups of all data. Look for files like:
- `character_stats_YYYYMMDD_HHMMSS.csv`
- `inventory_backup_YYYYMMDD_HHMMSS.csv`

### Data Cleanup
Several utility scripts are included for data maintenance:
- `clean_duplicate_data.py` - Remove duplicate entries
- `fix_character_case.py` - Fix character name casing issues
- `archive_old_files.py` - Move old files to archive directory

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Realms of Despair MUD community
- Bootstrap and DataTables for the beautiful UI components
- All the beta testers who helped refine the system

## 📞 Support

For questions, issues, or feature requests, please open an issue on GitHub or contact the development team.

---

**Made with ❤️ for the Realms of Despair community**