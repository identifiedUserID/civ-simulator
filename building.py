# building.py
# Needs pygame for drawing
import pygame
from constants import * # Import necessary constants

class Building:
    """Base class for all buildings."""
    def __init__(self, x: int, y: int, building_type: int):
        self.x = x # Grid coordinates
        self.y = y
        self.type = building_type
        # Use BUILDING_HP dictionary from constants
        self.hp = BUILDING_HP.get(building_type, 100)
        self.max_hp = self.hp

    def draw(self, surface: pygame.Surface, camera_x: int, camera_y: int):
        """Draws the building and its HP bar."""
        screen_x = self.x * TILE_SIZE - camera_x
        screen_y = self.y * TILE_SIZE - camera_y
        size = TILE_SIZE

        # Culling
        if not pygame.Rect(screen_x, screen_y, size, size).colliderect(surface.get_rect()):
             return

        # Determine color based on type
        color = GRAY # Default
        # Use constants for colors
        if self.type == BUILDING_TOWNHALL: color = ORANGE_TOWNHALL
        elif self.type == BUILDING_HOUSE: color = BROWN_STONE

        # Draw building representation
        pygame.draw.rect(surface, color, (screen_x, screen_y, size, size))
        pygame.draw.rect(surface, BLACK, (screen_x, screen_y, size, size), 2)

        # Draw HP bar if damaged
        if self.hp < self.max_hp and self.max_hp > 0: # Avoid division by zero
            hp_ratio = max(0, self.hp / self.max_hp)
            bar_width = size * 0.8
            bar_height = 5
            bar_x = screen_x + (size - bar_width) / 2
            bar_y = screen_y - bar_height - 3

            pygame.draw.rect(surface, DARK_RED, (bar_x, bar_y, bar_width, bar_height))
            pygame.draw.rect(surface, GREEN_GRASS, (bar_x, bar_y, bar_width * hp_ratio, bar_height))


class TownHall(Building):
    """The main player building."""
    def __init__(self, x: int, y: int):
        super().__init__(x, y, BUILDING_TOWNHALL)
        self.worker_spawn_timer = 0 # Time until next worker can spawn


class House(Building):
    """Increases population capacity."""
    def __init__(self, x: int, y: int):
        super().__init__(x, y, BUILDING_HOUSE)
        # Pop cap increase handled in Game class logic