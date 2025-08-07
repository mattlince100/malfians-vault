"""Enhanced house mapping system for visual layout generation."""

import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Room:
    """Represents a room in a house."""
    id: str
    name: str
    exits: Dict[str, str]  # direction -> destination_room_id
    containers: List[str]
    x: int = 0
    y: int = 0
    level: int = 0

class HouseMapper:
    """Maps house layouts from room connection data."""
    
    def __init__(self):
        self.rooms: Dict[str, Room] = {}
        self.entrance_id: Optional[str] = None
        
    def parse_room_data(self, room_data_string: str) -> Dict[str, Room]:
        """
        Parse enhanced room data format.
        Format: "id:name:exits(dir>dest):containers|..."
        Example: "1:Entrance:n>2,e>3:chest,shelf"
        """
        rooms = {}
        room_entries = room_data_string.split('|')
        
        for entry in room_entries:
            parts = entry.split(':')
            if len(parts) < 4:
                continue
                
            room_id = parts[0].strip()
            room_name = parts[1].strip()
            exits_str = parts[2].strip()
            containers_str = parts[3].strip() if len(parts) > 3 else ""
            
            # Parse exits
            exits = {}
            if exits_str:
                for exit_pair in exits_str.split(','):
                    if '>' in exit_pair:
                        direction, destination = exit_pair.split('>')
                        exits[direction.strip()] = destination.strip()
            
            # Parse containers
            containers = [c.strip() for c in containers_str.split(',') if c.strip()]
            
            room = Room(
                id=room_id,
                name=room_name,
                exits=exits,
                containers=containers
            )
            rooms[room_id] = room
            
            # First room is typically the entrance
            if not self.entrance_id:
                self.entrance_id = room_id
                
        self.rooms = rooms
        return rooms
    
    def calculate_layout(self) -> Dict[str, Room]:
        """
        Calculate 2D positions for rooms based on their connections.
        Uses a breadth-first approach from the entrance.
        """
        if not self.entrance_id or not self.rooms:
            return {}
            
        # Start with entrance at origin
        entrance = self.rooms[self.entrance_id]
        entrance.x = 0
        entrance.y = 0
        entrance.level = 0
        
        visited = {self.entrance_id}
        queue = [(self.entrance_id, 0, 0, 0)]  # room_id, x, y, level
        
        # Direction to coordinate changes
        direction_map = {
            'n': (0, -1, 0),
            's': (0, 1, 0),
            'e': (1, 0, 0),
            'w': (-1, 0, 0),
            'ne': (1, -1, 0),
            'nw': (-1, -1, 0),
            'se': (1, 1, 0),
            'sw': (-1, 1, 0),
            'u': (0, 0, 1),    # Up increases level
            'd': (0, 0, -1),   # Down decreases level
        }
        
        while queue:
            current_id, x, y, level = queue.pop(0)
            current_room = self.rooms[current_id]
            
            for direction, dest_id in current_room.exits.items():
                if dest_id not in visited and dest_id in self.rooms:
                    dx, dy, dl = direction_map.get(direction, (0, 0, 0))
                    
                    dest_room = self.rooms[dest_id]
                    dest_room.x = x + dx
                    dest_room.y = y + dy
                    dest_room.level = level + dl
                    
                    visited.add(dest_id)
                    queue.append((dest_id, dest_room.x, dest_room.y, dest_room.level))
        
        # Normalize positions to start from 0,0
        if self.rooms:
            min_x = min(r.x for r in self.rooms.values())
            min_y = min(r.y for r in self.rooms.values())
            
            for room in self.rooms.values():
                room.x -= min_x
                room.y -= min_y
                
        return self.rooms
    
    def detect_layout_type(self) -> str:
        """
        Detect the general layout pattern of the house.
        Returns: 'linear', 'branching', 'circular', 'grid', 'complex'
        """
        if not self.rooms:
            return 'empty'
            
        # Count connections per room
        connection_counts = []
        for room in self.rooms.values():
            connection_counts.append(len(room.exits))
            
        avg_connections = sum(connection_counts) / len(connection_counts)
        max_connections = max(connection_counts)
        
        # Detect patterns
        if max_connections <= 2 and avg_connections <= 1.5:
            return 'linear'
        elif max_connections >= 4:
            return 'grid'
        elif any(self._has_cycle()):
            return 'circular'
        elif max_connections == 3:
            return 'branching'
        else:
            return 'complex'
    
    def _has_cycle(self) -> bool:
        """Check if the house layout has any cycles."""
        if not self.entrance_id:
            return False
            
        visited = set()
        
        def dfs(room_id: str, parent: Optional[str] = None) -> bool:
            visited.add(room_id)
            room = self.rooms.get(room_id)
            if not room:
                return False
                
            for direction, dest_id in room.exits.items():
                if dest_id not in self.rooms:
                    continue
                if dest_id not in visited:
                    if dfs(dest_id, room_id):
                        return True
                elif dest_id != parent:
                    return True
            return False
        
        return dfs(self.entrance_id)
    
    def export_to_json(self) -> str:
        """Export the layout to JSON for the web interface."""
        layout_data = {
            'entrance': self.entrance_id,
            'layout_type': self.detect_layout_type(),
            'rooms': []
        }
        
        for room in self.rooms.values():
            layout_data['rooms'].append({
                'id': room.id,
                'name': room.name,
                'x': room.x,
                'y': room.y,
                'level': room.level,
                'exits': room.exits,
                'containers': room.containers
            })
            
        return json.dumps(layout_data, indent=2)
    
    def generate_simple_format(self) -> str:
        """
        Generate the simple format for backwards compatibility.
        Returns: "RoomName:path:containers|..."
        """
        if not self.entrance_id or not self.rooms:
            return ""
            
        result = []
        visited = set()
        
        def build_path(room_id: str, path: List[str] = None) -> None:
            if room_id in visited:
                return
            visited.add(room_id)
            
            room = self.rooms[room_id]
            if path is None:
                path_str = "start"
            else:
                path_str = ";".join(path)
                
            containers_str = ",".join(room.containers)
            result.append(f"{room.name}:{path_str}:{containers_str}")
            
            for direction, dest_id in room.exits.items():
                if dest_id not in visited:
                    new_path = (path or []) + [direction]
                    build_path(dest_id, new_path)
        
        build_path(self.entrance_id)
        return "|".join(result)


# Example usage
if __name__ == "__main__":
    mapper = HouseMapper()
    
    # Enhanced format with room connections
    room_data = "1:Manse of the Macabre:d>2:reliquary,crate,shell|2:Madness Below:u>1,d>3:shell|3:Base of the Pit:u>2,n>5,s>4:crate,reliquary,shell|4:Alchemy Laboratory:n>3:shelf,rack,desk|5:Vault of the Elders:s>3:bin,box"
    
    mapper.parse_room_data(room_data)
    mapper.calculate_layout()
    
    print("Layout type:", mapper.detect_layout_type())
    print("\nRoom positions:")
    for room in mapper.rooms.values():
        print(f"  {room.name}: ({room.x}, {room.y}) level {room.level}")
    
    print("\nJSON export:")
    print(mapper.export_to_json())
    
    print("\nSimple format:")
    print(mapper.generate_simple_format())