# map.py
import pygame
import random
import noise # Perlin noise
import math
from constants import *
from tile import Tile

class GameMap:
    def __init__(self, radius):
        self.radius = radius
        self.diameter = radius * 2 + 1
        self.tiles = [[None for _ in range(self.diameter)] for _ in range(self.diameter)]
        self.depleted_resources = {} # Store coords and original type for respawn: (x, y): type
        self._generate_map()
        self.width_pixels = self.diameter * TILE_SIZE
        self.height_pixels = self.diameter * TILE_SIZE

    def _generate_map(self):
        seed = random.randint(0, 10000)
        center_x, center_y = self.radius, self.radius

        print(f"Generating map with radius {self.radius} (Diameter: {self.diameter})")

        # Generate noise maps
        elevation_map = self._generate_noise_map(seed + 0)
        temperature_map = self._generate_noise_map(seed + 1)
        moisture_map = self._generate_noise_map(seed + 2)

        for y in range(self.diameter):
            for x in range(self.diameter):
                dist_from_center = math.sqrt((x - center_x)**2 + (y - center_y)**2)
                dist_ratio = dist_from_center / self.radius

                # Adjust elevation towards edges to create water border
                elevation = elevation_map[y][x]
                edge_factor = max(0, (dist_ratio - (1.0 - WATER_EDGE_PERCENT)) / WATER_EDGE_PERCENT) # 0 to 1 in the outer edge %
                elevation -= edge_factor * 0.8 # Significantly lower elevation at the very edge

                temp = temperature_map[y][x]
                moisture = moisture_map[y][x]

                # Determine Terrain Type
                if elevation < ELEVATION_THRESHOLD:
                     terrain_type = TERRAIN_WATER
                     if temp < TEMP_THRESHOLD_LOW - 0.1: # Colder water = ice
                         terrain_type = TERRAIN_ICE
                else:
                    terrain_type = TERRAIN_GROUND

                # Determine Biome (only for ground/ice)
                biome = BIOME_NONE
                if terrain_type == TERRAIN_WATER:
                    biome = BIOME_WATER
                elif terrain_type == TERRAIN_ICE:
                     biome = BIOME_ARCTIC # Ice is part of arctic
                else: # Ground
                    if temp < TEMP_THRESHOLD_LOW:
                        biome = BIOME_ARCTIC
                    elif temp > TEMP_THRESHOLD_HIGH and moisture < MOISTURE_THRESHOLD_LOW:
                        biome = BIOME_DESERT
                    elif moisture > MOISTURE_THRESHOLD_HIGH:
                         biome = BIOME_FOREST
                    else: # Default to Forest-like if no other match
                        biome = BIOME_FOREST # Or create a 'Plains' biome

                tile = Tile(x, y, terrain_type, biome)
                self.tiles[y][x] = tile

        self._place_resources()
        print("Map generation complete.")


    def _generate_noise_map(self, seed_offset):
         map_data = [[0.0 for _ in range(self.diameter)] for _ in range(self.diameter)]
         for y in range(self.diameter):
             for x in range(self.diameter):
                 map_data[y][x] = noise.pnoise2(
                     x * NOISE_SCALE,
                     y * NOISE_SCALE,
                     octaves=NOISE_OCTAVES,
                     persistence=NOISE_PERSISTENCE,
                     lacunarity=NOISE_LACUNARITY,
                     base=seed_offset
                 )
         return map_data

    def _place_resources(self):
        for y in range(self.diameter):
            for x in range(self.diameter):
                tile = self.tiles[y][x]
                if tile.terrain_type == TERRAIN_GROUND:
                    # Base probability - adjust these values for balance
                    prob_factor = 0.1

                    if tile.biome == BIOME_FOREST:
                        if random.random() < prob_factor * 3.0: # Higher chance in forest
                             if random.random() < 0.7: # Mostly wood
                                 tile.set_resource(RESOURCE_WOOD, random.randint(RESOURCE_START_AMOUNT[RESOURCE_WOOD]//2, RESOURCE_START_AMOUNT[RESOURCE_WOOD]))
                             else: # Some food
                                 tile.set_resource(RESOURCE_FOOD, random.randint(RESOURCE_START_AMOUNT[RESOURCE_FOOD]//2, RESOURCE_START_AMOUNT[RESOURCE_FOOD]))
                    elif tile.biome == BIOME_DESERT:
                        if random.random() < prob_factor * 1.5: # Moderate chance in desert
                             if random.random() < 0.6: # Mostly stone
                                 tile.set_resource(RESOURCE_STONE, random.randint(RESOURCE_START_AMOUNT[RESOURCE_STONE]//2, RESOURCE_START_AMOUNT[RESOURCE_STONE]))
                             else: # Some iron
                                 tile.set_resource(RESOURCE_IRON, random.randint(RESOURCE_START_AMOUNT[RESOURCE_IRON]//2, RESOURCE_START_AMOUNT[RESOURCE_IRON]))
                    elif tile.biome == BIOME_ARCTIC:
                         if random.random() < prob_factor * 0.2: # Low chance in arctic
                             if random.random() < 0.5:
                                 tile.set_resource(RESOURCE_STONE, random.randint(RESOURCE_START_AMOUNT[RESOURCE_STONE]//4, RESOURCE_START_AMOUNT[RESOURCE_STONE]//2))
                             # else: Maybe rare iron? For now, mostly barren


    def get_tile(self, x, y):
        if 0 <= x < self.diameter and 0 <= y < self.diameter:
            return self.tiles[y][x]
        return None

    def get_random_walkable_tile(self):
        attempts = 0
        while attempts < 1000:
            x = random.randint(0, self.diameter - 1)
            y = random.randint(0, self.diameter - 1)
            tile = self.get_tile(x, y)
            if tile and tile.walkable and tile.resource_type == RESOURCE_NONE and tile.building is None:
                # Also try to avoid starting right on the water edge if possible
                 dist_from_center = math.sqrt((x - self.radius)**2 + (y - self.radius)**2)
                 dist_ratio = dist_from_center / self.radius
                 if dist_ratio < 0.8: # Avoid outer 20% for starting position
                    return tile
            attempts += 1
        # Fallback if random spot not found quickly
        for y in range(self.radius - 5, self.radius + 5):
             for x in range(self.radius - 5, self.radius + 5):
                 tile = self.get_tile(x,y)
                 if tile and tile.walkable and tile.resource_type == RESOURCE_NONE and tile.building is None:
                     return tile
        return None # Should ideally always find a spot on a reasonable map

    def find_nearest_resource(self, start_x, start_y, resource_type, max_radius=15):
        """Simple BFS-like search for the nearest resource"""
        q = [(start_x, start_y, 0)]
        visited = set([(start_x, start_y)])
        while q:
            x, y, dist = q.pop(0)

            if dist > max_radius: continue

            tile = self.get_tile(x, y)
            if tile and tile.resource_type == resource_type and tile.resource_amount > 0:
                return tile # Found it

            # Check neighbors
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (nx, ny) not in visited:
                     neighbor_tile = self.get_tile(nx, ny)
                     # Can path through walkable tiles or the target resource tile itself
                     if neighbor_tile and (neighbor_tile.walkable or (neighbor_tile.resource_type == resource_type and neighbor_tile.resource_amount > 0)):
                        visited.add((nx, ny))
                        q.append((nx, ny, dist + 1))
        return None # Not found within radius

    def find_nearest_building(self, start_x, start_y, building_type, max_radius=30):
         """Simple BFS-like search for the nearest building of a type"""
         q = [(start_x, start_y, 0)]
         visited = set([(start_x, start_y)])
         while q:
             x, y, dist = q.pop(0)

             if dist > max_radius: continue

             tile = self.get_tile(x, y)
             if tile and tile.building and tile.building.type == building_type:
                 return tile.building # Found it

             # Check neighbors
             for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                 nx, ny = x + dx, y + dy
                 if (nx, ny) not in visited:
                      neighbor_tile = self.get_tile(nx, ny)
                      if neighbor_tile and neighbor_tile.walkable: # Can only path through walkable
                         visited.add((nx, ny))
                         q.append((nx, ny, dist + 1))
         return None


    def update_respawns(self, dt_ms, respawn_rate_modifier):
        spawned_coords = []
        # Iterate over a copy of keys because we might modify the dict
        for coords, original_type in list(self.depleted_resources.items()):
            tile = self.get_tile(coords[0], coords[1])
            if tile:
                tile.start_respawn(respawn_rate_modifier) # Ensure timer is running if not already
                if tile.update_respawn(dt_ms):
                     # Respawn the resource
                     tile.set_resource(original_type, RESOURCE_START_AMOUNT[original_type])
                     spawned_coords.append(coords) # Mark for removal from depleted list

        # Remove respawned resources from the tracking dict
        for coords in spawned_coords:
            del self.depleted_resources[coords]


    def draw(self, surface, camera_x, camera_y):
        # Calculate visible tile range
        start_col = max(0, camera_x // TILE_SIZE)
        end_col = min(self.diameter, (camera_x + GAME_AREA_WIDTH) // TILE_SIZE + 1)
        start_row = max(0, camera_y // TILE_SIZE)
        end_row = min(self.diameter, (camera_y + SCREEN_HEIGHT) // TILE_SIZE + 1)

        # Draw base tiles first
        for y in range(start_row, end_row):
            for x in range(start_col, end_col):
                tile = self.tiles[y][x]
                if tile:
                    tile.draw(surface, camera_x, camera_y)

        # Draw buildings/units/effects on top
        for y in range(start_row, end_row):
            for x in range(start_col, end_col):
                tile = self.tiles[y][x]
                if tile:
                    # We'll call draw methods for buildings/units from the main game loop
                    # after the map base is drawn, using the game's lists of these objects.
                    # However, if buildings were stored directly on tiles, we'd draw here:
                    # tile.draw_building_or_unit(surface, camera_x, camera_y)
                    pass