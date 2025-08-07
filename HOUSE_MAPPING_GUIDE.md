# House Mapping Guide

## Information Needed for Accurate House Maps

To create an accurate visual map of your house, we need the following information for each room:

### 1. Room Information
- **Room Name**: The exact name shown when you enter the room
- **Room ID/Position**: A unique identifier for reference
- **Containers**: What storage containers are in this room (chest, shelf, crate, etc.)

### 2. Exit Information
For each room, list ALL exits and where they lead:
- **Exit Direction**: n, s, e, w, ne, nw, se, sw, u, d
- **Destination Room**: Which room this exit leads to

### 3. Example Format

```csv
# Enhanced house configuration format
character,house_name,room_data
PlayerName,House Name,"room_id:room_name:exits:containers"

# Room data format:
# room_id:room_name:exits(dir>dest_id):containers

# Example for Kaan's House:
Kaan,Kaan's House,"1:Manse of the Macabre:d>2:reliquary,crate,shell|2:Madness Below:u>1,d>3:shell|3:Base of the Pit:u>2,n>5,s>4:crate,reliquary,shell|4:Alchemy Laboratory:n>3:shelf,rack,desk|5:Vault of the Elders:s>3:bin,box"
```

### 4. Step-by-Step Mapping Process

1. **Start at the entrance** of your house
2. **In each room, type `exits`** to see all available directions
3. **Document the room name** (shown when you enter)
4. **Move through each exit** and note where it leads
5. **List all containers** in each room using `look`

### 5. Information Collection Template

```
Room 1:
- Name: [Full room name as shown]
- Exits: 
  - north leads to: [room name]
  - south leads to: [room name]
  - up leads to: [room name]
  - down leads to: [room name]
- Containers: [list all containers]

Room 2:
[Repeat for each room]
```

### 6. Visual Layout Hints

To help the mapper understand your house layout, also provide:
- **Entry point**: Which room is the entrance?
- **Vertical levels**: Are some rooms above/below others?
- **Special layout**: Is it linear, branching, circular?

### 7. Example Complete Mapping

**Kaan's House** (Inverted T-shape, 3 levels):
```
Level 0 (Ground): 
  - Manse of the Macabre (entrance)
  
Level -1 (Basement):
  - Madness Below
  
Level -2 (Deep):
  - Base of the Pit (center)
  - Alchemy Laboratory (east wing)
  - Vault of the Elders (west wing)

Connections:
- Manse -> down -> Madness
- Madness -> up -> Manse, down -> Base
- Base -> up -> Madness, south -> Alchemy, north -> Vault
- Alchemy -> north -> Base
- Vault -> south -> Base
```

## Automated Mapping Algorithm

With this information, the system can:
1. Build a graph of room connections
2. Calculate optimal 2D positions for each room
3. Detect layout patterns (linear, branching, circular)
4. Handle multi-level structures
5. Draw connection lines between rooms

## Future Enhancements

Consider adding:
- Room types (storage, workshop, display, etc.)
- Room sizes (small, medium, large)
- Special features (portals, secret doors)
- Custom room colors or icons
- Notes about room purposes