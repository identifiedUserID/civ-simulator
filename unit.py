# unit.py
import pygame
import random
import math
from constants import *

class Unit:
    def __init__(self, x, y, unit_type, game_speed_modifier=1.0):
        # Store position as float for smoother movement between tiles
        self.x = float(x * TILE_SIZE + TILE_SIZE / 2)
        self.y = float(y * TILE_SIZE + TILE_SIZE / 2)
        self.grid_x = x
        self.grid_y = y
        self.type = unit_type
        self.target = None # Target coordinates (grid_x, grid_y) or object
        self.state = 'idle' # idle, moving, gathering, returning, attacking
        self.speed = 0.0
        self.game_speed_modifier = game_speed_modifier # Store reference

    def update_grid_pos(self):
        self.grid_x = int(self.x // TILE_SIZE)
        self.grid_y = int(self.y // TILE_SIZE)

    def move_towards(self, target_x, target_y, dt):
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.sqrt(dx**2 + dy**2)

        if dist < TILE_SIZE / 4: # Close enough to target center
             return True # Arrived

        # Normalize
        dx /= dist
        dy /= dist

        effective_speed = self.speed * TILE_SIZE * self.game_speed_modifier * dt
        self.x += dx * effective_speed
        self.y += dy * effective_speed
        self.update_grid_pos()
        return False # Still moving

    def draw(self, surface, camera_x, camera_y):
        screen_x = int(self.x - camera_x)
        screen_y = int(self.y - camera_y)
        radius = TILE_SIZE // 3

        # Culling
        if screen_x + radius < 0 or screen_x - radius > GAME_AREA_WIDTH or \
           screen_y + radius < 0 or screen_y - radius > SCREEN_HEIGHT:
           return

        color = WHITE # Default
        if self.type == UNIT_WORKER:
            color = (0, 200, 0) # Green
        elif self.type == UNIT_ENEMY_BASIC:
             color = RED

        pygame.draw.circle(surface, color, (screen_x, screen_y), radius)


class Worker(Unit):
    def __init__(self, x, y, game_speed_modifier):
        super().__init__(x, y, UNIT_WORKER, game_speed_modifier)
        self.speed = WORKER_SPEED
        self.resource_carried = RESOURCE_NONE
        self.carry_amount = 0
        self.target_tile = None # Reference to the target Tile object
        self.gather_timer = 0
        self.preferred_resource_order = [RESOURCE_FOOD, RESOURCE_WOOD, RESOURCE_STONE, RESOURCE_IRON] # Example order

    def update(self, dt, game_map, buildings, resources):
        """Worker AI Logic"""
        dt_ms = dt * 1000

        if self.state == 'idle':
            # If carrying resources, find town hall
            if self.carry_amount > 0:
                self.find_town_hall_and_return(game_map, buildings)
            else:
                # Find nearby resource
                found_resource = False
                for res_type in self.preferred_resource_order:
                     # Prioritize needed resources? Maybe later.
                     target_tile = game_map.find_nearest_resource(self.grid_x, self.grid_y, res_type)
                     if target_tile:
                         self.target_tile = target_tile
                         self.target = (target_tile.x, target_tile.y)
                         self.state = 'moving_to_resource'
                         #print(f"Worker at ({self.grid_x},{self.grid_y}) moving to {RESOURCE_NAMES[res_type]} at ({target_tile.x},{target_tile.y})")
                         found_resource = True
                         break
                if not found_resource:
                    # Wander randomly? Or just stay idle.
                    pass

        elif self.state == 'moving_to_resource':
            if self.target_tile and self.target_tile.resource_amount > 0:
                target_center_x = self.target[0] * TILE_SIZE + TILE_SIZE / 2
                target_center_y = self.target[1] * TILE_SIZE + TILE_SIZE / 2
                if self.move_towards(target_center_x, target_center_y, dt):
                    self.state = 'gathering'
                    self.gather_timer = WORKER_GATHER_TIME
            else:
                # Target disappeared or became invalid
                self.state = 'idle'
                self.target = None
                self.target_tile = None

        elif self.state == 'gathering':
            self.gather_timer -= dt_ms * self.game_speed_modifier
            if self.gather_timer <= 0:
                if self.target_tile and self.target_tile.resource_amount > 0:
                    gathered, res_type_gathered = self.target_tile.gather_resource(WORKER_GATHER_RATE)
                    if gathered > 0:
                        # If starting to carry or switching type, set it
                        if self.carry_amount == 0:
                            self.resource_carried = res_type_gathered
                        # Add to carried amount if it's the same type
                        if self.resource_carried == res_type_gathered:
                             self.carry_amount += gathered
                             #print(f"Gathered {gathered} {RESOURCE_NAMES[self.resource_carried]}, carrying {self.carry_amount}")
                        else:
                             # Cannot mix resources, drop off first (should ideally happen)
                             self.find_town_hall_and_return(game_map, buildings)

                    # If resource depleted or worker full, return
                    if self.target_tile.resource_amount <= 0 or self.carry_amount >= WORKER_CAPACITY:
                        if self.target_tile.resource_amount <= 0:
                             # Mark tile for respawn tracking in the map
                             coords = (self.target_tile.x, self.target_tile.y)
                             if coords not in game_map.depleted_resources:
                                 game_map.depleted_resources[coords] = res_type_gathered # Store original type
                                 self.target_tile.respawn_timer = 1 # Needs > 0 to start ticking down

                        self.find_town_hall_and_return(game_map, buildings)
                    else:
                         # Continue gathering
                         self.gather_timer = WORKER_GATHER_TIME
                else:
                    # Resource gone while gathering? Return or find new one
                     self.find_town_hall_and_return(game_map, buildings) # Prioritize return if carrying anything

        elif self.state == 'moving_to_townhall':
            if self.target:
                target_center_x = self.target[0] * TILE_SIZE + TILE_SIZE / 2
                target_center_y = self.target[1] * TILE_SIZE + TILE_SIZE / 2
                if self.move_towards(target_center_x, target_center_y, dt):
                     self.state = 'dropping_off'
            else: # Target lost? Find again or idle
                self.find_town_hall_and_return(game_map, buildings)
                if self.state != 'moving_to_townhall': # If couldn't find one
                    self.state = 'idle'


        elif self.state == 'dropping_off':
            if self.resource_carried != RESOURCE_NONE and self.carry_amount > 0:
                resource_name = RESOURCE_NAMES.get(self.resource_carried)
                if resource_name and resource_name != "None":
                     resources[resource_name] += self.carry_amount
                     #print(f"Dropped off {self.carry_amount} {resource_name}. Total: {resources}")
                self.carry_amount = 0
                self.resource_carried = RESOURCE_NONE
            self.state = 'idle' # Look for new task

    def find_town_hall_and_return(self, game_map, buildings):
        # Find nearest Town Hall to drop off resources
        town_hall = game_map.find_nearest_building(self.grid_x, self.grid_y, BUILDING_TOWNHALL)
        if town_hall:
            self.target = (town_hall.x, town_hall.y)
            self.state = 'moving_to_townhall'
            #print(f"Worker at ({self.grid_x},{self.grid_y}) returning to TH at ({town_hall.x},{town_hall.y})")
        else:
             # No town hall? Panic! Or just idle.
             self.state = 'idle'
             self.target = None
             self.target_tile = None


class Enemy(Unit):
    def __init__(self, x, y, game_speed_modifier):
        super().__init__(x, y, UNIT_ENEMY_BASIC, game_speed_modifier)
        self.speed = ENEMY_SPEED
        self.hp = ENEMY_HP
        self.damage = ENEMY_DAMAGE
        self.attack_rate = ENEMY_ATTACK_RATE
        self.attack_timer = 0
        self.target_unit_or_building = None

    def update(self, dt, game_map, buildings, workers):
        dt_ms = dt * 1000 * self.game_speed_modifier
        self.attack_timer -= dt_ms

        if self.state == 'idle':
            # Scan for targets (workers or buildings)
            self.target_unit_or_building = self.find_target(workers, buildings)
            if self.target_unit_or_building:
                self.state = 'moving_to_target'
            else:
                 # Wander randomly? (simple version: stay idle)
                 pass

        elif self.state == 'moving_to_target':
             if self.target_unit_or_building and self.target_unit_or_building.hp > 0: # Target still valid?
                 # Simplistic target coords - needs better handling for moving targets
                 target_x_px = 0
                 target_y_px = 0
                 if isinstance(self.target_unit_or_building, Unit):
                     target_x_px = self.target_unit_or_building.x
                     target_y_px = self.target_unit_or_building.y
                 elif isinstance(self.target_unit_or_building, Building):
                     target_x_px = self.target_unit_or_building.x * TILE_SIZE + TILE_SIZE / 2
                     target_y_px = self.target_unit_or_building.y * TILE_SIZE + TILE_SIZE / 2

                 # Check distance for attack range instead of moving exactly on top
                 dx = target_x_px - self.x
                 dy = target_y_px - self.y
                 dist_sq = dx**2 + dy**2

                 attack_range = TILE_SIZE * 1.1 # Attack if slightly more than 1 tile away

                 if dist_sq < attack_range**2:
                     self.state = 'attacking'
                 else:
                     # Move towards target
                     if not self.move_towards(target_x_px, target_y_px, dt):
                         pass # Still moving
                     else: # Arrived at approx location, switch to attack
                        self.state = 'attacking'

             else: # Target lost or destroyed
                 self.state = 'idle'
                 self.target_unit_or_building = None

        elif self.state == 'attacking':
            if self.target_unit_or_building and self.target_unit_or_building.hp > 0:
                # Check range again, maybe target moved
                target_x_px = 0
                target_y_px = 0
                if isinstance(self.target_unit_or_building, Unit):
                     target_x_px = self.target_unit_or_building.x
                     target_y_px = self.target_unit_or_building.y
                elif isinstance(self.target_unit_or_building, Building):
                    target_x_px = self.target_unit_or_building.x * TILE_SIZE + TILE_SIZE / 2
                    target_y_px = self.target_unit_or_building.y * TILE_SIZE + TILE_SIZE / 2

                dx = target_x_px - self.x
                dy = target_y_px - self.y
                dist_sq = dx**2 + dy**2
                attack_range = TILE_SIZE * 1.2 # Slightly larger range check when attacking

                if dist_sq > attack_range**2:
                    # Target moved out of range
                    self.state = 'moving_to_target'
                elif self.attack_timer <= 0:
                    # Attack!
                    print(f"Enemy at ({self.grid_x},{self.grid_y}) attacking target!")
                    self.target_unit_or_building.hp -= self.damage
                    print(f"Target HP: {self.target_unit_or_building.hp}")
                    if self.target_unit_or_building.hp <= 0:
                        print("Target destroyed!")
                        # Target cleanup happens in main game loop
                        self.state = 'idle'
                        self.target_unit_or_building = None
                    self.attack_timer = self.attack_rate # Reset timer
            else: # Target lost or destroyed
                self.state = 'idle'
                self.target_unit_or_building = None


    def find_target(self, workers, buildings, scan_radius_sq=15**2 * TILE_SIZE**2):
         """Find nearest worker or building"""
         nearest_target = None
         min_dist_sq = scan_radius_sq

         # Check workers
         for worker in workers:
             dx = worker.x - self.x
             dy = worker.y - self.y
             dist_sq = dx**2 + dy**2
             if dist_sq < min_dist_sq:
                 min_dist_sq = dist_sq
                 nearest_target = worker

         # Check buildings (TownHall first maybe?)
         for building in buildings:
              b_center_x = building.x * TILE_SIZE + TILE_SIZE / 2
              b_center_y = building.y * TILE_SIZE + TILE_SIZE / 2
              dx = b_center_x - self.x
              dy = b_center_y - self.y
              dist_sq = dx**2 + dy**2
              if dist_sq < min_dist_sq:
                  min_dist_sq = dist_sq
                  nearest_target = building

         return nearest_target