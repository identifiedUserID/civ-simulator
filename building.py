# building.py
import pygame
from constants import *

class Building:
    def __init__(self, x, y, building_type):
        self.x = x # Grid coordinates
        self.y = y
        self.type = building_type
        self.hp = 100 # Example HP

    def draw(self, surface, camera_x, camera_y):
        screen_x = self.x * TILE_SIZE - camera_x
        screen_y = self.y * TILE_SIZE - camera_y

        # Basic culling
        if screen_x + TILE_SIZE < 0 or screen_x > GAME_AREA_WIDTH or \
           screen_y + TILE_SIZE < 0 or screen_y > SCREEN_HEIGHT:
            return

        color = GRAY # Default building color
        if self.type == BUILDING_TOWNHALL:
            color = (255, 165, 0) # Orange
        elif self.type == BUILDING_HOUSE:
            color = (139, 69, 19) # Brown

        pygame.draw.rect(surface, color, (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
        pygame.draw.rect(surface, BLACK, (screen_x, screen_y, TILE_SIZE, TILE_SIZE), 2) # Border

class TownHall(Building):
    def __init__(self, x, y):
        super().__init__(x, y, BUILDING_TOWNHALL)
        self.worker_spawn_timer = 0
        self.spawn_point = (x + 1, y) # Example spawn adjacent

class House(Building):
    def __init__(self, x, y):
        super().__init__(x, y, BUILDING_HOUSE)
        # Houses increase population cap in the main game logic