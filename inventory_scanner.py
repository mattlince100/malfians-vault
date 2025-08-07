"""Inventory scanner for parsing MUD inventory data."""

import re
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from config import EQUIPMENT_COMMAND, INVENTORY_COMMAND, ITEM_PATTERNS
from container_manager import ContainerManager

logger = logging.getLogger(__name__)


class InventoryScanner:
    """Scans and parses character inventory from MUD responses."""
    
    def __init__(self, mud_client):
        self.mud_client = mud_client
        self.current_character = ""
        self.container_manager = ContainerManager()
        self.detected_containers = []
        self.unknown_containers = []
        
    async def scan_character_inventory(self, character_name: str) -> Tuple[List[Dict], Dict]:
        """Perform a complete inventory scan for a character."""
        import time
        start_time = time.time()
        self.current_character = character_name
        all_items = []
        
        logger.info(f"Starting inventory scan for {character_name}")
        
        # Get character stats immediately after login
        step_start = time.time()
        char_stats = await self.scan_character_stats()
        logger.info(f"Character stats scan took {time.time() - step_start:.2f}s")
        
        # Check for scan pause/cancel (import here to avoid circular import)
        await self._check_scan_state()
        
        # Get whois data immediately
        step_start = time.time()
        whois_data = await self.scan_whois_data()
        logger.info(f"Whois scan took {time.time() - step_start:.2f}s")
        
        # Merge whois data into char_stats
        char_stats.update(whois_data)
        
        await self._check_scan_state()
        
        # Scan carried inventory immediately
        step_start = time.time()
        items = await self.scan_inventory()
        all_items.extend(items)
        logger.info(f"Inventory scan took {time.time() - step_start:.2f}s")
        
        await self._check_scan_state()
        
        # Smart container detection - find containers in inventory
        step_start = time.time()
        inventory_items = [item for item in all_items if item.get('location') == 'inventory']
        self.detected_containers, self.unknown_containers = self.container_manager.detect_containers_in_inventory(inventory_items)
        
        # Log unknown potential containers for review
        if self.unknown_containers:
            logger.info(f"Unknown potential containers found for {character_name}: {self.unknown_containers}")
        
        # Scan each detected container
        for container_keyword in self.detected_containers:
            container_start = time.time()
            items = await self.scan_container(container_keyword)
            all_items.extend(items)
            logger.info(f"Smart container {container_keyword} scan took {time.time() - container_start:.2f}s")
            await self._check_scan_state()
            
        logger.info(f"Smart container detection took {time.time() - step_start:.2f}s")
            
        # Scan equipped items immediately
        step_start = time.time()
        items = await self.scan_equipment()
        all_items.extend(items)
        logger.info(f"Equipment scan took {time.time() - step_start:.2f}s")
        
        # Update needs field based on empty equipment slots
        char_stats['needs'] = self.generate_needs_list()
        
        # Check if this character has a house to scan
        house_items, house_stats = await self.scan_character_house(character_name)
        if house_items:
            logger.info(f"Found house storage for {character_name}: {len(house_items)} items")
            # House items and stats will be handled separately by the data manager
        
        # Save and quit immediately
        step_start = time.time()
        await self.mud_client.send_command("save")
        await self.mud_client.send_command("quit")
        logger.info(f"Save/quit took {time.time() - step_start:.2f}s")
        
        total_time = time.time() - start_time
        logger.info(f"Scan complete for {character_name}: {len(all_items)} items found in {total_time:.2f}s")
        
        # Return both character data and house data if available
        result = [(all_items, char_stats)]
        if house_items:
            result.append((house_items, house_stats))
        
        return result if len(result) > 1 else (all_items, char_stats)
    
    async def scan_character_house(self, character_name: str) -> Tuple[List[Dict], Dict]:
        """Scan a character's house if they have one configured."""
        try:
            # Try v2 first (multi-room support)
            try:
                from house_manager_v2 import HouseManagerV2
                from house_scanner_v2 import HouseScannerV2
                
                house_manager = HouseManagerV2()
                
                if not house_manager.has_house(character_name):
                    logger.debug(f"No house configured for {character_name}")
                    return [], {}
                
                house_config = house_manager.get_house_config(character_name)
                if not house_config:
                    logger.debug(f"Invalid house config for {character_name}")
                    return [], {}
                
                # Create house scanner and scan the house
                house_scanner = HouseScannerV2(self.mud_client)
                house_items, house_stats = await house_scanner.scan_house_inventory(character_name, house_config)
                
                return house_items, house_stats
                
            except ImportError:
                # Fall back to v1 (single room support)
                from house_manager import HouseManager
                from house_scanner import HouseScanner
                
                house_manager = HouseManager()
                
                if not house_manager.has_house(character_name):
                    logger.debug(f"No house configured for {character_name}")
                    return [], {}
                
                house_config = house_manager.get_house_config(character_name)
                if not house_config:
                    logger.debug(f"Invalid house config for {character_name}")
                    return [], {}
                
                # Create house scanner and scan the house
                house_scanner = HouseScanner(self.mud_client)
                house_items, house_stats = await house_scanner.scan_house_inventory(character_name, house_config)
                
                return house_items, house_stats
            
        except ImportError:
            logger.debug("House scanning modules not available")
            return [], {}
        except Exception as e:
            logger.error(f"Error scanning house for {character_name}: {str(e)}")
            return [], {}
    
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
                logger.info("Scan cancelled during character processing")
                raise KeyboardInterrupt("Scan cancelled by user")
        except (ImportError, AttributeError):
            # main module not available or scan controls not set up
            pass
    
    async def scan_character_stats(self) -> Dict:
        """Scan character statistics (class, race, gender, alignment, gold)."""
        logger.debug("Scanning character statistics")
        
        # Use 'score' command to get character stats (no additional delay - handled by caller)
        response = await self.mud_client.send_command("score")
        logger.debug(f"Score response: {response[:500]}...")
        
        return self.parse_character_stats(response)
    
    async def scan_whois_data(self) -> Dict:
        """Scan whois data for additional character information."""
        logger.debug("Scanning whois data")
        
        # Use 'whois' command with character name
        response = await self.mud_client.send_command(f"whois {self.current_character}")
        logger.debug(f"Whois response: {response[:500]}...")
        
        return self.parse_whois_data(response)
    
    def parse_whois_data(self, whois_response: str) -> Dict:
        """Parse whois response for additional character data."""
        whois_data = {
            'age': '-',
            'bio_status': '-',
            'honour': '-',
            'rank': '-',
            'guild': '-',
            'guild_role': '-',
            'sect': '-',
            'sect_role': '-',
            'order': '-',
            'order_role': '-'
        }
        
        lines = whois_response.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for age and gender: "He is a male level 50 Half-orc Warrior 262 years of age."
            # or "She is a female level 45 Elf Mage 180 years of age."
            # or "It is a level 30 Golem Warrior 50 years of age." (for neutral)
            if 'years of age' in line:
                age_match = re.search(r'(\d+)\s+years of age', line)
                if age_match:
                    whois_data['age'] = age_match.group(1)
                
                # Extract gender from the same line
                line_lower = line.lower()
                if 'he is a male' in line_lower:
                    whois_data['gender'] = 'Male'
                elif 'she is a female' in line_lower:
                    whois_data['gender'] = 'Female'
                elif 'it is a' in line_lower and 'level' in line_lower:
                    whois_data['gender'] = 'Neutral'
                    
            # Look for honor and rank: "Malfian has 10 honour and he holds the rank of: Soothsayer"
            if 'honour' in line and 'rank' in line:
                honour_match = re.search(r'has\s+(\d+)\s+honour', line)
                if honour_match:
                    whois_data['honour'] = honour_match.group(1)
                    
                rank_match = re.search(r'rank of:\s*([^\n]+)', line)
                if rank_match:
                    whois_data['rank'] = rank_match.group(1).strip()
                    
            # Parse organizational memberships - can be complex with multiple orgs in one line
            # Example: "is the Leader of the sect: Seraphim, and belongs to the Guild of Origin"
            # Example: "belongs to the Order of Ascendere"
            
            # Look for Guild membership
            if 'Guild of' in line:
                guild_match = re.search(r'Guild of\s+([^.,\n]+)', line)
                if guild_match:
                    whois_data['guild'] = guild_match.group(1).strip()
                    # Check if they're a leader of the guild (rare but possible)
                    if 'Leader of' in line and 'Guild' in line:
                        whois_data['guild_role'] = 'Leader'
                    else:
                        whois_data['guild_role'] = 'Member'
                    
            # Look for Sect membership and role
            if 'sect:' in line:
                sect_match = re.search(r'sect:\s*([^,.\n]+)', line)
                if sect_match:
                    whois_data['sect'] = sect_match.group(1).strip()
                    
                # Check sect role
                if 'Leader of the sect:' in line:
                    whois_data['sect_role'] = 'Leader'
                elif 'Second of the sect:' in line:
                    whois_data['sect_role'] = 'Second'  
                else:
                    whois_data['sect_role'] = 'Member'
                        
            # Look for Order membership and role
            if 'Order of' in line:
                order_match = re.search(r'Order of\s+([^.,\n]+)', line)
                if order_match:
                    whois_data['order'] = order_match.group(1).strip()
                    
                # Check order role
                if 'Leader of the Order of' in line:
                    whois_data['order_role'] = 'Leader'
                elif 'Second of the Order of' in line:
                    whois_data['order_role'] = 'Second'
                elif 'belongs to the Order of' in line:
                    whois_data['order_role'] = 'Member'
                    
            # Look for bio status: "has yet to create a bio" or bio exists
            if 'has yet to create a bio' in line:
                whois_data['bio_status'] = 'No bio'
            elif 'bio:' in line.lower():
                whois_data['bio_status'] = 'Has bio'
                
        return whois_data
    
    def parse_character_stats(self, score_response: str) -> Dict:
        """Parse character statistics from detailed score response."""
        stats = {
            'character': self.current_character,
            'class': 'Unknown',
            'race': 'Unknown', 
            'gender': 'Unknown',
            'alignment': 'Unknown',
            'gold': '0',
            'level': 'Unknown',
            'hitpoints': '-',
            'damroll': '-',
            'hitroll': '-',
            'deity': '-',
            'glory': '0',
            'org': '-',
            'role': '-',
            'needs': '-',
            'age': '-',
            'bio_status': '-',
            'honour': '-',
            'rank': '-',
            'guild': '-',
            'guild_role': '-',
            'sect': '-',
            'sect_role': '-',
            'order': '-',
            'order_role': '-',
            'raw_score': score_response  # Save the raw score output
        }
        
        # Parse score response for the detailed MUD format
        lines = score_response.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for "Score for [Name]" line
            if line.startswith('Score for'):
                # Extract character name from "Score for Kroc, River's Rage."
                parts = line.split(',')
                if len(parts) > 0:
                    name_part = parts[0].replace('Score for', '').strip()
                    if name_part:
                        # Use the consistent character name from self.current_character instead
                        # This ensures we use the login name, not the full character title
                        stats['character'] = self.current_character
                        
            # Look for LEVEL and Race line: "LEVEL: 50          Race : Half-orc"
            if line.startswith('LEVEL:') and 'Race' in line:
                # Extract level
                level_match = re.search(r'LEVEL:\s*(\d+)', line)
                if level_match:
                    stats['level'] = level_match.group(1)
                    
                # Extract race
                race_match = re.search(r'Race\s*:\s*([^\s]+)', line)
                if race_match:
                    stats['race'] = race_match.group(1)
                    
            # Look for Class line: "YEARS: 262         Class: Warrior"
            if 'Class:' in line:
                class_match = re.search(r'Class:\s*([^\s]+)', line)
                if class_match:
                    stats['class'] = class_match.group(1)
                    
            # Look for Align line: "DEX  : 21(14)      Align: +1000, devout"
            if 'Align:' in line:
                align_match = re.search(r'Align:\s*([^\n]+)', line)
                if align_match:
                    stats['alignment'] = align_match.group(1).strip()
                    
            # Look for Gold line: "Gold : 17,737,804"
            if line.startswith('Gold :') or 'Gold :' in line:
                gold_match = re.search(r'Gold\s*:\s*([\d,]+)', line)
                if gold_match:
                    stats['gold'] = gold_match.group(1).replace(',', '')
                    
            # Look for HitRoll and DamRoll: "HitRoll: 70               Saved: no save this session"
            if 'HitRoll:' in line:
                hitroll_match = re.search(r'HitRoll:\s*(\d+)', line)
                if hitroll_match:
                    stats['hitroll'] = hitroll_match.group(1)
                    
            if 'DamRoll:' in line:
                damroll_match = re.search(r'DamRoll:\s*(\d+)', line)
                if damroll_match:
                    stats['damroll'] = damroll_match.group(1)
                    
            # Look for Hitpoints: "Hitpoints: 1958  of  1958"
            if 'Hitpoints:' in line:
                hp_match = re.search(r'Hitpoints:\s*(\d+)\s*of\s*(\d+)', line)
                if hp_match:
                    stats['hitpoints'] = f"{hp_match.group(1)}/{hp_match.group(2)}"
                    
            # Look for Glory: "Glory: 0000(0000)"
            if line.startswith('Glory:'):
                glory_match = re.search(r'Glory:\s*(\d+)', line)
                if glory_match:
                    stats['glory'] = glory_match.group(1)
                    
            # Look for Deity: "Deity:  Tempus"
            if line.startswith('Deity:'):
                deity_match = re.search(r'Deity:\s*([^\s]+)', line)
                if deity_match:
                    stats['deity'] = deity_match.group(1)
                    
            # Look for Order: "Order:  Ascendere"
            if line.startswith('Order:'):
                order_match = re.search(r'Order:\s*([^\s]+)', line)
                if order_match:
                    stats['org'] = order_match.group(1)
                
        return stats
    
    async def scan_container(self, container_name: str) -> List[Dict]:
        """Scan a specific container and parse its contents."""
        logger.debug(f"Scanning container: {container_name}")
        
        # Use 'exam' command to examine the container (no additional delay - handled by caller)
        response = await self.mud_client.send_command(f"exam {container_name}")
        
        # Check if container exists and has contents
        if ("you do not see that here" in response.lower() or 
            "you do not see" in response.lower() or 
            "what do you want to" in response.lower()):
            # Container not found
            logger.warning(f"Smart container scan failed - container '{container_name}' not found")
            return []
        elif "appears to be empty" in response.lower():
            logger.debug(f"Container {container_name} is empty")
            return []
            
        return self.parse_container_output(response, container_name)
    
    async def scan_inventory(self) -> List[Dict]:
        """Scan carried inventory."""
        logger.debug("Scanning carried inventory")
        
        # Use 'i' command to show inventory (no additional delay - handled by caller)
        response = await self.mud_client.send_command("i")
        return self.parse_inventory_output(response)
    
    async def scan_equipment(self) -> List[Dict]:
        """Scan equipped items."""
        logger.debug("Scanning equipment")
        
        # Use 'garb' command to show equipment (no additional delay - handled by caller)
        response = await self.mud_client.send_command("garb")
        logger.debug(f"Equipment response length: {len(response)} chars")
        logger.debug(f"Equipment response: {response[:500]}...")
        return self.parse_equipment_output(response)
    
    def parse_container_output(self, response: str, container_name: str) -> List[Dict]:
        """Parse container examination output."""
        items = []
        lines = response.split('\n')
        seen_items = set()  # Track items to avoid duplicates
        
        # Look for the "contains:" section
        in_contents = False
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and character status lines
            if not line or (line.startswith('[') and line.endswith(']')):
                continue
                
            # Look for container contents section
            if "contains:" in line.lower() or "holds:" in line.lower():
                in_contents = True
                continue
                
            # Stop at next prompt or new command
            if (line.endswith('HTY\\') or 
                line.endswith('>') or 
                (line.startswith('[') and 'hp' in line)):
                break
                
            # Parse items if we're in contents section
            if in_contents and line:
                # Only add if we haven't seen this exact item line before
                if line not in seen_items:
                    seen_items.add(line)
                    item = self.parse_item_line(line, container_name)
                    if item:
                        items.append(item)
                    
        return items
    
    def parse_inventory_output(self, response: str) -> List[Dict]:
        """Parse inventory command output."""
        items = []
        lines = response.split('\n')
        seen_items = set()  # Track items to avoid duplicates
        
        # Look for inventory items after the "You are carrying" line
        found_header = False
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and character status lines
            if not line or (line.startswith('[') and line.endswith(']')):
                continue
                
            # Look for inventory header
            if "you are carrying" in line.lower() and ("items" in line.lower() or "item" in line.lower()):
                found_header = True
                continue
                
            # Stop at next prompt or new command
            if (line.endswith('HTY\\') or 
                line.endswith('>') or 
                (line.startswith('[') and 'hp' in line)):
                break
                
            # Parse items if we found the header
            if found_header and line:
                # Only add if we haven't seen this exact item line before
                if line not in seen_items:
                    seen_items.add(line)
                    item = self.parse_item_line(line, "inventory")
                    if item:
                        items.append(item)
                    
        return items
    
    def parse_equipment_output(self, response: str) -> List[Dict]:
        """Parse equipment command output and track empty slots."""
        items = []
        empty_slots = []
        lines = response.split('\n')
        seen_items = set()  # Track slot+item combinations to avoid duplicates
        
        # Define all possible equipment slots and track which ones we find
        all_slots = [
            'used as light', 'worn on finger', 'worn around neck', 'worn on body', 
            'worn on head', 'worn on legs', 'worn on feet', 'worn on hands', 
            'worn on arms', 'worn about body', 'worn about waist', 'worn around wrist',
            'wielded', 'dual wielded', 'worn as shield', 'held', 'worn on ears', 
            'worn on eyes', 'worn on back', 'worn over face', 'worn around ankle'
        ]
        found_slots = set()
        
        # Look for equipment lines after "You are using:"
        found_header = False
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and character status lines
            if not line or (line.startswith('[') and line.endswith(']')):
                continue
                
            # Look for equipment header
            if "you are using:" in line.lower():
                found_header = True
                continue
                
            # Stop at next prompt or new command
            if (line.endswith('HTY\\') or 
                line.endswith('>') or 
                (line.startswith('[') and 'hp' in line)):
                break
                
            # Parse equipment slot lines
            if found_header and line.startswith('<') and '>' in line:
                match = re.match(r'^<(.+?)>\s*(.+)$', line)
                if match:
                    slot = match.group(1)
                    item_text = match.group(2).strip()
                    found_slots.add(slot)
                    
                    # Check if slot is empty
                    if item_text.lower() in ['nothing', 'none', 'empty', '[nothing]']:
                        # Track ALL empty slots for needs analysis
                        empty_slots.append(slot)
                    else:
                        # Add equipped item only if we haven't seen this exact slot+item combo
                        item_key = f"{slot}:{item_text}"
                        if item_key not in seen_items:
                            seen_items.add(item_key)
                            item = self.parse_item_line(item_text, f"equipped:{slot}")
                            if item:
                                items.append(item)
        
        # Store empty slots for needs calculation
        self.empty_equipment_slots = empty_slots
        return items
    
    def generate_needs_list(self) -> str:
        """Generate a needs list based on empty equipment slots."""
        if not hasattr(self, 'empty_equipment_slots') or not self.empty_equipment_slots:
            return '-'
        
        # Map slot names to short descriptive names
        slot_mapping = {
            'used as light': 'light',
            'worn on finger': 'ring',
            'worn around neck': 'neck',
            'worn on body': 'body',
            'worn on head': 'head',
            'worn on legs': 'legs',
            'worn on feet': 'feet',
            'worn on hands': 'hands',
            'worn on arms': 'arms',
            'worn about body': 'cloak',
            'worn about waist': 'waist',
            'worn around wrist': 'wrist',
            'wielded': 'weapon',
            'dual wielded': 'dual',
            'worn as shield': 'shield',
            'held': 'held',
            'worn on ears': 'ears',
            'worn on eyes': 'eyes',
            'worn on back': 'back',
            'worn over face': 'face',
            'worn around ankle': 'ankle'
        }
        
        needs = []
        for slot in self.empty_equipment_slots:
            if slot in slot_mapping:
                needs.append(slot_mapping[slot])
            else:
                # For unmapped slots, use a cleaned version of the slot name
                clean_slot = slot.replace('worn ', '').replace('around ', '').replace('about ', '').replace('on ', '').replace('over ', '').replace('as ', '')
                needs.append(clean_slot)
        
        if needs:
            return ', '.join(needs)
        return '-'
    
    def parse_item_line(self, line: str, location: str) -> Optional[Dict]:
        """Parse a single item line."""
        if not line or line.lower() in ['nothing', 'none', 'empty']:
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
        item_name = self.clean_item_name(item_name)
        
        if not item_name:
            return None
            
        return {
            'character': self.current_character,
            'location': location,
            'item_name': item_name,
            'quantity': quantity,
            'scan_time': datetime.now().isoformat(),
            'raw_line': line
        }
    
    def clean_item_name(self, name: str) -> str:
        """Clean and normalize item name."""
        # Just strip whitespace - keep all magical properties and modifiers
        name = name.strip()
        
        # Remove leading articles if they're at the very beginning
        if name.lower().startswith('a '):
            name = name[2:]
        elif name.lower().startswith('an '):
            name = name[3:]
        elif name.lower().startswith('the '):
            name = name[4:]
            
        return name.strip()
    
    def get_smart_scan_stats(self) -> Dict:
        """Get statistics about the smart container scan."""
        container_mappings = self.container_manager.get_all_mappings()
        return {
            'detected_containers': self.detected_containers.copy(),
            'unknown_containers': self.unknown_containers.copy(),
            'total_container_mappings': len(container_mappings),
            'detection_successful': len(self.detected_containers) > 0,
            'unknown_found': len(self.unknown_containers) > 0
        }
    
    def add_container_mapping(self, item_name: str, container_keyword: str) -> bool:
        """Add a new container mapping through the scanner."""
        success = self.container_manager.add_container_mapping(item_name, container_keyword)
        if success:
            logger.info(f"Added container mapping: '{item_name}' -> {container_keyword}")
        return success
    
    def get_container_suggestions(self) -> List[str]:
        """Get suggestions for new container mappings based on unknown containers found."""
        return self.unknown_containers.copy()