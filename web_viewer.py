#!/usr/bin/env python3
"""
MUD Inventory Web Viewer
Beautiful web interface for viewing and managing character inventories
"""

import os
import pandas as pd
import numpy as np
from flask import Flask, render_template, request, jsonify, send_from_directory, session
import secrets
from pathlib import Path
import glob
from datetime import datetime
import json
from container_manager import ContainerManager

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

def generate_csrf_token():
    """Generate a CSRF token for the session."""
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(16)
    return session['csrf_token']

def validate_csrf_token(token):
    """Validate CSRF token."""
    return token and 'csrf_token' in session and token == session['csrf_token']

# Make CSRF token available in all templates
app.jinja_env.globals['csrf_token'] = generate_csrf_token

def get_class_icon(character_class):
    """Get appropriate Font Awesome icon for character class."""
    if not character_class:
        return 'fas fa-user'
    
    class_icons = {
        # Realms of Despair Classes - WoW-inspired icons (using available FA icons)
        'warrior': 'fas fa-shield-alt',  # WoW warrior = protective shield
        'thief': 'fas fa-user-secret',  # WoW rogue = stealth/secret agent
        'mage': 'fas fa-hat-wizard',  # WoW mage = wizard hat
        'cleric': 'fas fa-hands-praying',  # WoW priest = holy prayer hands
        'ranger': 'fas fa-crosshairs',  # WoW hunter = target/crosshairs
        'druid': 'fas fa-seedling',  # WoW druid = nature/growth
        'vampire': 'fas fa-tint',  # Vampire = blood drop
        'augurer': 'fas fa-eye',  # Divination/foresight = all-seeing eye
        'paladin': 'fas fa-fist-raised',  # WoW paladin = righteous might
        
        # Advanced/Prestige Classes - WoW-inspired
        'bladesinger': 'fas fa-music',  # Musical warrior (bard-like)
        'fathomer': 'fas fa-anchor',  # Sea-themed = anchor
        'nephandi': 'fas fa-skull',  # Corrupted/dark magic = skull
        'barbarian': 'fas fa-fire',  # WoW warrior variant = rage/fire
        'infernalist': 'fas fa-flame',  # Demonic = hellfire
        'dread': 'fas fa-skull-crossbones',  # Death knight = skull & bones
        'knight': 'fas fa-chess-knight',  # Knightly = knight chess piece
        'hunter': 'fas fa-bullseye',  # Classic hunter = perfect aim
        
        # Multi-class combinations
        'thief-warrior': 'fas fa-user-ninja',  # Rogue-warrior = ninja
        'cleric-druid': 'fas fa-spa',  # Nature-holy hybrid = harmony
        'druid-cleric': 'fas fa-leaf',  # Druid-primary = leaf
        
        # House/Storage (not actual classes)
        'house storage': 'fas fa-home',
        'storage': 'fas fa-warehouse'
    }
    
    # Convert to lowercase for matching
    class_lower = str(character_class).lower().strip()
    
    # Check for exact matches first
    if class_lower in class_icons:
        return class_icons[class_lower]
    
    # Check for partial matches
    for class_key, icon in class_icons.items():
        if class_key in class_lower:
            return icon
    
    # Default icon for unknown classes
    return 'fas fa-user-circle'

# Make the function available as a template filter
app.jinja_env.filters['class_icon'] = get_class_icon

