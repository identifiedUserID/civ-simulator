# map.py
import pygame
import random
import noise # Perlin noise
import math
import collections # For deque in BFS
from constants import * # Import constants
from tile import Tile   # Import Tile class
# Need Building base class for type hinting / isinstance check in find_nearest
from building import Building

class GameMap:
    def __init__(self, radius: int):
        self.radius = radius
        self.diameter = radius * 2 + 1
        self.tiles: list[list[Tile | None]] = [[None for _ in range(self.diameter)] for _ in range(self.diameter)]
        self.pending_respawn_tiles: set[tuple[int, int]] = set()
        self._generate_map()
        self.width_pixels = self.diameter * TILE_SIZE
        self.height_pixels = self.diameter * TILE_SIZE

    # --- _generate_map, _generate_noise_map, _place_initial_resources remain the same ---
    def _generate_map(self):
        """Generates the entire map procedurally using noise."""
        seed = random.randint(0, 10000)
        center_x, center_y = self.radius, self.radius
        print(f"Generating map with radius {self.radius} (Diameter: {self.diameter}), Seed: {seed}")

        elevation_map = self._generate_noise_map(seed + 0)
        temperature_map = self._generate_noise_map(seed + 1)
        moisture_map = self._generate_noise_map(seed + 2)

        for y in range(self.diameter):
            for x in range(self.diameter):
                dist_from_center = math.sqrt((x - center_x)**2 + (y - center_y)**2)
                dist_ratio = dist_from_center / max(1, self.radius)

                elevation = elevation_map[y][x]
                edge_start_ratio = 1.0 - WATER_EDGE_PERCENT
                if dist_ratio > edge_start_ratio and WATER_EDGE_PERCENT > 0:
                    edge_factor = (dist_ratio - edge_start_ratio) / WATER_EDGE_PERCENT
                    elevation -= edge_factor * 0.8 # Make edges water

                temp = temperature_map[y][x]
                moisture = moisture_map[y][x]

                # Determine Terrain Type
                if elevation < ELEVATION_THRESHOLD:
                    terrain_type = TERRAIN_WATER
                    if temp < TEMP_THRESHOLD_LOW - 0.1: terrain_type = TERRAIN_ICE
                else: terrain_type = TERRAIN_GROUND

                # Determine Biome
                biome = BIOME_WATER
                if terrain_type == TERRAIN_GROUND:
                    if temp < TEMP_THRESHOLD_LOW: biome = BIOME_ARCTIC
                    elif temp > TEMP_THRESHOLD_HIGH and moisture < MOISTURE_THRESHOLD_LOW: biome = BIOME_DESERT
                    elif moisture > MOISTURE_THRESHOLD_HIGH: biome = BIOME_FOREST
                    else: biome = BIOME_FOREST # Default ground biome
                elif terrain_type == TERRAIN_ICE: biome = BIOME_ARCTIC

                self.tiles[y][x] = Tile(x, y, terrain_type, biome)

        self._place_initial_resources()
        print("Map generation complete.")

    def _generate_noise_map(self, seed_offset: int) -> list[list[float]]:
        """Generates a 2D noise map using Perlin noise."""
        map_data = [[0.0 for _ in range(self.diameter)] for _ in range(self.diameter)]
        for y in range(self.diameter):
            for x in range(self.diameter):
                map_data[y][x] = noise.pnoise2(
                    x * NOISE_SCALE, y * NOISE_SCALE,
                    octaves=NOISE_OCTAVES, persistence=NOISE_PERSISTENCE,
                    lacunarity=NOISE_LACUNARITY, base=seed_offset
                )
        return map_data

    def _place_initial_resources(self):
        """Places starting resources based on biome."""
        print("Placing initial resources...")
        for y in range(self.diameter):
            for x in range(self.diameter):
                tile = self.tiles[y][x]
                if tile and tile.terrain_type == TERRAIN_GROUND:
                    prob = random.random()
                    res_type = RESOURCE_NONE
                    min_r, max_r = 0, 0
                    amount_mod = 1.0

                    if tile.biome == BIOME_FOREST:
                        if prob < RESOURCE_SPAWN_DENSITY * 2.5:
                             res_type = RESOURCE_WOOD if random.random() < 0.7 else RESOURCE_FOOD
                    elif tile.biome == BIOME_DESERT:
                        if prob < RESOURCE_SPAWN_DENSITY * 1.8:
                             res_type = RESOURCE_STONE if random.random() < 0.6 else RESOURCE_IRON
                    elif tile.biome == BIOME_ARCTIC:
                         if prob < RESOURCE_SPAWN_DENSITY * 0.3:
                             res_type = RESOURCE_STONE
                             amount_mod = 0.5

                    if res_type != RESOURCE_NONE and res_type in RESOURCE_BASE_AMOUNT:
                        min_r, max_r = RESOURCE_BASE_AMOUNT[res_type]
                        amount = random.randint(int(min_r * amount_mod), int(max_r * amount_mod))
                        tile.set_resource(res_type, max(1, amount))

        print("Resource placement finished.")

    def get_tile(self, x: int, y: int) -> Tile | None:
        """Safely retrieves a tile at given grid coordinates."""
        if 0 <= x < self.diameter and 0 <= y < self.diameter:
            return self.tiles[y][x]
        return None

    def get_random_walkable_tile(self, avoid_edge_percent=0.2) -> Tile | None:
        """Finds a random suitable starting tile."""
        attempts = 0; max_attempts = 1000
        min_dist_ratio = 0.0; max_dist_ratio = 1.0 - avoid_edge_percent
        center_x, center_y = self.radius, self.radius

        while attempts < max_attempts:
            x = random.randint(0, self.diameter - 1); y = random.randint(0, self.diameter - 1)
            tile = self.get_tile(x, y)
            if tile and tile.walkable and tile.building is None and tile.resource_type == RESOURCE_NONE:
                dist_ratio = math.sqrt((x - center_x)**2 + (y - center_y)**2) / max(1, self.radius)
                if min_dist_ratio <= dist_ratio <= max_dist_ratio: return tile
            attempts += 1

        print("Warning: Random suitable starting tile search failed, performing grid search...")
        search_radius = int(self.radius * max_dist_ratio)
        for r in range(search_radius + 1):
            for dx in range(-r, r + 1):
                 for dy in range(-r, r + 1):
                     if abs(dx) < r and abs(dy) < r: continue
                     x, y = center_x + dx, center_y + dy
                     if 0 <= x < self.diameter and 0 <= y < self.diameter:
                         tile = self.tiles[y][x]
                         if tile.walkable and tile.building is None and tile.resource_type == RESOURCE_NONE:
                             print(f"Fallback search found tile at ({x},{y}).")
                             return tile

        print("CRITICAL ERROR: Could not find ANY walkable starting tile!")
        return None

    def find_nearest_resource(self, start_x: int, start_y: int, resource_type: int, max_search_radius=20) -> Tile | None:
        """Finds the nearest tile with the specified resource using BFS."""
        if resource_type == RESOURCE_NONE: return None
        q = collections.deque([(start_x, start_y, 0)]); visited = set([(start_x, start_y)])
        while q:
            x, y, dist = q.popleft()
            if dist >= max_search_radius: continue
            tile = self.get_tile(x, y)
            if tile and tile.resource_type == resource_type and tile.resource_amount > 0: return tile
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (nx, ny) not in visited:
                    neighbor_tile = self.get_tile(nx, ny)
                    if neighbor_tile:
                        can_path = neighbor_tile.walkable or \
                                   (neighbor_tile.resource_type == resource_type and neighbor_tile.resource_amount > 0)
                        if can_path: visited.add((nx, ny)); q.append((nx, ny, dist + 1))
        return None

    def find_nearest_building(self, start_x: int, start_y: int, building_type: int, max_search_radius=40) -> Building | None:
        """
        Finds the nearest building of the specified type using BFS.
        Allows pathing through walkable tiles OR the target building tile itself.
        """
        q = collections.deque([(start_x, start_y, 0)])
        visited = set([(start_x, start_y)])
        while q:
            x, y, dist = q.popleft()
            if dist >= max_search_radius: continue

            tile = self.get_tile(x, y)
            # Check if current tile has the target building
            if tile and tile.building and tile.building.type == building_type:
                return tile.building # Found it

            # Explore neighbors
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (nx, ny) not in visited:
                     neighbor_tile = self.get_tile(nx, ny)
                     if neighbor_tile:
                         # --- MODIFIED BFS PATHING LOGIC ---
                         # Can path through walkable tiles OR the specific target building tile
                         is_target_building_tile = (neighbor_tile.building and
                                                    neighbor_tile.building.type == building_type)
                         if neighbor_tile.walkable or is_target_building_tile:
                         # --- END MODIFICATION ---
                            visited.add((nx, ny))
                            q.append((nx, ny, dist + 1))
        return None # Not found


    def mark_for_respawn(self, x: int, y: int):
        """Adds a depleted tile's coordinates to the set needing respawn checks."""
        if 0 <= x < self.diameter and 0 <= y < self.diameter:
            tile = self.get_tile(x, y)
            if tile and tile.resource_original_type != RESOURCE_NONE and tile.resource_type == RESOURCE_NONE:
                self.pending_respawn_tiles.add((x, y))

    def update_respawns(self, dt_ms_simulated: float, respawn_rate_modifier: float):
        """Checks tiles marked for respawn, manages timers, and respawns resources."""
        if not self.pending_respawn_tiles: return

        processed_coords = set()
        for x, y in list(self.pending_respawn_tiles): # Iterate copy
            tile = self.get_tile(x, y)
            if not tile: processed_coords.add((x,y)); continue

            is_eligible = (tile.terrain_type == TERRAIN_GROUND and
                           tile.building is None and
                           tile.resource_type == RESOURCE_NONE and
                           tile.resource_original_type != RESOURCE_NONE)

            if not is_eligible:
                tile.resource_respawn_timer = 0; tile.resource_original_type = RESOURCE_NONE
                processed_coords.add((x, y)); continue

            if tile.resource_respawn_timer <= 0: tile.start_respawn_timer(respawn_rate_modifier)

            if tile.resource_respawn_timer > 0:
                if tile.update_respawn_timer(dt_ms_simulated):
                     tile.respawn_resource() # Handles internal state reset
                     processed_coords.add((x, y))

        self.pending_respawn_tiles -= processed_coords

    def draw(self, surface, camera_x: int, camera_y: int):
        """Draws the visible portion of the map's tiles and resources."""
        import pygame
        start_col = max(0, camera_x // TILE_SIZE)
        end_col = min(self.diameter, (camera_x + GAME_AREA_WIDTH) // TILE_SIZE + 2)
        start_row = max(0, camera_y // TILE_SIZE)
        end_row = min(self.diameter, (camera_y + SCREEN_HEIGHT) // TILE_SIZE + 2)

        for y in range(start_row, end_row):
            for x in range(start_col, end_col):
                tile = self.get_tile(x, y)
                if tile: tile.draw(surface, camera_x, camera_y)