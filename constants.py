# constants.py
# NOTE: No 'import pygame' needed here if only defining constants.
# pygame is needed if you use pygame *objects* like Rect, Color, etc. directly.
# We use tuples for colors, so pygame import is removed.

# Screen Dimensions
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
SIDE_PANEL_WIDTH = 200
GAME_AREA_WIDTH = SCREEN_WIDTH - SIDE_PANEL_WIDTH

# Tile Settings
TILE_SIZE = 32

# Colors (using tuples)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
RED = (200, 0, 0)
DARK_RED = (100, 0, 0)
GREEN = (0, 200, 0)
BLUE = (50, 100, 200) # Water
DARK_BLUE = (0, 0, 139) # Deep Water edge / UI Panel
GREEN_FOREST_1 = (34, 139, 34) # Forest Green 1
GREEN_FOREST_2 = (0, 100, 0)   # Forest Green 2
GREEN_GRASS = (124, 252, 0) # Brighter Grass for contrast / HP Bar
BEIGE_DESERT_1 = (245, 245, 220) # Beige Sand 1
BROWN_DESERT_2 = (210, 180, 140) # Tan Sand 2
BROWN_STONE = (139, 69, 19) # For Stone resource hint / House color
SILVER_ARCTIC_1 = (192, 192, 192) # Silver
WHITE_ARCTIC_2 = (240, 248, 255) # Alice Blue (Snow)
CYAN_ICE = (175, 238, 238) # Pale Turquoise (Ice)
YELLOW_GOLD = (255, 215, 0) # For Iron resource hint
ORANGE_TOWNHALL = (255, 165, 0) # Town Hall color

# Terrain Types
TERRAIN_GROUND = 0
TERRAIN_WATER = 1
TERRAIN_ICE = 2 # Walkable water in Arctic

# Biomes
BIOME_NONE = 0 # Should not happen on generated tiles
BIOME_FOREST = 1
BIOME_DESERT = 2
BIOME_ARCTIC = 3
BIOME_WATER = 4

# Resources
RESOURCE_NONE = 0
RESOURCE_WOOD = 1 # From trees
RESOURCE_FOOD = 2 # From trees/bushes
RESOURCE_STONE = 3 # From quarries
RESOURCE_IRON = 4  # From quarries

RESOURCE_COLORS = {
    RESOURCE_WOOD: BROWN_STONE,
    RESOURCE_FOOD: GREEN_GRASS,
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
# Base amount range for newly spawned/respawned resources
RESOURCE_BASE_AMOUNT = {
    RESOURCE_WOOD: (40, 60),
    RESOURCE_FOOD: (25, 40),
    RESOURCE_STONE: (80, 120),
    RESOURCE_IRON: (60, 100),
}
RESOURCE_RESPAWN_TIME_BASE = 30 * 1000 # 30 seconds in milliseconds
RESOURCE_SPAWN_DENSITY = 0.12 # Probability factor for resource spawning

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
BUILDING_HP = {
    BUILDING_TOWNHALL: 500,
    BUILDING_HOUSE: 100,
}
HOUSE_POP_BONUS = 5

# Units
UNIT_WORKER = 1
UNIT_ENEMY_BASIC = 2

# Worker Constants
WORKER_HP = 25
WORKER_CAPACITY = 10
WORKER_GATHER_RATE = 1 # amount per gather action
WORKER_GATHER_TIME = 500 # ms per gather action
WORKER_SPEED = 1.8 # tiles per second
WORKER_SPAWN_TIME = 10 * 1000 # ms

# Enemy Constants
ENEMY_HP = 50
ENEMY_DAMAGE = 5
ENEMY_ATTACK_RATE = 1000 # ms between attacks
ENEMY_SPAWN_TIME_BASE = 20 * 1000 # ms
ENEMY_SPEED = 1.2 # tiles per second
ENEMY_SCAN_RADIUS_SQ = (15 * TILE_SIZE) ** 2 # Squared pixel distance

# Initial Game Settings
INITIAL_RESOURCES = {'Wood': 100, 'Food': 100, 'Stone': 50, 'Iron': 10, 'Water': 100}
INITIAL_POPULATION_CAP = 5
FOOD_CONSUMPTION_RATE_BASE = 0.1 # Per person per second
WATER_CONSUMPTION_RATE_BASE = 0.05 # Per person per second

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

# UI Constants
UI_DEFAULT_FONT_SIZE = 24
UI_SMALL_FONT_SIZE = 20
UI_SLIDER_HEIGHT = 15
UI_PADDING = 10
UI_BUTTON_SIZE = 40