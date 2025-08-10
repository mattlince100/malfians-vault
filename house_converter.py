#!/usr/bin/env python3
"""
Simple House Converter
Converts user-friendly house descriptions to technical CSV format
"""

import re
import sys
import csv
from pathlib import Path


class HouseConverter:
    """Converts simple house descriptions to technical CSV format."""
    
    def __init__(self):
        self.rooms = {}
        self.paths = {}
        self.character = ""
        self.house_name = ""
        
    def parse_simple_format(self, content):
        """Parse the simple text format into structured data."""
        lines = content.strip().split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            # Parse header information
            if line.startswith('HOUSE SETUP FOR:'):
                self.character = line.split(':', 1)[1].strip()
                continue
                
            if line.startswith('MY HOUSE NAME:'):
                self.house_name = line.split(':', 1)[1].strip()
                continue
                
            # Parse sections - make section detection more flexible
            if 'ROOMS IN MY HOUSE' in line.upper():
                current_section = 'rooms'
                continue
                
            if 'HOW TO GET' in line.upper() or 'HOW TO GEAT' in line.upper():  # Handle typos
                current_section = 'paths'
                continue
                
            # Parse room definitions
            if current_section == 'rooms' and line:
                self.parse_room_line(line)
                
            # Parse path definitions  
            if current_section == 'paths' and line:
                self.parse_path_line(line)
    
    def parse_room_line(self, line):
        """Parse a room definition line."""
        # Skip empty lines
        if not line.strip():
            return
            
        # Try multiple formats to be more flexible
        # Format 1: "1. Room Name (description) - has: container1, container2"
        # Format 2: "1. Room Name (description) - has container1, container2"  
        # Format 3: "1. Room Name - has: container1, container2"
        
        # Look for "has" keyword with containers after it
        if ' has' in line.lower():
            # Split on " - has" or just "has"
            if ' - has' in line.lower():
                parts = line.split(' - has', 1)
            elif '-has' in line.lower():
                parts = line.split('-has', 1) 
            elif ' has ' in line.lower():
                parts = line.split(' has ', 1)
            else:
                return
                
            if len(parts) == 2:
                # Extract room name from first part
                room_part = parts[0].strip()
                containers_part = parts[1].strip()
                
                # Remove leading number if present (e.g., "1. ")
                room_part = re.sub(r'^\d+\.\s*', '', room_part)
                
                # Remove parenthetical descriptions
                room_name = re.sub(r'\s*\([^)]*\)\s*', ' ', room_part).strip()
                
                # Remove colon from containers part if present
                containers_part = containers_part.lstrip(':').strip()
                
                # Split containers
                containers = [c.strip() for c in containers_part.split(',')]
                
                # Store the room
                self.rooms[room_name] = containers
    
    def parse_path_line(self, line):
        """Parse a path definition line."""
        # Format: "- Room Name: from Another Room, go direction, then direction"
        if line.startswith('- '):
            line = line[2:]  # Remove "- "
            if ':' in line:
                room_name, path_desc = line.split(':', 1)
                room_name = room_name.strip()
                path_desc = path_desc.strip()
                
                # Try to match this room name with existing parsed rooms (fuzzy matching for typos)
                matched_room = self.find_matching_room(room_name)
                if matched_room:
                    room_name = matched_room  # Use the canonical room name
                
                if path_desc == 'starting room' or 'starting' in path_desc:
                    self.paths[room_name] = 'start'
                else:
                    # Parse "from Room, go direction, then direction"
                    path = self.parse_path_description(path_desc)
                    self.paths[room_name] = path
    
    def find_matching_room(self, room_name):
        """Find a matching room name accounting for typos and variations."""
        room_lower = room_name.lower().strip()
        
        # Exact match first
        for existing_room in self.rooms.keys():
            if existing_room.lower() == room_lower:
                return existing_room
        
        # Partial match - if one contains the other
        for existing_room in self.rooms.keys():
            existing_lower = existing_room.lower()
            # Check if they're very similar (one typo difference)
            if self.similar_strings(existing_lower, room_lower):
                return existing_room
                
        return room_name  # Return original if no match found
    
    def similar_strings(self, s1, s2):
        """Check if two strings are similar (allowing for small typos)."""
        # Simple similarity check - could be enhanced
        if abs(len(s1) - len(s2)) > 2:
            return False
            
        # Check if most words match
        words1 = set(s1.split())
        words2 = set(s2.split())
        
        if not words1 or not words2:
            return False
            
        common = words1.intersection(words2)
        total = max(len(words1), len(words2))
        
        # If 70% or more words match, consider them similar
        return len(common) >= total * 0.7
    
    def parse_path_description(self, desc):
        """Convert natural language path to technical format."""
        # Clean up the description
        desc = desc.lower().replace(',', ' ').replace('  ', ' ')
        
        # Extract directions
        directions = []
        direction_words = ['north', 'south', 'east', 'west', 'up', 'down',
                          'northeast', 'northwest', 'southeast', 'southwest',
                          'n', 's', 'e', 'w', 'u', 'd', 'ne', 'nw', 'se', 'sw']
        
        words = desc.split()
        for i, word in enumerate(words):
            if word in direction_words:
                # Map full words to abbreviations
                direction_map = {
                    'north': 'n', 'south': 's', 'east': 'e', 'west': 'w',
                    'up': 'u', 'down': 'd', 'northeast': 'ne', 'northwest': 'nw',
                    'southeast': 'se', 'southwest': 'sw'
                }
                direction = direction_map.get(word, word)
                directions.append(direction)
        
        return ';'.join(directions) if directions else 'start'
    
    def convert_to_csv_format(self):
        """Convert parsed data to CSV format."""
        if not self.character or not self.house_name:
            raise ValueError("Missing character name or house name")
            
        # Build the rooms string for CSV - fix case sensitivity and ensure all rooms are included
        rooms_data = []
        for room_name, containers in self.rooms.items():
            path = self.paths.get(room_name, 'start')
            containers_str = ';'.join(containers)
            room_data = f"{room_name}:{path}:{containers_str}"
            rooms_data.append(room_data)
        
        rooms_string = '|'.join(rooms_data)
        
        return {
            'character': self.character.lower(),  # Convert to lowercase for consistency
            'house_name': self.house_name,  
            'rooms': rooms_string
        }
    
    def save_to_csv(self, output_file='houses_v2.csv'):
        """Save the converted data to CSV file."""
        csv_data = self.convert_to_csv_format()
        
        # Check if file exists to determine if we need headers
        file_exists = Path(output_file).exists()
        
        with open(output_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['character', 'house_name', 'rooms'])
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerow(csv_data)
        
        return csv_data


