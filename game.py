# game.py
import pygame
import sys
import random
import math
from constants import *
from map import GameMap
from tile import Tile
from building import Building, TownHall, House
from unit import Unit, Worker, Enemy
from ui import UI

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Civ Resource/Defense Sim")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 30)

        self.map_radius = 50 # Medium size map
        self.game_map = GameMap(self.map_radius)

        self.camera_x = (self.game_map.width_pixels - GAME_AREA_WIDTH) // 2
        self.camera_y = (self.game_map.height_pixels - SCREEN_HEIGHT) // 2
        self.dragging = False
        self.drag_start_pos = None
        self.drag_start_camera = None

        self.resources = INITIAL_RESOURCES.copy()
        self.resources['Water'] = 100 # Add water tracking

        self.population = 0
        self.population_cap = INITIAL_POPULATION_CAP

        self.buildings = []
        self.workers = []
        self.enemies = []

        self.ui = UI()

        self._spawn_initial_town_hall()

        self.game_time_ms = 0
        self.last_food_consumption_time = 0
        self.last_water_consumption_time = 0
        self.last_enemy_spawn_time = 0

        # Build mode state
        self.build_mode = False
        self.building_to_place_type = None
        self.build_ghost_pos = None # Grid coords (x,y)

    def _spawn_initial_town_hall(self):
        start_tile = self.game_map.get_random_walkable_tile()
        if start_tile:
            town_hall = TownHall(start_tile.x, start_tile.y)
            if start_tile.set_building(town_hall):
                self.buildings.append(town_hall)
                print(f"Spawned Town Hall at ({start_tile.x}, {start_tile.y})")
                # Center camera roughly on town hall
                self.camera_x = start_tile.x * TILE_SIZE - GAME_AREA_WIDTH // 2
                self.camera_y = start_tile.y * TILE_SIZE - SCREEN_HEIGHT // 2
                self.clamp_camera()
            else:
                 print("Error: Could not place initial Town Hall!")
                 sys.exit() # Critical error
        else:
            print("Error: Could not find valid starting tile for Town Hall!")
            sys.exit() # Critical error

    def run(self):
        while True:
            # Calculate delta time (dt) in seconds
            # Use raw pygame ticks for timers, but dt for physics/movement
            dt_ms = self.clock.tick(60) # Limit FPS to 60
            dt = dt_ms / 1000.0 # Convert ms to seconds
            sim_speed = self.ui.sliders['sim_speed'].get_value()
            game_dt = dt * sim_speed # Game time delta

            self.game_time_ms += dt_ms * sim_speed

            self.handle_events()
            self.update(game_dt, dt_ms) # Pass both for different update needs
            self.draw()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # --- UI Event Handling ---
            ui_handled = self.ui.handle_event(event)
            if ui_handled:
                 # Check if a build button was clicked
                 if isinstance(ui_handled, int): # Returned building type
                     if not self.build_mode:
                         self.build_mode = True
                         self.building_to_place_type = ui_handled
                         print(f"Entering build mode for: {BUILDING_NAMES.get(self.building_to_place_type)}")
                     else: # Clicked again or another build button, cancel/switch
                         if self.building_to_place_type == ui_handled: # Clicked same button
                             self.build_mode = False
                             self.building_to_place_type = None
                             print("Exiting build mode.")
                         else: # Clicked different button
                             self.building_to_place_type = ui_handled
                             print(f"Switching build mode to: {BUILDING_NAMES.get(self.building_to_place_type)}")

                 continue # Don't process game world clicks if UI was interacted with

            # --- Build Mode Click Handling ---
            if self.build_mode and event.type == pygame.MOUSEBUTTONDOWN:
                 if event.button == 1: # Left click to place
                     mouse_x, mouse_y = event.pos
                     if mouse_x < GAME_AREA_WIDTH: # Clicked in game area
                         grid_x, grid_y = self.screen_to_grid(mouse_x, mouse_y)
                         if self.can_place_building(grid_x, grid_y, self.building_to_place_type):
                             self.place_building(grid_x, grid_y, self.building_to_place_type)
                             # Option: Exit build mode after placing? Or allow multiple placements?
                             # For now, exit build mode:
                             # self.build_mode = False
                             # self.building_to_place_type = None
                 elif event.button == 3: # Right click to cancel build mode
                      self.build_mode = False
                      self.building_to_place_type = None
                      print("Exiting build mode.")
                 continue # Don't process dragging etc. if in build mode click

            # --- Map Dragging ---
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and event.pos[0] < GAME_AREA_WIDTH: # Left click in game area starts drag
                    self.dragging = True
                    self.drag_start_pos = event.pos
                    self.drag_start_camera = (self.camera_x, self.camera_y)
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.dragging = False
            elif event.type == pygame.MOUSEMOTION:
                 # Update build ghost position if in build mode
                 if self.build_mode:
                    mouse_x, mouse_y = event.pos
                    if mouse_x < GAME_AREA_WIDTH:
                         self.build_ghost_pos = self.screen_to_grid(mouse_x, mouse_y)
                    else:
                        self.build_ghost_pos = None # Don't show ghost over UI
                 # Handle map dragging
                 elif self.dragging:
                    current_mouse_pos = event.pos
                    dx = current_mouse_pos[0] - self.drag_start_pos[0]
                    dy = current_mouse_pos[1] - self.drag_start_pos[1]
                    self.camera_x = self.drag_start_camera[0] - dx
                    self.camera_y = self.drag_start_camera[1] - dy
                    self.clamp_camera()


    def update(self, game_dt, dt_ms_realtime):
         sim_speed = self.ui.sliders['sim_speed'].get_value()
         consumption_mod = self.ui.sliders['consumption'].get_value()
         respawn_mod = self.ui.sliders['respawn'].get_value()
         monster_spawn_mod = self.ui.sliders['monster_spawn'].get_value()

         # --- Town Hall Logic (Worker Spawning) ---
         for building in self.buildings:
             if isinstance(building, TownHall):
                 building.worker_spawn_timer -= dt_ms_realtime * sim_speed
                 if building.worker_spawn_timer <= 0 and self.population < self.population_cap:
                     # Try to spawn adjacent to town hall
                     spawn_tile = None
                     for dx, dy in [(1,0), (-1,0), (0,1), (0,-1), (1,1), (1,-1), (-1,1), (-1,-1)]:
                         check_x, check_y = building.x + dx, building.y + dy
                         tile = self.game_map.get_tile(check_x, check_y)
                         if tile and tile.walkable and tile.building is None and tile.resource_type == RESOURCE_NONE:
                             spawn_tile = tile
                             break
                     if spawn_tile:
                         new_worker = Worker(spawn_tile.x, spawn_tile.y, sim_speed)
                         self.workers.append(new_worker)
                         self.population += 1
                         print(f"Spawned worker. Population: {self.population}/{self.population_cap}")
                         building.worker_spawn_timer = WORKER_SPAWN_TIME # Reset timer
                     else:
                         # Can't find spawn spot, try again slightly later
                         building.worker_spawn_timer = 500 # Wait 0.5 sec game time

         # --- Update Workers ---
         for worker in self.workers:
             # Pass sim_speed modifier reference for worker's internal speed calc
             worker.game_speed_modifier = sim_speed
             worker.update(game_dt, self.game_map, self.buildings, self.resources)

         # --- Resource Consumption ---
         time_since_last_food = self.game_time_ms - self.last_food_consumption_time
         if time_since_last_food >= 1000: # Check every second of game time
             food_needed = self.population * FOOD_CONSUMPTION_RATE_BASE * consumption_mod * (time_since_last_food / 1000.0)
             self.resources['Food'] = max(0, self.resources['Food'] - food_needed)
             self.last_food_consumption_time = self.game_time_ms
             # Add Water Consumption
             time_since_last_water = self.game_time_ms - self.last_water_consumption_time
             water_needed = self.population * WATER_CONSUMPTION_RATE_BASE * consumption_mod * (time_since_last_water / 1000.0)
             self.resources['Water'] = max(0, self.resources['Water'] - water_needed)
             self.last_water_consumption_time = self.game_time_ms

             # Add consequences for running out (e.g., starvation) - later

         # --- Resource Respawns ---
         self.game_map.update_respawns(dt_ms_realtime * sim_speed, respawn_mod)

         # --- Enemy Spawning ---
         time_since_last_spawn = self.game_time_ms - self.last_enemy_spawn_time
         enemy_spawn_interval = ENEMY_SPAWN_TIME_BASE / monster_spawn_mod
         if time_since_last_spawn >= enemy_spawn_interval:
              self.spawn_enemy(sim_speed)
              self.last_enemy_spawn_time = self.game_time_ms


         # --- Update Enemies ---
         dead_enemies = []
         for enemy in self.enemies:
             enemy.game_speed_modifier = sim_speed
             enemy.update(game_dt, self.game_map, self.buildings, self.workers)
             if enemy.hp <= 0:
                 dead_enemies.append(enemy)
                 print("Enemy died.")

         # Remove dead enemies
         for dead in dead_enemies:
             self.enemies.remove(dead)


         # --- Update Combat Results (Unit/Building HP checks) ---
         dead_workers = []
         for worker in self.workers:
             if worker.hp <= 0: # Workers don't have HP yet, add later if needed
                 pass # dead_workers.append(worker)

         destroyed_buildings = []
         for building in self.buildings:
              if building.hp <= 0:
                  destroyed_buildings.append(building)

         # Remove dead workers
         # for dead in dead_workers:
         #     self.workers.remove(dead)
         #     self.population -= 1
         #     print("Worker died.")

         # Remove destroyed buildings
         for destroyed in destroyed_buildings:
              tile = self.game_map.get_tile(destroyed.x, destroyed.y)
              if tile:
                  tile.remove_building()
              self.buildings.remove(destroyed)
              if isinstance(destroyed, House):
                  self.population_cap -= 5 # Assuming house adds 5 cap
              elif isinstance(destroyed, TownHall):
                   print("GAME OVER - Town Hall Destroyed!")
                   pygame.time.wait(3000)
                   pygame.quit()
                   sys.exit()
              print(f"{BUILDING_NAMES.get(destroyed.type)} destroyed.")

         # --- Update Build Ghost ---
         if self.build_mode and pygame.mouse.get_focused():
             mouse_x, mouse_y = pygame.mouse.get_pos()
             if mouse_x < GAME_AREA_WIDTH:
                 self.build_ghost_pos = self.screen_to_grid(mouse_x, mouse_y)
             else:
                 self.build_ghost_pos = None
         else:
             self.build_ghost_pos = None


    def spawn_enemy(self, sim_speed):
         # Spawn enemies near the edge of the map
         attempts = 0
         while attempts < 50:
             angle = random.uniform(0, 2 * math.pi)
             # Spawn closer to edge (e.g., 80-95% of radius)
             dist_ratio = random.uniform(0.8, 0.95)
             dist = self.map_radius * dist_ratio

             spawn_x = int(self.game_map.radius + dist * math.cos(angle))
             spawn_y = int(self.game_map.radius + dist * math.sin(angle))

             tile = self.game_map.get_tile(spawn_x, spawn_y)
             if tile and tile.walkable and tile.building is None and tile.resource_type == RESOURCE_NONE:
                 new_enemy = Enemy(spawn_x, spawn_y, sim_speed)
                 self.enemies.append(new_enemy)
                 print(f"Spawned enemy at ({spawn_x}, {spawn_y})")
                 return # Success
             attempts += 1
         # print("Could not find suitable spot to spawn enemy.")


    def clamp_camera(self):
        # Prevent camera from going too far off map
        self.camera_x = max(0, min(self.camera_x, self.game_map.width_pixels - GAME_AREA_WIDTH))
        self.camera_y = max(0, min(self.camera_y, self.game_map.height_pixels - SCREEN_HEIGHT))

    def screen_to_grid(self, screen_x, screen_y):
        grid_x = (screen_x + self.camera_x) // TILE_SIZE
        grid_y = (screen_y + self.camera_y) // TILE_SIZE
        return int(grid_x), int(grid_y)

    def can_place_building(self, grid_x, grid_y, building_type):
         tile = self.game_map.get_tile(grid_x, grid_y)
         if not tile: return False # Off map

         # Check tile validity
         if not tile.walkable or tile.building is not None or tile.resource_type != RESOURCE_NONE:
             return False # Must be walkable ground, no existing building or resource

         # Check cost
         cost = BUILDING_COSTS.get(building_type)
         if cost:
              for resource_name, amount in cost.items():
                  if self.resources.get(resource_name, 0) < amount:
                      # print(f"Not enough {resource_name}")
                      return False # Not enough resources
         return True

    def place_building(self, grid_x, grid_y, building_type):
         if not self.can_place_building(grid_x, grid_y, building_type):
             print("Cannot place building there.")
             return False

         tile = self.game_map.get_tile(grid_x, grid_y)
         new_building = None

         # Deduct Cost
         cost = BUILDING_COSTS.get(building_type)
         if cost:
              for resource_name, amount in cost.items():
                  self.resources[resource_name] -= amount

         # Create and place building
         if building_type == BUILDING_HOUSE:
             new_building = House(grid_x, grid_y)
             self.population_cap += 5 # Add pop cap boost for house
         # Add other building types here...

         if new_building:
              if tile.set_building(new_building):
                  self.buildings.append(new_building)
                  print(f"Placed {BUILDING_NAMES.get(building_type)} at ({grid_x}, {grid_y}). Pop Cap: {self.population_cap}")
                  return True
              else:
                  # Refund cost if placement failed unexpectedly (shouldn't happen often with checks)
                  print("Error! Failed to set building on tile after check.")
                  if cost:
                      for resource_name, amount in cost.items():
                         self.resources[resource_name] += amount
                  return False
         return False


    def draw(self):
        self.screen.fill(BLACK) # Background for areas outside map

        # --- Draw Game Area ---
        game_area_surface = self.screen.subsurface(pygame.Rect(0, 0, GAME_AREA_WIDTH, SCREEN_HEIGHT))
        game_area_surface.fill(DARK_BLUE) # Water color background if map doesn't fill

        # Draw map tiles
        self.game_map.draw(game_area_surface, self.camera_x, self.camera_y)

        # Draw buildings
        for building in self.buildings:
             building.draw(game_area_surface, self.camera_x, self.camera_y)

        # Draw workers
        for worker in self.workers:
             worker.draw(game_area_surface, self.camera_x, self.camera_y)

        # Draw enemies
        for enemy in self.enemies:
             enemy.draw(game_area_surface, self.camera_x, self.camera_y)

        # --- Draw Build Ghost ---
        if self.build_mode and self.build_ghost_pos:
            grid_x, grid_y = self.build_ghost_pos
            screen_x = grid_x * TILE_SIZE - self.camera_x
            screen_y = grid_y * TILE_SIZE - self.camera_y

            if 0 <= screen_x < GAME_AREA_WIDTH and 0 <= screen_y < SCREEN_HEIGHT:
                 ghost_surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                 can_place = self.can_place_building(grid_x, grid_y, self.building_to_place_type)
                 color = (*GREEN_GRASS[:3], 128) if can_place else (*RED[:3], 128) # Semi-transparent green/red

                 # Simple ghost representation
                 pygame.draw.rect(ghost_surface, color, (0, 0, TILE_SIZE, TILE_SIZE))
                 pygame.draw.rect(ghost_surface, WHITE, (0, 0, TILE_SIZE, TILE_SIZE), 1) # White border

                 game_area_surface.blit(ghost_surface, (screen_x, screen_y))


        # --- Draw UI ---
        self.ui.draw(self.screen, self.resources, self.population, self.population_cap)

        pygame.display.flip()