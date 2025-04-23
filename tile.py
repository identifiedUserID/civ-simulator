# tile.py
import random
# NOTE: No 'import pygame' needed here as Tile itself doesn't use pygame functions directly.
# Pygame is used by the main loop to *draw* the tile using its attributes.
from constants import * # Import necessary constants

class Tile:
    def __init__(self, x: int, y: int, terrain_type: int, biome: int):
        self.x = x # Grid coordinates
        self.y = y
        self.terrain_type = terrain_type
        self.biome = biome
        self.resource_type = RESOURCE_NONE
        self.resource_amount = 0
        self.building = None # Reference to Building object if present
        self.walkable = (terrain_type == TERRAIN_GROUND or terrain_type == TERRAIN_ICE)
        self.color = self._get_base_color()
        self.resource_color = None
        self.resource_respawn_timer = 0 # Time until this tile can respawn
        self.resource_original_type = RESOURCE_NONE # Remember what was here

    def _get_base_color(self):
        """Determines the base color of the tile based on terrain and biome."""
        if self.terrain_type == TERRAIN_WATER: return BLUE
        if self.terrain_type == TERRAIN_ICE: return CYAN_ICE
        # Ground types:
        if self.biome == BIOME_FOREST:
            return GREEN_FOREST_1 if hash(f"{self.x},{self.y}") % 2 == 0 else GREEN_FOREST_2
        if self.biome == BIOME_DESERT:
            return BEIGE_DESERT_1 if hash(f"{self.x},{self.y}") % 2 == 0 else BROWN_DESERT_2
        if self.biome == BIOME_ARCTIC:
            return SILVER_ARCTIC_1 if hash(f"{self.x},{self.y}") % 2 == 0 else WHITE_ARCTIC_2
        return GRAY # Fallback

    def set_resource(self, resource_type: int, amount: int):
        """Places a resource on the tile if possible."""
        if self.terrain_type == TERRAIN_GROUND and self.building is None:
            self.resource_type = resource_type
            self.resource_amount = amount
            if resource_type != RESOURCE_NONE:
                self.resource_color = RESOURCE_COLORS.get(resource_type)
                self.walkable = False
                self.resource_original_type = resource_type
            else: # Clearing the resource
                self.resource_color = None
                self.walkable = True
                # Don't clear original_type here, respawn logic handles it
        elif resource_type == RESOURCE_NONE: # Explicit clear allowed even if not ground
            self.resource_type = RESOURCE_NONE
            self.resource_amount = 0
            self.resource_color = None
            self.walkable = (self.terrain_type == TERRAIN_GROUND or self.terrain_type == TERRAIN_ICE)

    def set_building(self, building): # Building type hint would require forward ref or import
        """Places a building on the tile if possible. Returns True on success."""
        if self.terrain_type == TERRAIN_GROUND and self.resource_type == RESOURCE_NONE and self.building is None:
            self.building = building
            self.walkable = False
            return True
        return False

    def remove_building(self):
        """Removes a building from the tile."""
        self.building = None
        self.walkable = (self.terrain_type == TERRAIN_GROUND or self.terrain_type == TERRAIN_ICE)

    def gather_resource(self, amount_to_gather: int) -> tuple[int, int]:
        """Removes resources, returns (amount_gathered, resource_type_gathered)."""
        if self.resource_type == RESOURCE_NONE or self.resource_amount <= 0:
            return 0, RESOURCE_NONE

        gathered = min(amount_to_gather, self.resource_amount)
        self.resource_amount -= gathered
        resource_type_gathered = self.resource_type

        if self.resource_amount <= 0:
            # Depleted: clear visual/type, make walkable, keep original type for respawn
            self.resource_type = RESOURCE_NONE
            self.resource_amount = 0
            self.resource_color = None
            self.walkable = True

        return gathered, resource_type_gathered

    def start_respawn_timer(self, respawn_rate_modifier: float):
        """Initiates the countdown for resource respawn."""
        if self.resource_original_type != RESOURCE_NONE and self.resource_respawn_timer <= 0:
            # Higher modifier = faster respawn (shorter time)
            self.resource_respawn_timer = RESOURCE_RESPAWN_TIME_BASE / max(0.1, respawn_rate_modifier)

    def update_respawn_timer(self, dt_ms_simulated: float) -> bool:
        """Counts down timer. Returns True if ready to respawn."""
        if self.resource_respawn_timer > 0:
            self.resource_respawn_timer -= dt_ms_simulated
            if self.resource_respawn_timer <= 0:
                self.resource_respawn_timer = 0
                return True # Ready
        return False

    def respawn_resource(self) -> bool:
        """Respawns the original resource if tile is suitable. Returns True on success."""
        # Check if eligible: had an original resource, is currently clear ground
        if self.resource_original_type != RESOURCE_NONE and \
           self.resource_type == RESOURCE_NONE and \
           self.building is None and \
           self.terrain_type == TERRAIN_GROUND:
             # Use RESOURCE_BASE_AMOUNT (ensure it's imported via constants)
             if self.resource_original_type in RESOURCE_BASE_AMOUNT:
                min_amount, max_amount = RESOURCE_BASE_AMOUNT[self.resource_original_type]
                amount = random.randint(min_amount, max_amount)
                self.set_resource(self.resource_original_type, amount)
                self.resource_original_type = RESOURCE_NONE # Clear original type after respawn
                return True
             else:
                 print(f"Warning: Respawn failed, resource type {self.resource_original_type} not in RESOURCE_BASE_AMOUNT.")
                 self.resource_original_type = RESOURCE_NONE # Forget it
                 return False

        # Not eligible (blocked, wrong terrain, etc.)
        if self.resource_original_type != RESOURCE_NONE:
            # If it had an original type but couldn't respawn, forget it
             self.resource_original_type = RESOURCE_NONE
        return False

    def draw(self, surface, camera_x: int, camera_y: int):
        """Draws the base tile and resource indicator."""
        # Needs pygame for drawing functions, but called externally.
        # We'll assume pygame is initialized and surface is valid.
        import pygame # Local import only needed if using pygame types/functions here

        screen_x = self.x * TILE_SIZE - camera_x
        screen_y = self.y * TILE_SIZE - camera_y

        # Culling
        if screen_x + TILE_SIZE < 0 or screen_x > GAME_AREA_WIDTH or \
           screen_y + TILE_SIZE < 0 or screen_y > SCREEN_HEIGHT:
            return

        pygame.draw.rect(surface, self.color, (screen_x, screen_y, TILE_SIZE, TILE_SIZE))

        # Draw resource indicator
        if self.resource_type != RESOURCE_NONE and self.resource_color:
            center_x = screen_x + TILE_SIZE // 2
            center_y = screen_y + TILE_SIZE // 2
            radius = max(2, TILE_SIZE // 5)
            pygame.draw.circle(surface, BLACK, (center_x, center_y), radius + 1) # Outline
            pygame.draw.circle(surface, self.resource_color, (center_x, center_y), radius)

        # Optional grid lines for debugging
        # pygame.draw.rect(surface, BLACK, (screen_x, screen_y, TILE_SIZE, TILE_SIZE), 1)