def main():
    """Main conversion function."""
    if len(sys.argv) != 2:
        print("Usage: python house_converter.py <input_file.txt>")
        print("\nExample:")
        print("  python house_converter.py my_house.txt")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    if not Path(input_file).exists():
        print(f"Error: File '{input_file}' not found!")
        sys.exit(1)
    
    try:
        # Read the input file
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Convert the format
        converter = HouseConverter()
        converter.parse_simple_format(content)
        
        # Debug output - show what was parsed
        print(f"\nDEBUG - Parsed Rooms:")
        for room, containers in converter.rooms.items():
            print(f"  - {room}: {containers}")
        
        print(f"\nDEBUG - Parsed Paths:")
        for room, path in converter.paths.items():
            print(f"  - {room}: {path}")
        
        # Save to CSV
        csv_data = converter.save_to_csv()
        
        print("\nSUCCESS: House setup converted successfully!")
        print(f"Character: {csv_data['character']}")
        print(f"House: {csv_data['house_name']}")
        print(f"Rooms: {len(converter.rooms)}")
        print(f"Saved to: houses_v2.csv")
        
        print(f"\nCSV Output:")
        print(f"  Rooms string: {csv_data['rooms']}")
        
        print(f"\nNext steps:")
        print(f"1. Make sure '{csv_data['character']}' is in your characters.csv file")
        print(f"2. Run a scan with --house flag to capture your house inventory!")
        print(f"3. View your house map in the web interface")
        
    except Exception as e:
        print(f"ERROR: Converting house failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()