def get_class_color(character_class):
    """Get appropriate color for character class."""
    if not character_class:
        return 'var(--accent-color)'
    
    class_colors = {
        # Realms of Despair Classes - Matching character_table.html colors
        'warrior': '#D2691E',  # Light Brown (matching row-warrior)
        'thief': '#FFFF00',  # Yellow (matching row-thief)
        'mage': '#00FFFF',  # Cyan (matching row-mage)
        'cleric': '#FFFFFF',  # White (matching row-cleric)
        'ranger': '#32CD32',  # Forest Green (matching row-ranger)
        'druid': '#00FF00',  # Green (matching row-druid)
        'vampire': '#FF6B6B',  # Bright Red (matching row-vampire)
        'augurer': '#B0B0B0',  # Gray (matching row-augurer)
        'paladin': '#FFB6C1',  # Pink (matching row-paladin)
        
        # Advanced/Prestige Classes - Matching character_table.html colors
        'bladesinger': '#CD5C5C',  # Dull Red (matching row-bladesinger)
        'fathomer': '#5F9EA0',  # Ocean Blue (matching row-fathomer)
        'nephandi': '#9400D3',  # Purple (matching row-nephandi)
        'barbarian': '#FFA500',  # Orange (matching row-barbarian)
        'infernalist': '#9400D3',  # Purple (same as nephandi)
        'dread': '#FF6B6B',  # Bright Red (matching row-dread, same as vampire)
        'knight': '#FFB6C1',  # Pink (same as paladin)
        'hunter': '#32CD32',  # Forest Green (same as ranger)
        
        # Multi-class combinations - Use primary class color
        'thief-warrior': '#FFFF00',  # Yellow (thief primary)
        'cleric-druid': '#FFFFFF',  # White (cleric primary)
        'druid-cleric': '#00FF00',  # Green (druid primary)
        
        # House/Storage (not actual classes)
        'house storage': 'var(--house-color)',
        'storage': 'var(--house-color)'
    }
    
    # Convert to lowercase for matching
    class_lower = str(character_class).lower().strip()
    
    # Check for exact matches first
    if class_lower in class_colors:
        return class_colors[class_lower]
    
    # Check for partial matches
    for class_key, color in class_colors.items():
        if class_key in class_lower:
            return color
    
    # Default color
    return 'var(--accent-color)'

# Make the color function available as a template filter
app.jinja_env.filters['class_color'] = get_class_color

