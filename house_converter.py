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
                
            # Parse sections
            if line == 'ROOMS IN MY HOUSE:':
                current_section = 'rooms'
                continue
                
            if line == 'HOW TO GET TO EACH ROOM:':
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
        # Format: "1. Room Name (description) - has: container1, container2"
        match = re.match(r'\d+\.\s*(.+?)\s*(?:\([^)]*\))?\s*-\s*has:\s*(.+)', line)
        if match:
            room_name = match.group(1).strip()
            containers_text = match.group(2).strip()
            containers = [c.strip() for c in containers_text.split(',')]
            self.rooms[room_name] = containers
        else:
            # Simple format: "Room Name - has: containers"
            if ' - has:' in line:
                room_name, containers_text = line.split(' - has:', 1)
                room_name = room_name.strip()
                containers = [c.strip() for c in containers_text.split(',')]
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
                
                if path_desc == 'starting room' or 'starting' in path_desc:
                    self.paths[room_name] = 'start'
                else:
                    # Parse "from Room, go direction, then direction"
                    path = self.parse_path_description(path_desc)
                    self.paths[room_name] = path
    
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
            
        # Build the rooms string for CSV
        rooms_data = []
        for room_name, containers in self.rooms.items():
            path = self.paths.get(room_name, 'start')
            containers_str = ';'.join(containers)
            room_data = f"{room_name}:{path}:{containers_str}"
            rooms_data.append(room_data)
        
        rooms_string = '|'.join(rooms_data)
        
        return {
            'character': self.character,  # Use base character name, not _house version
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
        
        # Save to CSV
        csv_data = converter.save_to_csv()
        
        print("SUCCESS: House setup converted successfully!")
        print(f"Character: {csv_data['character']}")
        print(f"House: {csv_data['house_name']}")
        print(f"Rooms: {len(converter.rooms)}")
        print(f"Saved to: houses_v2.csv")
        
        print(f"\nNext steps:")
        print(f"1. Make sure '{csv_data['character']}' is in your characters.csv file")
        print(f"2. Run a scan with --house flag to capture your house inventory!")
        print(f"3. View your house map in the web interface")
        
    except Exception as e:
        print(f"ERROR: Converting house failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()