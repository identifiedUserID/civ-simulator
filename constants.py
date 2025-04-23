# constants.py
import pygame

# Screen Dimensions
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
SIDE_PANEL_WIDTH = 200
GAME_AREA_WIDTH = SCREEN_WIDTH - SIDE_PANEL_WIDTH

# Tile Settings
TILE_SIZE = 32

# Colors (using more distinct shades)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
RED = (200, 0, 0)
BLUE = (50, 100, 200) # Water
DARK_BLUE = (0, 0, 139) # Deep Water edge
GREEN_FOREST_1 = (34, 139, 34) # Forest Green 1
GREEN_FOREST_2 = (0, 100, 0)   # Forest Green 2
GREEN_GRASS = (124, 252, 0) # Brighter Grass for contrast
BEIGE_DESERT_1 = (245, 245, 220) # Beige Sand 1
BROWN_DESERT_2 = (210, 180, 140) # Tan Sand 2
BROWN_STONE = (139, 69, 19) # For Stone resource hint
SILVER_ARCTIC_1 = (192, 192, 192) # Silver
WHITE_ARCTIC_2 = (240, 248, 255) # Alice Blue (Snow)
CYAN_ICE = (175, 238, 238) # Pale Turquoise (Ice)
YELLOW_GOLD = (255, 215, 0) # For Iron resource hint

# Terrain Types
TERRAIN_GROUND = 0
TERRAIN_WATER = 1
TERRAIN_ICE = 2 # Walkable water in Arctic

# Biomes
BIOME_NONE = 0
BIOME_FOREST = 1
BIOME_DESERT = 2
BIOME_ARCTIC = 3
BIOME_WATER = 4

# Resources
RESOURCE_NONE = 0
RESOURCE_WOOD = 1 # From trees
RESOURCE_FOOD = 2 # From trees/bushes (can be same visual as wood for now)
RESOURCE_STONE = 3 # From quarries
RESOURCE_IRON = 4  # From quarries

RESOURCE_COLORS = {
    RESOURCE_WOOD: BROWN_STONE, # Tree trunk color
    RESOURCE_FOOD: GREEN_GRASS, # Bushy color
    RESOURCE_STONE: GRAY,
    RESOURCE_IRON: YELLOW_GOLD,
}
RESOURCE_NAMES = {
    RESOURCE_NONE: "None",
    RESOURCE_WOOD: "Wood",
    RESOURCE_FOOD: "Food",
    RESOURCE_STONE: "Stone",
    RESOURCE_IRON: "Iron",
}
RESOURCE_START_AMOUNT = {
    RESOURCE_WOOD: 50,
    RESOURCE_FOOD: 30,
    RESOURCE_STONE: 100,
    RESOURCE_IRON: 80,
}
RESOURCE_RESPAWN_TIME_BASE = 30 * 1000 # 30 seconds in milliseconds

# Buildings
BUILDING_TOWNHALL = 1
BUILDING_HOUSE = 2

BUILDING_COSTS = {
    BUILDING_HOUSE: {'Wood': 50}
}

BUILDING_NAMES = {
    BUILDING_TOWNHALL: "Town Hall",
    BUILDING_HOUSE: "House"
}

# Units
UNIT_WORKER = 1
UNIT_ENEMY_BASIC = 2

# Worker Constants
WORKER_CAPACITY = 10
WORKER_GATHER_RATE = 1 # amount per tick
WORKER_GATHER_TIME = 500 # ms per gather action
WORKER_SPEED = 1.5 # tiles per second (adjust with simulation speed)
WORKER_SPAWN_TIME = 10 * 1000 # ms

# Enemy Constants
ENEMY_SPAWN_TIME_BASE = 20 * 1000 # ms
ENEMY_SPEED = 1.0
ENEMY_HP = 50
ENEMY_DAMAGE = 5
ENEMY_ATTACK_RATE = 1000 # ms

# Initial Game Settings
INITIAL_RESOURCES = {'Wood': 100, 'Food': 100, 'Stone': 50, 'Iron': 10}
INITIAL_POPULATION_CAP = 5
FOOD_CONSUMPTION_RATE_BASE = 0.1 # Per person per second
WATER_CONSUMPTION_RATE_BASE = 0.05 # Per person per second (Adding water tracking)

# Map Generation Constants
NOISE_SCALE = 0.03 # Lower = larger features
NOISE_OCTAVES = 4
NOISE_PERSISTENCE = 0.5
NOISE_LACUNARITY = 2.0
ELEVATION_THRESHOLD = 0.0 # Noise values above this are land
WATER_EDGE_PERCENT = 0.10 # Last 10% radius is mostly water
TEMP_THRESHOLD_LOW = -0.2 # For Arctic
TEMP_THRESHOLD_HIGH = 0.3 # For Desert
MOISTURE_THRESHOLD_LOW = -0.1 # For Desert
MOISTURE_THRESHOLD_HIGH = 0.1 # For Forest