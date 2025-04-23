# tile.py
import pygame
from constants import *

class Tile:
    def __init__(self, x, y, terrain_type, biome):
        self.x = x
        self.y = y
        self.grid_x = x
        self.grid_y = y
        self.terrain_type = terrain_type
        self.biome = biome
        self.resource_type = RESOURCE_NONE
        self.resource_amount = 0
        self.building = None
        self.walkable = (terrain_type == TERRAIN_GROUND or terrain_type == TERRAIN_ICE)
        self.color = self._get_base_color()
        self.resource_color = None
        self.respawn_timer = 0 # Timer for resource respawn

    def _get_base_color(self):
        if self.terrain_type == TERRAIN_WATER:
            return BLUE
        elif self.terrain_type == TERRAIN_ICE:
            return CYAN_ICE
        else: # Ground
            if self.biome == BIOME_FOREST:
                return GREEN_FOREST_1 if (self.x + self.y) % 2 == 0 else GREEN_FOREST_2
            elif self.biome == BIOME_DESERT:
                return BEIGE_DESERT_1 if (self.x + self.y) % 2 == 0 else BROWN_DESERT_2
            elif self.biome == BIOME_ARCTIC:
                 return SILVER_ARCTIC_1 if (self.x + self.y) % 2 == 0 else WHITE_ARCTIC_2
            else:
                return GRAY # Should not happen often

    def set_resource(self, resource_type, amount):
        if self.terrain_type == TERRAIN_GROUND and self.building is None:
            self.resource_type = resource_type
            self.resource_amount = amount
            self.resource_color = RESOURCE_COLORS.get(resource_type)
            self.walkable = False # Can't walk through resources initially
        elif resource_type == RESOURCE_NONE:
             self.resource_type = RESOURCE_NONE
             self.resource_amount = 0
             self.resource_color = None
             self.walkable = (self.terrain_type == TERRAIN_GROUND or self.terrain_type == TERRAIN_ICE)


    def set_building(self, building):
        if self.terrain_type == TERRAIN_GROUND and self.resource_type == RESOURCE_NONE:
            self.building = building
            self.walkable = False
            return True
        return False

    def remove_building(self):
        self.building = None
        self.walkable = True # Assuming ground underneath

    def gather_resource(self, amount):
        gathered = min(amount, self.resource_amount)
        self.resource_amount -= gathered
        if self.resource_amount <= 0:
            # Start respawn timer when depleted
            original_type = self.resource_type
            self.set_resource(RESOURCE_NONE, 0) # Clear resource visually
            self.walkable = True # Can walk here now
            return gathered, original_type # Return original type for respawn tracking
        return gathered, self.resource_type

    def start_respawn(self, respawn_time_modifier):
        base_time = RESOURCE_RESPAWN_TIME_BASE
        self.respawn_timer = base_time / respawn_time_modifier # Higher modifier = faster respawn

    def update_respawn(self, dt_ms):
        if self.respawn_timer > 0:
            self.respawn_timer -= dt_ms
            if self.respawn_timer <= 0:
                return True # Ready to respawn
        return False

    def draw(self, surface, camera_x, camera_y):
        screen_x = self.x * TILE_SIZE - camera_x
        screen_y = self.y * TILE_SIZE - camera_y

        # Basic culling
        if screen_x + TILE_SIZE < 0 or screen_x > GAME_AREA_WIDTH or \
           screen_y + TILE_SIZE < 0 or screen_y > SCREEN_HEIGHT:
            return

        pygame.draw.rect(surface, self.color, (screen_x, screen_y, TILE_SIZE, TILE_SIZE))

        # Draw resource indicator (small circle)
        if self.resource_type != RESOURCE_NONE and self.resource_color:
            center_x = screen_x + TILE_SIZE // 2
            center_y = screen_y + TILE_SIZE // 2
            pygame.draw.circle(surface, self.resource_color, (center_x, center_y), TILE_SIZE // 4)

        # Draw border for debugging (optional)
        # pygame.draw.rect(surface, BLACK, (screen_x, screen_y, TILE_SIZE, TILE_SIZE), 1)

    def draw_building_or_unit(self, surface, camera_x, camera_y):
        # Buildings and units are drawn separately after the base tiles
         screen_x = self.x * TILE_SIZE - camera_x
         screen_y = self.y * TILE_SIZE - camera_y

         # Basic culling
         if screen_x + TILE_SIZE < 0 or screen_x > GAME_AREA_WIDTH or \
            screen_y + TILE_SIZE < 0 or screen_y > SCREEN_HEIGHT:
             return

         if self.building:
             self.building.draw(surface, camera_x, camera_y)