class InventoryViewer:
    def __init__(self):
        self.df = None
        self.stats_df = None
        self.container_manager = ContainerManager()
        self.load_latest_data()
    
    def clean_nan_values(self, data):
        """Clean NaN values from data to make it JSON serializable."""
        if isinstance(data, dict):
            return {k: self.clean_nan_values(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.clean_nan_values(item) for item in data]
        elif pd.isna(data) or (isinstance(data, float) and np.isnan(data)):
            return None
        else:
            return data
        
    def load_latest_data(self):
        """Load the most recent CSV files."""
        print(f"Reloading data at {datetime.now().strftime('%H:%M:%S')}")
        
        # Load inventory data
        csv_files = glob.glob("inventory_backup_*.csv")
        if csv_files:
            latest_file = max(csv_files, key=os.path.getctime)
            self.df = pd.read_csv(latest_file)
            print(f"Loaded inventory data from: {latest_file}")
        else:
            print("No inventory CSV files found")
            self.df = pd.DataFrame()
            
        # Load character stats
        stats_files = glob.glob("character_stats_*.csv")
        if stats_files:
            latest_stats_file = max(stats_files, key=os.path.getctime)
            # Read CSV with proper handling of escape sequences
            self.stats_df = pd.read_csv(latest_stats_file, encoding='utf-8', escapechar=None)
            print(f"Loaded character stats from: {latest_stats_file}")
            print(f"Successfully reloaded {len(self.df)} items and {len(self.stats_df)} character stats")
            
            # Debug: Check if ANSI codes survive CSV loading
            abygale_row = self.stats_df[self.stats_df['character'] == 'Abygale']
            if not abygale_row.empty and 'raw_score' in abygale_row.columns:
                raw_score = str(abygale_row['raw_score'].iloc[0])
                escape_char = chr(27)
                literal_pattern = '\\x1b'
                print(f"Debug CSV loading: Abygale raw_score has actual escape char: {escape_char in raw_score}")
                print(f"Debug CSV loading: Abygale raw_score has \\x1b pattern: {literal_pattern in raw_score}")
                print(f"Debug CSV loading: First 100 chars: {repr(raw_score[:100])}")
        else:
            print("No character stats files found")
            self.stats_df = pd.DataFrame()
    
    def get_characters(self):
        """Get list of all characters."""
        if self.df.empty:
            return []
        return sorted(self.df['character'].unique().tolist())
    
    def get_character_stats(self):
        """Get character statistics with custom roles."""
        if self.stats_df.empty:
            logger.warning("stats_df is empty, no character stats available")
            return []
        
        logger.info(f"Processing {len(self.stats_df)} rows from stats_df")
        logger.info(f"Stats_df columns: {list(self.stats_df.columns)}")
        
        # Check if we have character data vs item data
        if 'item_name' in self.stats_df.columns:
            logger.error("ERROR: stats_df contains item data instead of character data!")
            logger.error("This suggests character_stats.csv file is corrupted with inventory data")
            return []
        
        # Load custom roles
        roles_file = 'character_roles.json'
        custom_roles = {}
        if os.path.exists(roles_file):
            with open(roles_file, 'r') as f:
                custom_roles = json.load(f)
        
        # Convert to dict records and add custom roles
        stats = self.stats_df.to_dict('records')
        
        # Process each character and identify houses
        processed_stats = []
        house_owners = {}
        
        # First pass: identify house owners
        for stat in stats:
            char_name = stat['character']
            if char_name.endswith('_house') or char_name.endswith('_House'):
                owner_name = char_name.replace('_house', '').replace('_House', '')
                house_owners[owner_name.lower()] = char_name
        
        # Second pass: process all characters
        for stat in stats:
            char_name = stat['character']
            char_lower = char_name.lower()
            
            # Add custom role
            stat['custom_role'] = custom_roles.get(char_lower, '')
            
            # Check if this is a house
            if char_name.endswith('_house') or char_name.endswith('_House'):
                stat['is_house'] = True
                stat['owner'] = char_name.replace('_house', '').replace('_House', '')
                # Don't include houses in the main character list
                continue
            else:
                stat['is_house'] = False
                # Check if this character has a house
                stat['has_house'] = char_lower in house_owners
                if stat['has_house']:
                    stat['house_name'] = house_owners[char_lower]
                else:
                    stat['house_name'] = None
            
            processed_stats.append(stat)
        
        # Preserve ANSI codes by converting escape chars to safe JSON format
        for stat in processed_stats:
            if 'raw_score' in stat and stat['raw_score']:
                # Convert actual escape characters to literal \x1b for JSON safety
                raw_score = str(stat['raw_score'])
                if chr(27) in raw_score:  # Has actual escape characters
                    # Replace actual escape chars with literal \x1b for JSON serialization
                    safe_raw_score = raw_score.replace(chr(27), '\\x1b')
                    stat['raw_score'] = safe_raw_score
                elif '[' in raw_score and 'm' in raw_score:
                    # Handle literal bracket sequences like "[0;1;32m" -> "\x1b[0;1;32m"
                    # Convert literal ANSI sequences to proper escape format
                    import re
                    safe_raw_score = re.sub(r'\[(\d+(?:;\d+)*)m', r'\\x1b[\1m', raw_score)
                    stat['raw_score'] = safe_raw_score
                    
        # Clean NaN values before returning
        cleaned_stats = self.clean_nan_values(processed_stats)
                
        return cleaned_stats
    
    def get_character_data(self, character_name):
        """Get all data for a specific character."""
        if self.df.empty:
            return {}
            
        char_data = self.df[self.df['character'] == character_name]
        
        # Organize data by location type
        inventory = char_data[char_data['location'] == 'inventory'].to_dict('records')
        
        # Sort equipment by MUD slot order
        equipment_data = char_data[char_data['location'].str.startswith('equipped:')]
        equipment_order = [
            'used as light', 'worn on finger', 'worn around neck', 'worn on body', 
            'worn on head', 'worn on legs', 'worn on feet', 'worn on hands', 
            'worn on arms', 'worn about body', 'worn about waist', 'worn around wrist',
            'wielded', 'dual wielded', 'worn as shield', 'held', 'worn on ears', 
            'worn on eyes', 'worn on back', 'worn over face', 'worn around ankle'
        ]
        
        equipment = []
        for slot in equipment_order:
            slot_items = equipment_data[equipment_data['location'] == f'equipped:{slot}'].to_dict('records')
            equipment.extend(slot_items)
        
        # Add any remaining equipment slots not in our predefined order
        remaining_equipment = equipment_data[~equipment_data['location'].str.replace('equipped:', '').isin(equipment_order)].to_dict('records')
        equipment.extend(remaining_equipment)
        
        containers = {}
        
        # Check if this is a house character
        if character_name.endswith('_house') or character_name.endswith('_House'):
            # Group house container items by location (format: "house:Room Name:container")
            house_data = char_data[char_data['location'].str.startswith('house:')]
            
            # Parse house locations and group by room and container
            for _, item in house_data.iterrows():
                location = item['location']
                parts = location.split(':')
                if len(parts) == 3:
                    room_name = parts[1]
                    container_name = parts[2]
                    container_key = f"{room_name}:{container_name}"
                    
                    if container_key not in containers:
                        containers[container_key] = []
                    containers[container_key].append(item.to_dict())
        else:
            # Regular character containers - use dynamic detection
            container_data = char_data[
                (char_data['location'].str.startswith('my.')) & 
                (~char_data['location'].isin(['inventory', 'equipped']))
            ]
            
            # Get unique container locations for this character
            unique_containers = container_data['location'].unique().tolist()
            for container in unique_containers:
                containers[container] = container_data[container_data['location'] == container].to_dict('records')
        
        # Get character stats if available
        char_stats = {}
        if not self.stats_df.empty:
            stats_row = self.stats_df[self.stats_df['character'] == character_name]
            if not stats_row.empty:
                char_stats = stats_row.iloc[0].to_dict()
        
        result = {
            'character': character_name,
            'inventory': inventory,
            'equipment': equipment,
            'containers': containers,
            'total_items': len(char_data),
            'total_quantity': int(char_data['quantity'].fillna(0).astype(int).sum()),
            'stats': char_stats  # Add character stats
        }
        
        return self.clean_nan_values(result)
    
    def get_consolidated_inventory(self):
        """Get all inventory items with ANSI conversion applied."""
        if self.df.empty:
            return []
        
        # Convert DataFrame records to dict and clean NaN values
        records = self.df.to_dict('records')
        cleaned_records = self.clean_nan_values(records)
        
        # Apply ANSI conversion to both raw_line and item_name fields
        for item in cleaned_records:
            # Process raw_line
            if 'raw_line' in item and item['raw_line']:
                raw_line = str(item['raw_line'])
                # Handle literal bracket sequences like "[0;1;32m" -> "\x1b[0;1;32m"
                if '[' in raw_line and 'm' in raw_line and chr(27) not in raw_line:
                    import re
                    safe_raw_line = re.sub(r'\[(\d+(?:;\d+)*)m', r'\\x1b[\1m', raw_line)
                    item['raw_line'] = safe_raw_line
                elif chr(27) in raw_line:
                    # Convert actual escape chars to literal \x1b for JSON safety
                    safe_raw_line = raw_line.replace(chr(27), '\\x1b')
                    item['raw_line'] = safe_raw_line
            
            # Also process item_name for ANSI codes (since we're keeping them)
            if 'item_name' in item and item['item_name']:
                item_name = str(item['item_name'])
                # Handle literal bracket sequences like "[0;1;32m" -> "\x1b[0;1;32m"
                if '[' in item_name and 'm' in item_name and chr(27) not in item_name:
                    import re
                    safe_item_name = re.sub(r'\[(\d+(?:;\d+)*)m', r'\\x1b[\1m', item_name)
                    item['item_name'] = safe_item_name
                elif chr(27) in item_name:
                    # Convert actual escape chars to literal \x1b for JSON safety
                    safe_item_name = item_name.replace(chr(27), '\\x1b')
                    item['item_name'] = safe_item_name
                    
        return cleaned_records
    
    def get_treasure_vault(self):
        """Get all items from all containers across all characters."""
        if self.df.empty:
            return []
        
        # Get all container mappings to identify container locations
        container_keywords = list(self.container_manager.get_all_mappings().values())
        
        # Filter for container items (both personal containers and house containers)
        container_items = self.df[
            ((self.df['location'].str.startswith('my.')) & 
             (~self.df['location'].isin(['inventory', 'equipped']))) |
            (self.df['location'].str.startswith('house:'))
        ]
        
        # Group by item name and sum quantities
        vault_data = container_items.groupby(['item_name', 'location']).agg({
            'quantity': lambda x: int(x.fillna(0).astype(int).sum()),
            'character': lambda x: ', '.join(x.unique()),  # Join characters as string
            'raw_line': 'first'
        }).reset_index()
        
        # Clean the data
        records = vault_data.to_dict('records')
        cleaned_records = []
        
        for record in records:
            # Preserve ANSI color codes for web display
            item_name = record['item_name']
            raw_line = record.get('raw_line', '')
            
            # Convert actual escape characters to literal \x1b for JSON safety
            if chr(27) in str(item_name):
                item_name = str(item_name).replace(chr(27), '\\x1b')
                record['item_name'] = item_name
            
            if chr(27) in str(raw_line):
                raw_line = str(raw_line).replace(chr(27), '\\x1b')
                record['raw_line'] = raw_line
            
            # Store raw item name with ANSI codes for display
            record['raw_item_name'] = item_name
            # Also keep clean name for searching/filtering
            if '\\x1b[' in item_name:
                import re
                clean_name = re.sub(r'\\x1b\\[[0-9;]*m', '', item_name).strip()
                record['clean_item_name'] = clean_name
            else:
                record['clean_item_name'] = item_name
            
            cleaned_records.append(record)
        
        return self.clean_nan_values(cleaned_records)
    
    def search_items(self, search_term, location_filter=None):
        """Search for items across all characters."""
        if self.df.empty:
            return []
            
        filtered_df = self.df[self.df['item_name'].str.contains(search_term, case=False, na=False)]
        
        if location_filter and location_filter != 'all':
            if location_filter == 'containers':
                # Filter for all container locations (both personal and house containers)
                filtered_df = filtered_df[
                    ((filtered_df['location'].str.startswith('my.')) & 
                     (~filtered_df['location'].isin(['inventory', 'equipped']))) |
                    (filtered_df['location'].str.startswith('house:'))
                ]
            elif location_filter == 'equipment':
                filtered_df = filtered_df[filtered_df['location'].str.startswith('equipped:')]
            elif location_filter == 'inventory':
                filtered_df = filtered_df[filtered_df['location'] == 'inventory']
        
        return filtered_df.to_dict('records')
    
    def get_stats(self):
        """Get overall statistics."""
        if self.df.empty:
            return {}
            
        return {
            'total_characters': int(self.df['character'].nunique()),
            'total_items': len(self.df),
            'total_quantity': int(self.df['quantity'].fillna(0).astype(int).sum()),
            'unique_items': int(self.df['item_name'].nunique()),
            'container_items': len(self.df[
                ((self.df['location'].str.startswith('my.')) & 
                 (~self.df['location'].isin(['inventory', 'equipped']))) |
                (self.df['location'].str.startswith('house:'))
            ]),
            'equipment_items': len(self.df[self.df['location'].str.startswith('equipped:')]),
            'inventory_items': len(self.df[self.df['location'] == 'inventory'])
        }

# Initialize viewer
viewer = InventoryViewer()

@app.route('/')
def index():
    """Main character table page."""
    return render_template('character_table.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard page with character details."""
    return render_template('dashboard.html')

@app.route('/old-dashboard')
def old_dashboard():
    """Old dashboard page."""
    stats = viewer.get_stats()
    characters = viewer.get_characters()
    return render_template('index.html', stats=stats, characters=characters)

@app.route('/character/<character_name>')
def character_detail(character_name):
    """Character detail page."""
    char_data = viewer.get_character_data(character_name)
    return render_template('character.html', data=char_data)

@app.route('/debug/<character_name>')
def debug_character(character_name):
    """Debug character data."""
    char_data = viewer.get_character_data(character_name)
    return render_template('debug_template.html', data=char_data)

@app.route('/treasure-vault')
def treasure_vault():
    """Treasure vault page showing all container items."""
    vault_data = viewer.get_treasure_vault()
    
    # Calculate stats for the template
    stats = {
        'total_items': len(vault_data),
        'total_quantity': sum(item['quantity'] for item in vault_data),
        'baskets': len([item for item in vault_data if item['location'] == 'my.basket']),
        'magical': len([item for item in vault_data if '(' in item['item_name']])
    }
    
    return render_template('treasure_vault.html', items=vault_data, stats=stats)

@app.route('/search')
def search():
    """Search page."""
    return render_template('search.html')

@app.route('/api/search')
def api_search():
    """API endpoint for searching items."""
    search_term = request.args.get('q', '')
    location_filter = request.args.get('location', 'all')
    
    results = viewer.search_items(search_term, location_filter)
    return jsonify(results)

@app.route('/api/characters')
def api_characters():
    """API endpoint for getting character list."""
    return jsonify(viewer.get_characters())

@app.route('/api/character/<character_name>')
def api_character(character_name):
    """API endpoint for getting character data."""
    return jsonify(viewer.get_character_data(character_name))

@app.route('/api/house/<owner_name>')
def api_house(owner_name):
    """API endpoint for getting house data for a character."""
    # Try both house naming conventions (case variations)
    house_names = [f"{owner_name}_house", f"{owner_name}_House"]
    
    for house_name in house_names:
        house_data = viewer.get_character_data(house_name)
        if house_data and house_data.get('total_items', 0) > 0:
            house_data['is_house'] = True
            house_data['owner'] = owner_name
            return jsonify(house_data)
    
    return jsonify({'error': 'House not found'}), 404

@app.route('/api/stats')
def api_stats():
    """API endpoint for getting statistics."""
    return jsonify(viewer.get_stats())

@app.route('/api/character-stats')
def api_character_stats():
    """API endpoint for getting character statistics."""
    stats = viewer.get_character_stats()
    
    # Debug logging
    if stats and len(stats) > 0:
        logger.info(f"Returning {len(stats)} character stats")
        logger.info(f"First stat keys: {list(stats[0].keys()) if stats[0] else 'None'}")
        logger.info(f"First stat character: {stats[0].get('character', 'NOT SET') if stats[0] else 'None'}")
    else:
        logger.warning("No character stats to return")
    
    return jsonify(stats)

@app.route('/api/update-role', methods=['POST'])
def update_character_role():
    """API endpoint for updating a character's role."""
    data = request.json
    character = data.get('character')
    role = data.get('role', '')
    
    if not character:
        return jsonify({'error': 'Character name required'}), 400
    
    # Load or create character roles file
    roles_file = 'character_roles.json'
    roles = {}
    
    if os.path.exists(roles_file):
        with open(roles_file, 'r') as f:
            roles = json.load(f)
    
    # Update the role
    roles[character.lower()] = role
    
    # Save the roles file
    with open(roles_file, 'w') as f:
        json.dump(roles, f, indent=2)
    
    return jsonify({'success': True, 'character': character, 'role': role})

@app.route('/api/character-roles')
def get_character_roles():
    """API endpoint for getting all character roles."""
    roles_file = 'character_roles.json'
    if os.path.exists(roles_file):
        with open(roles_file, 'r') as f:
            return jsonify(json.load(f))
    return jsonify({})

@app.route('/api/for-sale-items')
def get_for_sale_items():
    """API endpoint for getting items marked for sale."""
    for_sale_file = 'for_sale_items.json'
    if os.path.exists(for_sale_file):
        with open(for_sale_file, 'r') as f:
            return jsonify(json.load(f))
    return jsonify({})

@app.route('/house-inventory')
def house_inventory():
    """House inventory view."""
    return render_template('house_inventory.html')

@app.route('/api/house-inventory')
def api_house_inventory():
    """API endpoint for getting house inventory only."""
    try:
        house_items = viewer.get_consolidated_inventory()
        # Filter to only house items (location starts with 'house:')
        filtered_items = [
            item for item in house_items 
            if item.get('location', '').startswith('house:')
        ]
        return jsonify(filtered_items)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/for-sale-items', methods=['POST'])
def update_for_sale_items():
    """API endpoint for updating items marked for sale."""
    try:
        data = request.json
        for_sale_file = 'for_sale_items.json'
        
        # Load existing data
        existing_data = {}
        if os.path.exists(for_sale_file):
            with open(for_sale_file, 'r') as f:
                existing_data = json.load(f)
        
        # Update with new data
        item_name = data.get('item_name')
        is_for_sale = data.get('for_sale', False)
        price = data.get('price', '')
        notes = data.get('notes', '')
        
        if not item_name:
            return jsonify({'error': 'item_name required'}), 400
        
        if is_for_sale:
            existing_data[item_name] = {
                'for_sale': True,
                'price': price,
                'notes': notes,
                'timestamp': datetime.now().isoformat()
            }
        else:
            # Remove from for-sale if unchecked
            existing_data.pop(item_name, None)
        
        # Save updated data
        with open(for_sale_file, 'w') as f:
            json.dump(existing_data, f, indent=2)
        
        return jsonify({'success': True, 'item': item_name, 'for_sale': is_for_sale})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scan-info')
def api_scan_info():
    """API endpoint for getting scan information (last scan time, file info)."""
    import glob
    import os
    from datetime import datetime
    
    # Get latest inventory file
    inventory_files = glob.glob("inventory_backup_*.csv")
    stats_files = glob.glob("character_stats_*.csv")
    
    scan_info = {
        'last_inventory_scan': None,
        'last_stats_scan': None,
        'inventory_file': None,
        'stats_file': None
    }
    
    if inventory_files:
        latest_inventory = max(inventory_files, key=os.path.getctime)
        scan_info['inventory_file'] = latest_inventory
        # Parse timestamp from filename like "inventory_backup_20250802_101040.csv"
        try:
            timestamp_str = latest_inventory.split('_')[2] + '_' + latest_inventory.split('_')[3].replace('.csv', '')
            scan_time = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
            scan_info['last_inventory_scan'] = scan_time.isoformat()
        except:
            scan_info['last_inventory_scan'] = datetime.fromtimestamp(os.path.getctime(latest_inventory)).isoformat()
    
    if stats_files:
        latest_stats = max(stats_files, key=os.path.getctime)
        scan_info['stats_file'] = latest_stats
        try:
            timestamp_str = latest_stats.split('_')[2] + '_' + latest_stats.split('_')[3].replace('.csv', '')
            scan_time = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
            scan_info['last_stats_scan'] = scan_time.isoformat()
        except:
            scan_info['last_stats_scan'] = datetime.fromtimestamp(os.path.getctime(latest_stats)).isoformat()
    
    return jsonify(scan_info)

@app.route('/consolidated-inventory')
def consolidated_inventory():
    """Consolidated inventory view page."""
    return render_template('consolidated_inventory.html')

@app.route('/api/consolidated-inventory')
def api_consolidated_inventory():
    """API endpoint for getting all inventory items."""
    return jsonify(viewer.get_consolidated_inventory())

@app.route('/reload')
def reload_data():
    """Reload data from CSV files."""
    viewer.load_latest_data()
    return jsonify({'status': 'success', 'message': 'Data reloaded'})

@app.route('/containers')
def container_management():
    """Container management page."""
    return render_template('container_management.html')

@app.route('/api/containers')
def api_get_containers():
    """API endpoint for getting all container mappings."""
    return jsonify(viewer.container_manager.get_all_mappings())

@app.route('/api/containers/stats')
def api_container_stats():
    """API endpoint for getting container statistics."""
    return jsonify(viewer.container_manager.get_stats())

@app.route('/api/containers', methods=['POST'])
def api_add_container():
    """API endpoint for adding a new container mapping."""
    try:
        data = request.json
        
        # Validate CSRF token
        csrf_token = data.get('csrf_token', '')
        if not validate_csrf_token(csrf_token):
            return jsonify({'error': 'Invalid or missing CSRF token'}), 403
        
        item_name = data.get('item_name', '').strip()
        container_keyword = data.get('container_keyword', '').strip()
        
        if not item_name or not container_keyword:
            return jsonify({'error': 'Both item_name and container_keyword are required'}), 400
        
        success = viewer.container_manager.add_container_mapping(item_name, container_keyword)
        
        if success:
            return jsonify({
                'success': True, 
                'message': f'Added container mapping: "{item_name}" -> {container_keyword}',
                'item_name': item_name,
                'container_keyword': container_keyword
            })
        else:
            return jsonify({'error': 'Failed to add container mapping'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/containers/<path:item_name>', methods=['DELETE'])
def api_delete_container(item_name):
    """API endpoint for deleting a container mapping."""
    try:
        # Validate CSRF token from header
        csrf_token = request.headers.get('X-CSRF-Token', '')
        if not validate_csrf_token(csrf_token):
            return jsonify({'error': 'Invalid or missing CSRF token'}), 403
        success = viewer.container_manager.remove_container_mapping(item_name)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Removed container mapping for "{item_name}"'
            })
        else:
            return jsonify({'error': 'Failed to remove container mapping'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/favicon.ico')
def favicon():
    """Return a simple favicon to prevent 404 errors."""
    return '', 204  # No content response

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    Path('templates').mkdir(exist_ok=True)
    Path('static').mkdir(exist_ok=True)
    
    app.run(debug=True, host='127.0.0.1', port=5000)