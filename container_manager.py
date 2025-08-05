"""Container mappings manager for smart inventory scanning."""

import json
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

class ContainerManager:
    """Manages container mappings for smart inventory scanning."""
    
    def __init__(self, mappings_file='container_mappings.json'):
        self.mappings_file = mappings_file
        self.container_mappings = {}
        self.load_mappings()
    
    def load_mappings(self) -> bool:
        """Load container mappings from JSON file."""
        try:
            with open(self.mappings_file, 'r') as f:
                data = json.load(f)
                self.container_mappings = data.get('container_mappings', {})
                logger.info(f"Loaded {len(self.container_mappings)} container mappings")
                return True
        except FileNotFoundError:
            logger.warning(f"Container mappings file {self.mappings_file} not found, using empty mappings")
            self.container_mappings = {}
            return False
        except Exception as e:
            logger.error(f"Error loading container mappings: {e}")
            self.container_mappings = {}
            return False
    
    def save_mappings(self) -> bool:
        """Save container mappings to JSON file."""
        try:
            data = {
                'container_mappings': self.container_mappings,
                'metadata': {
                    'version': '1.0',
                    'last_updated': datetime.now().isoformat(),
                    'total_mappings': len(self.container_mappings)
                }
            }
            with open(self.mappings_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self.container_mappings)} container mappings")
            return True
        except Exception as e:
            logger.error(f"Error saving container mappings: {e}")
            return False
    
    def detect_containers_in_inventory(self, inventory_items: List[Dict]) -> Tuple[List[str], List[str]]:
        """
        Detect containers in inventory items.
        
        Returns:
            Tuple of (detected_containers, unknown_potential_containers)
        """
        detected_containers = []
        unknown_potential_containers = []
        
        for item in inventory_items:
            item_name = item.get('item_name', '').strip()
            
            # Strip item flags like (Magical), (Glowing), etc. from the beginning
            clean_item_name = self._strip_item_flags(item_name)
            
            # Check if this item matches a known container
            container_keyword = self._find_container_mapping(clean_item_name)
            
            if container_keyword:
                if container_keyword not in detected_containers:
                    detected_containers.append(container_keyword)
                    logger.info(f"Detected container: '{clean_item_name}' -> {container_keyword}")
            else:
                # Check if this might be a container based on common container words
                if self._might_be_container(clean_item_name):
                    if clean_item_name not in unknown_potential_containers:
                        unknown_potential_containers.append(clean_item_name)
                        logger.info(f"Unknown potential container: '{clean_item_name}'")
        
        return detected_containers, unknown_potential_containers
    
    def _strip_item_flags(self, item_name: str) -> str:
        """
        Strip item flags like (Magical), (Glowing), etc. from item names.
        
        Args:
            item_name: The item name possibly containing flags
            
        Returns:
            Clean item name without flags
        """
        import re
        # Remove all parenthetical flags at the beginning of the item name
        # This handles (Magical), (Glowing), (Humming), (Red Aura), etc.
        clean_name = re.sub(r'^(\([^)]+\)\s*)+', '', item_name).strip()
        return clean_name
    
    def _find_container_mapping(self, item_name: str) -> Optional[str]:
        """
        Find container mapping for an item, trying multiple variations.
        
        Args:
            item_name: The item name to search for
            
        Returns:
            Container keyword if found, None otherwise
        """
        # Try exact match first
        if item_name in self.container_mappings:
            return self.container_mappings[item_name]
        
        # Try with articles added
        for article in ['a ', 'an ', 'the ']:
            with_article = article + item_name
            if with_article in self.container_mappings:
                return self.container_mappings[with_article]
        
        # Try with articles removed (in case mapping doesn't have article)
        item_lower = item_name.lower()
        if item_lower.startswith(('a ', 'an ', 'the ')):
            # Remove article and try again
            if item_lower.startswith('a '):
                without_article = item_name[2:].strip()
            elif item_lower.startswith('an '):
                without_article = item_name[3:].strip()
            elif item_lower.startswith('the '):
                without_article = item_name[4:].strip()
            
            if without_article in self.container_mappings:
                return self.container_mappings[without_article]
        
        return None
    
    def _might_be_container(self, item_name: str) -> bool:
        """Check if an item might be a container based on common container words."""
        container_indicators = [
            'basket', 'pouch', 'bag', 'sack', 'chest', 'case', 'container', 
            'box', 'crate', 'barrel', 'pack', 'satchel', 'knapsack', 'backpack',
            'rift', 'portal', 'void', 'pocket', 'quiver', 'sheath', 'scabbard'
        ]
        
        item_lower = item_name.lower()
        return any(indicator in item_lower for indicator in container_indicators)
    
    def add_container_mapping(self, item_name: str, container_keyword: str) -> bool:
        """Add a new container mapping."""
        try:
            self.container_mappings[item_name.strip()] = container_keyword.strip()
            return self.save_mappings()
        except Exception as e:
            logger.error(f"Error adding container mapping: {e}")
            return False
    
    def remove_container_mapping(self, item_name: str) -> bool:
        """Remove a container mapping."""
        try:
            if item_name in self.container_mappings:
                del self.container_mappings[item_name]
                return self.save_mappings()
            return True
        except Exception as e:
            logger.error(f"Error removing container mapping: {e}")
            return False
    
    def get_all_mappings(self) -> Dict[str, str]:
        """Get all container mappings."""
        return self.container_mappings.copy()
    
    def get_container_keyword(self, item_name: str) -> Optional[str]:
        """Get container keyword for an item name."""
        return self.container_mappings.get(item_name)
    
    def get_stats(self) -> Dict:
        """Get statistics about container mappings."""
        return {
            'total_mappings': len(self.container_mappings),
            'mappings_file': self.mappings_file,
            'last_loaded': datetime.now().isoformat()
        }