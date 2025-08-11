"""Enhanced house inventory scanner for scanning multiple rooms in MUD houses."""

import re
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from config import HOUSE_MOVEMENT_DELAY, HOUSE_EXAMINE_DELAY

logger = logging.getLogger(__name__)


class HouseScannerV2:
    """Scans and parses house inventory from multiple rooms."""
    
    def __init__(self, mud_client):
        self.mud_client = mud_client
        self.current_character = ""
        self.current_house_name = ""
        
    async def scan_house_inventory(self, character_name: str, house_config: Dict) -> Tuple[List[Dict], Dict]:
        """Perform a complete house inventory scan across multiple rooms."""
        import time
        start_time = time.time()
        self.current_character = character_name
        self.current_house_name = house_config.get('house_name', f"{character_name}'s House")
        all_items = []
        
        logger.info(f"Starting house inventory scan for {character_name}'s {self.current_house_name}")
        
        try:
            # Use secthome to go directly to the house
            logger.info("Using secthome to navigate to house")
            response = await self.mud_client.send_command("secthome", delay=HOUSE_MOVEMENT_DELAY)
            
            # Check if secthome worked
            if "you don't have a home" in response.lower() or "you can't" in response.lower():
                logger.error(f"Failed to use secthome for {character_name}")
                return [], {}
            
            # Parse room configurations
            rooms = self._parse_room_config(house_config.get('rooms', ''))
            
            # Scan each room
            for room_config in rooms:
                room_name = room_config.get('name', 'Unknown Room')
                room_path = room_config.get('path', '')
                containers = room_config.get('containers', [])
                
                logger.info(f"Scanning room: {room_name}")
                
                # Navigate to room if needed
                if room_path:
                    if not await self._navigate_to_room(room_path):
                        logger.error(f"Failed to navigate to room: {room_name}")
                        continue
                
                # Scan containers in this room
                logger.info(f"Found {len(containers)} containers to scan in room '{room_name}': {containers}")
                for container in containers:
                    if container:  # Skip empty container names
                        logger.info(f"Scanning container '{container}' in room '{room_name}'")
                        items = await self.scan_house_container(container, room_name)
                        logger.info(f"Container '{container}' returned {len(items)} items")
                        all_items.extend(items)
                        
                        # Check for scan pause/cancel
                        await self._check_scan_state()
                    else:
                        logger.warning(f"Skipping empty container name in room '{room_name}'")
                
                # Return to starting point if we moved
                if room_path and room_path != "start":
                    # Go back to secthome start point
                    await self.mud_client.send_command("secthome", delay=HOUSE_MOVEMENT_DELAY)
            
            # Create house "character" stats - ensure all fields match regular character stats
            house_stats = {
                'character': f"{character_name}_House",
                'house_name': self.current_house_name,
                'owner': character_name,
                'class': 'House Storage',
                'race': 'Property',
                'gender': 'Neutral',
                'alignment': 'Neutral',
                'gold': '0',
                'level': 'N/A',
                'hitpoints': 'N/A',
                'damroll': 'N/A',
                'hitroll': 'N/A',
                'deity': 'N/A',
                'glory': '0',
                'org': 'N/A',
                'role': 'Storage',
                'needs': '-',
                'age': 'N/A',
                'bio_status': 'House Storage',
                'honour': 'N/A',
                'rank': 'N/A',
                'guild': 'N/A',
                'guild_role': 'N/A',
                'sect': 'N/A',
                'sect_role': 'N/A',
                'order': 'N/A',
                'order_role': 'N/A',
                'raw_score': f"House Storage for {character_name}"  # Add missing field to prevent CSV corruption
            }
            
            scan_time = time.time() - start_time
            logger.info(f"House scan complete for {character_name}: {len(all_items)} items found in {scan_time:.1f}s")
            
            # Debug logging
            if all_items:
                logger.info(f"First house item character name: {all_items[0].get('character', 'NOT SET')}")
                logger.info(f"House stats character name: {house_stats.get('character', 'NOT SET')}")
            
            return all_items, house_stats
            
        except Exception as e:
            logger.error(f"Error during house scan for {character_name}: {str(e)}")
            return [], {}
    
    def _parse_room_config(self, rooms_str: str) -> List[Dict]:
        """Parse room configuration string into structured format.
        
        Format: "RoomName:path:container1;container2|RoomName2:path2:container3;container4"
        Uses | as room separator and ; as container separator
        Special paths:
        - "start" or empty = starting room (where secthome takes you)
        - "u" = up, "d" = down, "n" = north, etc.
        - "u;n;e" = up, then north, then east (paths also use ;)
        """
        rooms = []
        
        if not rooms_str.strip():
            # Default single room configuration
            return [{
                'name': 'Main Room',
                'path': '',
                'containers': []
            }]
        
        # First check if using new format with | separator
        if '|' in rooms_str:
            room_entries = [r.strip() for r in rooms_str.split('|') if r.strip()]
        else:
            # Fall back to trying to parse with careful semicolon splitting
            # This is complex because paths can contain semicolons
            room_entries = []
            current_entry = []
            parts = rooms_str.split(':')
            
            i = 0
            while i < len(parts):
                if i + 2 < len(parts):
                    # We have at least 3 parts, could be a complete room
                    room_name = parts[i]
                    path = parts[i + 1]
                    containers = parts[i + 2]
                    
                    # Check if containers part contains another room start
                    # (it would have a : before the end)
                    next_room_pos = containers.find(';')
                    if next_room_pos > 0 and i + 3 < len(parts):
                        # There's another room definition
                        actual_containers = containers[:next_room_pos]
                        room_entries.append(f"{room_name}:{path}:{actual_containers}")
                        
                        # Continue with the rest
                        remaining = containers[next_room_pos + 1:] + ':' + ':'.join(parts[i + 3:])
                        parts = remaining.split(':')
                        i = 0
                    else:
                        # This is the last room
                        room_entries.append(f"{room_name}:{path}:{containers}")
                        break
                else:
                    break
        
        for entry in room_entries:
            parts = entry.split(':')
            if len(parts) >= 3:
                room_name = parts[0].strip()
                room_path = parts[1].strip()
                containers_str = ':'.join(parts[2:]).strip()  # Rejoin in case container names have colons
                containers = [c.strip() for c in containers_str.split(';') if c.strip()]
                
                rooms.append({
                    'name': room_name,
                    'path': room_path if room_path != 'start' else '',
                    'containers': containers
                })
        
        return rooms
    
    async def _navigate_to_room(self, room_path: str) -> bool:
        """Navigate to a specific room within the house."""
        if not room_path or room_path == 'start':
            return True
        
        commands = [cmd.strip() for cmd in room_path.split(';') if cmd.strip()]
        logger.debug(f"Navigating to room with {len(commands)} commands: {commands}")
        
        for i, command in enumerate(commands):
            logger.debug(f"Room nav step {i+1}: {command}")
            response = await self.mud_client.send_command(command, delay=HOUSE_MOVEMENT_DELAY)
            
            # Check for navigation failures
            if any(failure in response.lower() for failure in [
                "you can't go that way", "the door is locked", "you can't see that here",
                "what", "there is no", "you don't see"
            ]):
                logger.error(f"Room navigation failed at step {i+1} '{command}': {response[:100]}")
                return False
            
            await self._check_scan_state()
        
        return True
    
    async def scan_house_container(self, container_name: str, room_name: str = "Unknown") -> List[Dict]:
        """Scan a specific container in the house."""
        logger.info(f"Attempting to scan house container '{container_name}' in room '{room_name}'")
        
        # First, try to see if the container is visible in the room
        look_response = await self.mud_client.send_command("look", delay=HOUSE_EXAMINE_DELAY)
        logger.info(f"Look response length: {len(look_response)} chars")
        
        # Then examine the container
        exam_command = f"exam {container_name}"
        logger.info(f"Running command: {exam_command}")
        response = await self.mud_client.send_command(exam_command, delay=HOUSE_EXAMINE_DELAY)
        logger.info(f"Exam response length: {len(response)} chars")
        
        # Log the first 200 chars of the response for debugging
        logger.info(f"Exam response preview: {response[:200]}...")
        
        # Check if container exists and has contents
        error_messages = [
            "you do not see that here", "you do not see", "what do you want to", "there is no"
        ]
        found_error = None
        for error in error_messages:
            if error in response.lower():
                found_error = error
                break
                
        if found_error:
            logger.info(f"Container '{container_name}' not found in room '{room_name}' - found error: '{found_error}'")
            return []
        
        if "appears to be empty" in response.lower():
            logger.info(f"Container '{container_name}' in room '{room_name}' is empty")
            return []
        
        return self.parse_house_container_output(response, container_name, room_name)
    
    def parse_house_container_output(self, response: str, container_name: str, room_name: str) -> List[Dict]:
        """Parse house container examination output."""
        items = []
        lines = response.split('\n')
        
        # Look for the "contains:" section
        in_contents = False
        for line in lines:
            # Keep original line for parsing but check stripped version
            original_line = line
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Enhanced prompt detection - strip ANSI codes first
            import re
            clean_line = re.sub(r'\x1b\[[0-9;]*m', '', line)
            clean_line = re.sub(r'\\x1b\[[0-9;]*m', '', clean_line)
            
            # Skip character status prompts (e.g., "[Kaan] 1674/1674hp 461mn HY")
            # More comprehensive check for prompts
            if clean_line.startswith('['):
                # Check for health/mana indicators
                if ('hp' in clean_line.lower() or 'mn' in clean_line.lower() or 
                    '/' in clean_line):  # HP format like 1674/1674
                    continue
                # Check for status flags
                if any(flag in clean_line for flag in ['HTY', 'HSY', 'HY', 'TY', 'SY']):
                    continue
            
            # Skip lines that are purely ANSI codes or whitespace after cleaning
            if not clean_line.strip() or re.match(r'^[\s\x1b\[\]0-9;m\\]*$', clean_line):
                continue
                
            # Look for container contents section
            if "contains:" in line.lower():
                in_contents = True
                continue
                
            # Stop at next prompt or new command
            if (clean_line.endswith('HTY\\') or 
                clean_line.endswith('>') or 
                clean_line.endswith('HTY') or
                clean_line.endswith('HSY') or
                clean_line.endswith('HY')):
                break
                
            # Parse items if we're in contents section
            if in_contents and line:
                item = self.parse_house_item_line(original_line, f"house:{room_name}:{container_name}")
                if item:
                    items.append(item)
                    
        return items
    
    def parse_house_item_line(self, line: str, location: str) -> Optional[Dict]:
        """Parse a single item line from house containers."""
        if not line or line.lower() in ['nothing', 'none', 'empty']:
            return None
        
        # Enhanced prompt detection - strip ANSI codes first
        import re
        clean_line = re.sub(r'\x1b\[[0-9;]*m', '', line)
        clean_line = re.sub(r'\\x1b\[[0-9;]*m', '', clean_line).strip()
        
        # Skip if this looks like a character prompt
        # Format: [CharacterName] XXX/XXXhp XXXmn (flags) 
        if (clean_line.startswith('[') and 
            ('/' in clean_line) and 
            ('hp' in clean_line.lower() or 'mn' in clean_line.lower())):
            logger.debug(f"Skipping prompt line in house container: {clean_line[:50]}")
            return None
        
        # Also skip if line ends with combat/status flags
        if any(clean_line.endswith(flag) for flag in ['HTY', 'HSY', 'HY', 'TY', 'SY', 'HTY\\', 'HSY\\', 'HY\\']):
            logger.debug(f"Skipping status flag line in house container: {clean_line[:50]}")
            return None
        
        # Skip lines that are purely ANSI codes or whitespace after cleaning
        if not clean_line or re.match(r'^[\s\x1b\[\]0-9;m\\]*$', clean_line):
            logger.debug(f"Skipping ANSI/empty line in house container: {repr(line[:50])}")
            return None
            
        # Extract quantity if present - look for patterns like "(2)" or "(15)" at the end
        quantity = "1"
        item_name = line
        
        # Check for quantity in parentheses at the end
        quantity_match = re.search(r'\((\d+)\)\s*$', line)
        if quantity_match:
            quantity = quantity_match.group(1)
            item_name = line[:quantity_match.start()].strip()
        
        # Clean up item name - remove extra articles and modifiers but keep magical properties
        item_name = self.clean_house_item_name(item_name)
        
        if not item_name:
            return None
            
        return {
            'character': f"{self.current_character}_House",
            'location': location,
            'item_name': item_name,
            'quantity': quantity,
            'scan_time': datetime.now().isoformat(),
            'raw_line': line,
            'house_owner': self.current_character,
            'house_name': self.current_house_name
        }
    
    def clean_house_item_name(self, name: str) -> str:
        """Clean and normalize house item name."""
        import re
        
        # Strip ANSI escape codes that are causing corruption
        # These are appearing in character names and corrupting the display
        name = re.sub(r'\x1b\[[0-9;]*m', '', name)
        name = re.sub(r'\\x1b\[[0-9;]*m', '', name)
        
        # Strip whitespace
        name = name.strip()
        
        # Remove leading articles if they're at the very beginning
        if name.lower().startswith('a '):
            name = name[2:]
        elif name.lower().startswith('an '):
            name = name[3:]
        elif name.lower().startswith('the '):
            name = name[4:]
            
        return name.strip()
    
    async def _check_scan_state(self):
        """Check if scan is paused or cancelled."""
        try:
            # Import here to avoid circular import
            import main
            
            # Handle pause
            while main.scan_paused and not main.scan_cancelled:
                await asyncio.sleep(0.5)
                
            # Check for cancellation
            if main.scan_cancelled:
                logger.info("House scan cancelled during processing")
                raise KeyboardInterrupt("House scan cancelled by user")
        except (ImportError, AttributeError):
            # main module not available or scan controls not set up
            pass