"""Enhanced house configuration manager supporting multi-room houses."""

import csv
import logging
from typing import List, Dict, Optional
from pathlib import Path
from config import HOUSES_FILE

logger = logging.getLogger(__name__)


class HouseManagerV2:
    """Manages house configurations with multi-room support."""
    
    def __init__(self):
        self.houses = {}
        self.load_houses()
    
    def load_houses(self) -> bool:
        """Load house configurations from CSV file."""
        if not Path(HOUSES_FILE).exists():
            logger.info(f"No houses file found at {HOUSES_FILE}")
            return False
        
        try:
            with open(HOUSES_FILE, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    character = row['character'].strip()
                    
                    # Check if this is the new format (with 'rooms' column) or old format
                    if 'rooms' in row:
                        # New multi-room format
                        house_config = {
                            'house_name': row.get('house_name', f"{character}'s House").strip(),
                            'rooms': row['rooms'].strip(),
                            'format': 'v2'
                        }
                    else:
                        # Old format - convert to new format
                        house_config = self._convert_old_format(row)
                    
                    self.houses[character] = house_config
                    logger.debug(f"Loaded house config for {character}: {house_config['house_name']}")
            
            logger.info(f"Loaded {len(self.houses)} house configurations")
            return True
            
        except Exception as e:
            logger.error(f"Error loading houses: {str(e)}")
            return False
    
    def _convert_old_format(self, row: Dict) -> Dict:
        """Convert old house format to new multi-room format."""
        character = row['character'].strip()
        house_name = row.get('house_name', f"{character}'s House").strip()
        containers = row.get('containers', '').strip()
        
        # Create a single room configuration from old format
        # Old format doesn't use secthome, so we'll mark it as requiring manual navigation
        rooms_config = f"Main Room:start:{containers}"
        
        return {
            'house_name': house_name,
            'rooms': rooms_config,
            'format': 'v1-converted',
            # Store old navigation paths for reference
            'old_path_to_house': row.get('path_to_house', ''),
            'old_storage_room_path': row.get('storage_room_path', '')
        }
    
    def get_house_config(self, character: str) -> Optional[Dict]:
        """Get house configuration for a specific character."""
        return self.houses.get(character)
    
    def has_house(self, character: str) -> bool:
        """Check if a character has a house configured."""
        return character in self.houses
    
    def get_all_house_owners(self) -> List[str]:
        """Get list of all characters that have houses."""
        return list(self.houses.keys())
    
    def parse_rooms(self, rooms_str: str) -> List[Dict]:
        """Parse room configuration string into structured format.
        
        Format: "RoomName:path:container1,container2|RoomName2:path2:container3,container4"
        Can use | or ; as room separator (| preferred when paths contain ;)
        """
        rooms = []
        
        if not rooms_str.strip():
            return rooms
        
        # Check which separator is used
        if '|' in rooms_str:
            # New format with pipe separator
            room_entries = [r.strip() for r in rooms_str.split('|') if r.strip()]
        else:
            # Old format with semicolon separator
            room_entries = [r.strip() for r in rooms_str.split(';') if r.strip()]
        
        for entry in room_entries:
            parts = entry.split(':')
            if len(parts) >= 3:
                room_name = parts[0].strip()
                room_path = parts[1].strip()
                containers_str = ':'.join(parts[2:]).strip()  # Rejoin in case container names have colons
                containers = [c.strip() for c in containers_str.split(',') if c.strip()]
                
                rooms.append({
                    'name': room_name,
                    'path': room_path if room_path != 'start' else '',
                    'containers': containers
                })
        
        return rooms
    
    def get_house_summary(self) -> Dict:
        """Get summary statistics about configured houses."""
        total_houses = len(self.houses)
        total_rooms = 0
        total_containers = 0
        
        for config in self.houses.values():
            rooms = self.parse_rooms(config.get('rooms', ''))
            total_rooms += len(rooms)
            
            for room in rooms:
                total_containers += len(room.get('containers', []))
        
        return {
            'total_houses': total_houses,
            'total_rooms': total_rooms,
            'total_containers': total_containers,
            'average_rooms_per_house': total_rooms / total_houses if total_houses > 0 else 0,
            'average_containers_per_house': total_containers / total_houses if total_houses > 0 else 0
        }
    
    def validate_house_config(self, config: Dict) -> List[str]:
        """Validate a house configuration and return any errors."""
        errors = []
        
        if not config.get('house_name', '').strip():
            errors.append("House name is required")
        
        rooms_str = config.get('rooms', '').strip()
        if not rooms_str:
            errors.append("At least one room must be configured")
        else:
            rooms = self.parse_rooms(rooms_str)
            if not rooms:
                errors.append("Invalid room configuration format")
            else:
                for i, room in enumerate(rooms):
                    if not room.get('name'):
                        errors.append(f"Room {i+1} is missing a name")
                    if not room.get('containers'):
                        errors.append(f"Room '{room.get('name', i+1)}' has no containers")
        
        return errors
    
    def add_house_config(self, character: str, house_name: str, rooms: str) -> bool:
        """Add a new house configuration."""
        try:
            house_config = {
                'house_name': house_name.strip(),
                'rooms': rooms.strip(),
                'format': 'v2'
            }
            
            # Validate before adding
            errors = self.validate_house_config(house_config)
            if errors:
                logger.error(f"Invalid house configuration: {errors}")
                return False
            
            self.houses[character] = house_config
            
            # Save to file
            self.save_houses()
            
            logger.info(f"Added house config for {character}: {house_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding house config: {str(e)}")
            return False
    
    def save_houses(self) -> bool:
        """Save house configurations to CSV file."""
        try:
            with open(HOUSES_FILE, 'w', newline='') as f:
                fieldnames = ['character', 'house_name', 'rooms']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for character, config in self.houses.items():
                    # Only save in new format
                    row = {
                        'character': character,
                        'house_name': config.get('house_name', f"{character}'s House"),
                        'rooms': config.get('rooms', '')
                    }
                    writer.writerow(row)
            
            logger.info(f"Saved {len(self.houses)} house configurations")
            return True
            
        except Exception as e:
            logger.error(f"Error saving houses: {str(e)}")
            return False