"""Data management for processing and storing inventory data."""

import csv
import pandas as pd
import logging
import glob
import os
from typing import List, Dict, Tuple
from datetime import datetime
from config import OUTPUT_CSV_FILE, SAVE_RAW_OUTPUT

logger = logging.getLogger(__name__)


class DataManager:
    """Manages inventory data processing and storage."""
    
    def __init__(self, load_existing=True):
        self.all_data: List[Dict] = []
        self.character_stats: List[Dict] = []
        
        if load_existing:
            self._load_existing_data()
    
    def normalize_character_name(self, name: str) -> str:
        """Normalize character name to consistent capitalization."""
        if not name:
            return name
        # Capitalize first letter, keep rest as-is for now
        # This ensures consistent casing for new characters
        return name.strip().capitalize()
    
    def _load_existing_data(self):
        """Load existing inventory and character stats data from previous scans."""
        try:
            # Load latest inventory data
            inventory_files = glob.glob("inventory_backup_*.csv")
            if inventory_files:
                # Prioritize cleaned files over merged, then regular files
                clean_files = [f for f in inventory_files if 'CLEAN' in f]
                merged_files = [f for f in inventory_files if 'MERGED' in f and 'CLEAN' not in f]
                regular_files = [f for f in inventory_files if 'MERGED' not in f and 'CLEAN' not in f]
                
                # Prefer latest cleaned file, then merged, then regular
                if clean_files:
                    latest_file = max(clean_files, key=os.path.getctime)
                elif merged_files:
                    latest_file = max(merged_files, key=os.path.getctime)
                elif regular_files:
                    latest_file = max(regular_files, key=os.path.getctime)
                else:
                    latest_file = None
                
                if latest_file:
                    df = pd.read_csv(latest_file)
                    self.all_data = df.to_dict('records')
                    logger.info(f"Loaded {len(self.all_data)} existing inventory items from {latest_file}")
            
            # Load latest character stats data
            stats_files = glob.glob("character_stats_*.csv")
            if stats_files:
                # Prioritize cleaned files over merged, then regular files
                clean_files = [f for f in stats_files if 'CLEAN' in f]
                merged_files = [f for f in stats_files if 'MERGED' in f and 'CLEAN' not in f]
                regular_files = [f for f in stats_files if 'MERGED' not in f and 'CLEAN' not in f]
                
                # Prefer latest cleaned file, then merged, then regular
                if clean_files:
                    latest_file = max(clean_files, key=os.path.getctime)
                elif merged_files:
                    latest_file = max(merged_files, key=os.path.getctime)
                elif regular_files:
                    latest_file = max(regular_files, key=os.path.getctime)
                else:
                    latest_file = None
                
                if latest_file:
                    df = pd.read_csv(latest_file)
                    # Convert to dict but keep as a dict indexed by character name for deduplication
                    existing_stats = {row['character'].lower(): row for _, row in df.iterrows()}
                    self.character_stats = list(existing_stats.values())
                    logger.info(f"Loaded {len(self.character_stats)} existing character stats from {latest_file}")
        
        except Exception as e:
            logger.warning(f"Could not load existing data: {e}")
            # Continue with empty data if loading fails
    
    def add_character_data(self, character_data: List[Dict], char_stats: Dict = None):
        """Add scanned data from a character to the collection, replacing any existing data for that character."""
        
        if character_data and len(character_data) > 0:
            # Preserve original character name for house characters - don't normalize case for houses
            original_name = character_data[0]['character']
            
            # Safety check: ensure character name doesn't contain ANSI codes (indicates corrupted data)
            import re
            if re.search(r'[\x1b\\].*?m', str(original_name)):
                logger.error(f"Character name contains ANSI codes, data may be corrupted: {repr(original_name)}")
                # Try to extract a clean character name or skip this data
                clean_name = re.sub(r'\x1b\[[0-9;]*m', '', str(original_name))
                clean_name = re.sub(r'\\x1b\[[0-9;]*m', '', clean_name).strip()
                if clean_name and len(clean_name) < 50:  # Reasonable character name length
                    logger.info(f"Recovered character name: {clean_name}")
                    original_name = clean_name
                    # Update all items with clean name
                    for item in character_data:
                        item['character'] = clean_name
                else:
                    logger.error("Cannot recover character name, skipping corrupted data")
                    return
            
            # Only normalize non-house characters
            if '_house' not in original_name.lower() and '_House' not in original_name:
                normalized_name = self.normalize_character_name(original_name)
                for item in character_data:
                    item['character'] = normalized_name
            else:
                # Keep house character names exactly as they are
                normalized_name = original_name
            
            # Get character name for comparison - exact match now, not just case-insensitive
            char_name_exact = normalized_name
            
            # Remove any existing inventory data for this exact character name
            original_count = len(self.all_data)
            self.all_data = [item for item in self.all_data if item['character'] != char_name_exact]
            removed_count = original_count - len(self.all_data)
            
            if removed_count > 0:
                logger.info(f"Removed {removed_count} existing items for character: {normalized_name}")
            
            # Add new inventory data for this character
            self.all_data.extend(character_data)
            logger.info(f"Added {len(character_data)} new items for character: {normalized_name}")
        
        if char_stats:
            # Normalize character name in stats
            normalized_name = self.normalize_character_name(char_stats['character'])
            char_stats['character'] = normalized_name
            char_name = normalized_name.lower()
            
            # Find and replace existing stats for this character
            existing_index = None
            for i, existing_stats in enumerate(self.character_stats):
                if existing_stats['character'].lower() == char_name:
                    existing_index = i
                    break
            
            if existing_index is not None:
                # Update existing character stats
                self.character_stats[existing_index] = char_stats
                logger.info(f"Updated stats for character: {normalized_name}")
            else:
                # Add new character stats
                self.character_stats.append(char_stats)
                logger.info(f"Added new character: {normalized_name}")
        
        total_items = len(self.all_data)
        total_characters = len(set(item['character'].lower() for item in self.all_data))
        logger.info(f"Dataset now contains {total_items} items from {total_characters} characters")
    
    def export_character_stats(self, filename: str = None) -> str:
        """Export character statistics to CSV file."""
        if not self.character_stats:
            logger.warning("No character stats to export")
            return None
            
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"character_stats_{timestamp}.csv"
        
        try:
            # Clean character_stats data for CSV export
            clean_stats = []
            for stat in self.character_stats:
                if isinstance(stat, dict):
                    # Convert any nested structures to strings for CSV compatibility
                    clean_stat = {}
                    for key, value in stat.items():
                        if isinstance(value, (dict, list)):
                            clean_stat[key] = str(value)
                        else:
                            clean_stat[key] = value
                    clean_stats.append(clean_stat)
                elif hasattr(stat, 'to_dict'):
                    # Handle pandas Series objects
                    clean_stat = {}
                    stat_dict = stat.to_dict() if hasattr(stat, 'to_dict') else dict(stat)
                    for key, value in stat_dict.items():
                        if isinstance(value, (dict, list)):
                            clean_stat[key] = str(value)
                        else:
                            clean_stat[key] = value
                    clean_stats.append(clean_stat)
                else:
                    logger.warning(f"Unexpected character stat type: {type(stat)} - skipping")
                    continue
            
            df_stats = pd.DataFrame(clean_stats)
            df_stats.to_csv(filename, index=False)
            logger.info(f"Exported {len(df_stats)} character stats to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error exporting character stats: {str(e)}")
            logger.error(f"Character stats structure: {type(self.character_stats)}")
            if self.character_stats:
                logger.error(f"First stat structure: {type(self.character_stats[0])}")
            return None
        
    def process_inventory_data(self) -> pd.DataFrame:
        """Process raw inventory data into a cleaned DataFrame."""
        if not self.all_data:
            logger.warning("No data to process")
            return pd.DataFrame()
            
        # Create DataFrame
        df = pd.DataFrame(self.all_data)
        
        # Sort by character and location
        df = df.sort_values(['character', 'location', 'item_name'])
        
        # Add additional columns for analysis
        df['is_equipment'] = df['location'].str.startswith('equipped:')
        df['container'] = df['location'].apply(lambda x: x.split(':')[0])
        
        logger.info(f"Processed {len(df)} total items")
        return df
    
    def export_to_csv(self, filename: str = None) -> str:
        """Export inventory data to CSV file."""
        if filename is None:
            filename = OUTPUT_CSV_FILE
            
        df = self.process_inventory_data()
        
        if df.empty:
            logger.warning("No data to export")
            return ""
            
        # Select columns to export - include house-specific columns if they exist
        export_columns = ['character', 'location', 'item_name', 'quantity', 'scan_time']
        if SAVE_RAW_OUTPUT:
            export_columns.append('raw_line')
        
        # Add house-specific columns if they exist in the data
        if 'house_owner' in df.columns:
            export_columns.append('house_owner')
        if 'house_name' in df.columns:
            export_columns.append('house_name')
            
        df[export_columns].to_csv(filename, index=False)
        logger.info(f"Exported {len(df)} items to {filename}")
        
        return filename
    
    def generate_summary_stats(self) -> Dict[str, any]:
        """Generate summary statistics for the inventory data."""
        df = self.process_inventory_data()
        
        if df.empty:
            return {
                'total_items': 0,
                'total_characters': 0,
                'scan_time': datetime.now().isoformat()
            }
            
        # Calculate statistics
        stats = {
            'total_items': len(df),
            'total_quantity': df['quantity'].astype(int).sum(),
            'unique_items': df['item_name'].nunique(),
            'total_characters': df['character'].nunique(),
            'scan_time': datetime.now().isoformat(),
            'character_summary': [],
            'location_summary': []
        }
        
        # Character summary
        char_summary = df.groupby('character').agg({
            'item_name': 'count',
            'quantity': lambda x: x.astype(int).sum()
        }).reset_index()
        char_summary.columns = ['character', 'item_count', 'total_quantity']
        stats['character_summary'] = char_summary.to_dict('records')
        
        # Location summary
        loc_summary = df.groupby('container').agg({
            'item_name': 'count',
            'quantity': lambda x: x.astype(int).sum()
        }).reset_index()
        loc_summary.columns = ['location', 'item_count', 'total_quantity']
        stats['location_summary'] = loc_summary.to_dict('records')
        
        # Most common items
        item_counts = df.groupby('item_name').agg({
            'quantity': lambda x: x.astype(int).sum(),
            'character': 'count'
        }).reset_index()
        item_counts.columns = ['item_name', 'total_quantity', 'character_count']
        item_counts = item_counts.sort_values('total_quantity', ascending=False).head(10)
        stats['top_items'] = item_counts.to_dict('records')
        
        return stats
    
    def find_items(self, search_term: str) -> pd.DataFrame:
        """Search for items matching a term."""
        df = self.process_inventory_data()
        
        if df.empty:
            return pd.DataFrame()
            
        # Case-insensitive search
        mask = df['item_name'].str.contains(search_term, case=False, na=False)
        results = df[mask]
        
        logger.info(f"Found {len(results)} items matching '{search_term}'")
        return results
    
    def get_character_inventory(self, character_name: str) -> pd.DataFrame:
        """Get all items for a specific character."""
        df = self.process_inventory_data()
        
        if df.empty:
            return pd.DataFrame()
            
        return df[df['character'] == character_name]