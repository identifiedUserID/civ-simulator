# game.py
import pygame
import sys
import random
import math
from constants import * # Import ALL constants
# Import specific classes needed
from map import GameMap
# Building base class *IS* needed for isinstance checks
from building import Building, TownHall, House # Import specific building types AND BASE CLASS
from unit import Unit, Worker, Enemy # Import specific unit types (Unit needed for isinstance)
from ui import UI

class Game:
    """Main game class orchestrating all game components and logic."""

    def __init__(self):
        """Initializes Pygame, game state, map, UI, and starting objects."""
        pygame.init()
        pygame.font.init()

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Civ Resource/Defense Sim")
        self.clock = pygame.time.Clock()
        try: # Font initialization with fallback
            self.font = pygame.font.SysFont(None, UI_DEFAULT_FONT_SIZE)
        except Exception as e:
            print(f"ERROR initializing font: {e}. Using fallback.")
            self.font = pygame.font.SysFont(pygame.font.get_default_font(), 24)

        self.resources = INITIAL_RESOURCES.copy()
        self.population = 0
        self.population_cap = INITIAL_POPULATION_CAP
        self.game_time_ms = 0
        self.last_consumption_check_time = 0
        self.last_enemy_spawn_time = 0

        self.map_radius = 50
        print(f"Initializing Game with map radius: {self.map_radius}")
        self.game_map = GameMap(self.map_radius)
        self.buildings: list[Building] = [] # Use base Building type hint now
        self.workers: list[Worker] = []
        self.enemies: list[Enemy] = []

        self.ui = UI()

        self.camera_x = (self.game_map.width_pixels - GAME_AREA_WIDTH) // 2
        self.camera_y = (self.game_map.height_pixels - SCREEN_HEIGHT) // 2
        self.dragging = False
        self.drag_start_pos = None
        self.drag_start_camera = None

        self.build_mode = False
        self.building_to_place_type = None
        self.build_ghost_pos = None

        self._spawn_initial_town_hall()
        self.population = len(self.workers) # Correct initial population
        self.clamp_camera()
        print("Game initialization complete.")

    def _spawn_initial_town_hall(self):
        """Finds a suitable location and spawns the starting Town Hall and worker."""
        print("Attempting to spawn initial Town Hall...")
        start_tile = self.game_map.get_random_walkable_tile()
        if not start_tile: Game.quit_game("CRITICAL ERROR: No valid starting tile found!")

        town_hall = TownHall(start_tile.x, start_tile.y)
        if start_tile.set_building(town_hall):
            self.buildings.append(town_hall)
            print(f"Spawned Town Hall at ({start_tile.x}, {start_tile.y})")
            self.center_camera_on(start_tile.x, start_tile.y) # Center camera

            initial_sim_speed = self.ui.sliders['sim_speed'].get_value()
            if not self.try_spawn_worker(town_hall, initial_sim_speed):
                 print("Warning: Could not spawn initial worker.")
        else: Game.quit_game("CRITICAL ERROR: Failed to place TH on selected tile!")

    def try_spawn_worker(self, town_hall: TownHall, current_sim_speed: float) -> bool:
        """Attempts to spawn a worker near the town hall."""
        if self.population >= self.population_cap: return False

        spawn_tile = None
        for r in range(1, 4):
            possible_spawns = []
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                     if abs(dx) != r and abs(dy) != r: continue
                     check_x, check_y = town_hall.x + dx, town_hall.y + dy
                     tile = self.game_map.get_tile(check_x, check_y)
                     if tile and tile.walkable and tile.building is None and tile.resource_type == RESOURCE_NONE:
                         occupied = any(u.grid_x == check_x and u.grid_y == check_y
                                        for u in self.workers + self.enemies)
                         if not occupied: possible_spawns.append(tile)
            if possible_spawns:
                spawn_tile = random.choice(possible_spawns); break

        if spawn_tile:
            new_worker = Worker(spawn_tile.x, spawn_tile.y, current_sim_speed)
            self.workers.append(new_worker); self.population += 1
            return True
        return False

    def center_camera_on(self, grid_x: int, grid_y: int):
         """Centers the camera view on a specific grid coordinate."""
         self.camera_x = grid_x * TILE_SIZE - GAME_AREA_WIDTH // 2
         self.camera_y = grid_y * TILE_SIZE - SCREEN_HEIGHT // 2
         self.clamp_camera()

    def run(self):
        """Main game loop."""
        while True:
            dt_ms_realtime = self.clock.tick(60)
            dt_realtime = dt_ms_realtime / 1000.0
            current_sim_speed = max(0.01, self.ui.sliders['sim_speed'].get_value())
            dt_simulated = dt_realtime * current_sim_speed
            dt_ms_simulated = dt_ms_realtime * current_sim_speed
            self.game_time_ms += dt_ms_simulated

            for unit in self.workers + self.enemies: unit.set_speed_modifier(current_sim_speed)

            self.handle_events()
            self.update(dt_simulated, dt_ms_simulated)
            self.draw()

    def handle_events(self):
        """Processes all user input and system events."""
        mouse_pos = pygame.mouse.get_pos()
        mouse_in_game_area = mouse_pos[0] < GAME_AREA_WIDTH

        for event in pygame.event.get():
            if event.type == pygame.QUIT: Game.quit_game()

            ui_result = self.ui.handle_event(event)
            if ui_result:
                if ui_result.get('type') == 'build_button_click':
                    self.handle_build_button_click(ui_result.get('building'))
                continue # UI handled event

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: self.cancel_build_mode(); continue

            # Build Mode Clicks
            if self.build_mode and mouse_in_game_area and event.type == pygame.MOUSEBUTTONDOWN:
                 if event.button == 1: # Left click place
                     grid_x, grid_y = self.screen_to_grid(mouse_pos[0], mouse_pos[1])
                     if self.can_place_building(grid_x, grid_y, self.building_to_place_type):
                         self.place_building(grid_x, grid_y, self.building_to_place_type)
                     else: print("Cannot place building there.")
                     continue
                 elif event.button == 3: self.cancel_build_mode(); continue # Right click cancel

            # Map Dragging
            if event.type == pygame.MOUSEBUTTONDOWN:
                can_start_drag = event.button == 2 or \
                                 (event.button == 1 and not self.build_mode and mouse_in_game_area)
                if can_start_drag:
                    self.dragging = True; self.drag_start_pos = mouse_pos
                    self.drag_start_camera = (self.camera_x, self.camera_y)
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_SIZEALL); continue
            elif event.type == pygame.MOUSEBUTTONUP:
                 if self.dragging and (event.button == 2 or event.button == 1):
                    self.dragging = False; pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW); continue

            # Mouse Motion
            if event.type == pygame.MOUSEMOTION:
                 if self.build_mode: # Update ghost
                     self.build_ghost_pos = self.screen_to_grid(mouse_pos[0], mouse_pos[1]) if mouse_in_game_area else None
                 elif self.dragging: # Move camera
                    dx = mouse_pos[0] - self.drag_start_pos[0]; dy = mouse_pos[1] - self.drag_start_pos[1]
                    self.camera_x = self.drag_start_camera[0] - dx; self.camera_y = self.drag_start_camera[1] - dy
                    self.clamp_camera()

    def handle_build_button_click(self, building_type: int | None):
        """Logic for when a build button is clicked."""
        if building_type is None: return

        cost = BUILDING_COSTS.get(building_type, {})
        can_afford = all(self.resources.get(res, 0) >= amount for res, amount in cost.items())

        if not can_afford:
            cost_str = ", ".join([f"{amt} {res}" for res, amt in cost.items()])
            print(f"Cannot afford {BUILDING_NAMES.get(building_type)}: Requires {cost_str}")
            self.cancel_build_mode(); return

        if self.build_mode and self.building_to_place_type == building_type:
            self.cancel_build_mode()
        else:
            print(f"Entering build mode for: {BUILDING_NAMES.get(building_type)}")
            self.build_mode = True; self.building_to_place_type = building_type
            mouse_pos = pygame.mouse.get_pos() # Update ghost immediately
            self.build_ghost_pos = self.screen_to_grid(mouse_pos[0], mouse_pos[1]) if mouse_pos[0] < GAME_AREA_WIDTH else None

    def cancel_build_mode(self):
        """Turns off build mode."""
        if self.build_mode:
            self.build_mode = False; self.building_to_place_type = None; self.build_ghost_pos = None

    def update(self, dt_simulated: float, dt_ms_simulated: float):
        """Updates game state."""
        consumption_mod = self.ui.sliders['consumption'].get_value()
        respawn_mod = self.ui.sliders['respawn'].get_value()
        monster_spawn_mod = self.ui.sliders['monster_spawn'].get_value()
        current_sim_speed = self.ui.sliders['sim_speed'].get_value()

        # --- Updates ---
        # Town Hall Spawning
        for building in self.buildings:
            if isinstance(building, TownHall):
                building.worker_spawn_timer -= dt_ms_simulated
                if building.worker_spawn_timer <= 0:
                    self.try_spawn_worker(building, current_sim_speed)
                    building.worker_spawn_timer = WORKER_SPAWN_TIME

        # Worker Updates
        for worker in self.workers:
            worker.update(dt_simulated, self.game_map, self.buildings, self.resources, self.population)

        # Resource Consumption
        if self.game_time_ms - self.last_consumption_check_time >= 1000:
            time_passed = (self.game_time_ms - self.last_consumption_check_time) / 1000.0
            food_need = self.population * FOOD_CONSUMPTION_RATE_BASE * consumption_mod * time_passed
            water_need = self.population * WATER_CONSUMPTION_RATE_BASE * consumption_mod * time_passed
            self.resources['Food'] = max(0, self.resources['Food'] - food_need)
            self.resources['Water'] = max(0, self.resources['Water'] - water_need)
            self.last_consumption_check_time = self.game_time_ms

        # Resource Respawns
        self.game_map.update_respawns(dt_ms_simulated, respawn_mod)

        # Enemy Spawning
        time_since_spawn = self.game_time_ms - self.last_enemy_spawn_time
        spawn_interval = ENEMY_SPAWN_TIME_BASE / max(0.01, monster_spawn_mod)
        if time_since_spawn >= spawn_interval:
             self.spawn_enemy(current_sim_speed)
             self.last_enemy_spawn_time = self.game_time_ms

        # Enemy Updates (Pass only needed info: buildings, workers)
        # --- CORRECTION: Enemy update in unit.py was changed to need buildings and workers ---
        for enemy in self.enemies:
            # The enemy update method expects buildings and workers list
            enemy.update(dt_simulated, self.buildings, self.workers)

        # Cleanup Dead Entities
        self.cleanup_entities()

        # Update Build Ghost (if mouse stationary)
        if self.build_mode and not self.dragging and not any(pygame.mouse.get_pressed()):
             mouse_pos = pygame.mouse.get_pos()
             current_ghost_pos = self.screen_to_grid(mouse_pos[0], mouse_pos[1]) if mouse_pos[0] < GAME_AREA_WIDTH else None
             if current_ghost_pos != self.build_ghost_pos: self.build_ghost_pos = current_ghost_pos

    def cleanup_entities(self):
        """Removes dead units/buildings and updates state."""
        initial_pop = self.population

        self.workers = [w for w in self.workers if w.hp > 0]
        self.enemies = [e for e in self.enemies if e.hp > 0]
        destroyed = [b for b in self.buildings if b.hp <= 0]
        self.buildings = [b for b in self.buildings if b.hp > 0]

        self.population = len(self.workers) # Recalculate population

        pop_cap_loss = 0
        game_over = False
        for b in destroyed:
            tile = self.game_map.get_tile(b.x, b.y)
            if tile: tile.remove_building()
            if b.type == BUILDING_HOUSE: pop_cap_loss += HOUSE_POP_BONUS
            elif b.type == BUILDING_TOWNHALL: game_over = True

        if pop_cap_loss > 0:
            self.population_cap = max(INITIAL_POPULATION_CAP, self.population_cap - pop_cap_loss)

        if game_over: self.handle_game_over()

    def handle_game_over(self):
        """Displays game over message and quits."""
        print("\n--- GAME OVER --- Your Town Hall was destroyed!")
        try: # Attempt to show message on screen
            font_large = pygame.font.SysFont(None, 72, bold=True)
            text_surf = font_large.render("GAME OVER", True, RED)
            text_rect = text_surf.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
            self.screen.blit(text_surf, text_rect)
            pygame.display.flip()
            pygame.time.wait(5000)
        except Exception as e: print(f"Error showing game over screen: {e}")
        Game.quit_game()

    def spawn_enemy(self, current_sim_speed: float):
        """Spawns an enemy near map edge."""
        attempts = 0; max_attempts = 50
        center_x, center_y = self.game_map.radius, self.game_map.radius
        while attempts < max_attempts:
            angle = random.uniform(0, 2 * math.pi)
            dist = self.map_radius * random.uniform(0.80, 0.98)
            sx = int(center_x + dist * math.cos(angle))
            sy = int(center_y + dist * math.sin(angle))
            sx = max(0, min(self.game_map.diameter - 1, sx))
            sy = max(0, min(self.game_map.diameter - 1, sy))
            tile = self.game_map.get_tile(sx, sy)
            if tile and tile.walkable and tile.building is None and tile.resource_type == RESOURCE_NONE:
                if not any(u.grid_x == sx and u.grid_y == sy for u in self.workers + self.enemies):
                    self.enemies.append(Enemy(sx, sy, current_sim_speed)); return
            attempts += 1

    def clamp_camera(self):
        """Keeps camera within map bounds."""
        max_x = max(0, self.game_map.width_pixels - GAME_AREA_WIDTH)
        max_y = max(0, self.game_map.height_pixels - SCREEN_HEIGHT)
        self.camera_x = max(0, min(int(self.camera_x), max_x))
        self.camera_y = max(0, min(int(self.camera_y), max_y))

    def screen_to_grid(self, screen_x: int, screen_y: int) -> tuple[int, int] | tuple[None, None]:
        """Converts screen pixel coords to map grid coords."""
        if not (0 <= screen_x < GAME_AREA_WIDTH and 0 <= screen_y < SCREEN_HEIGHT): return None, None
        world_x = screen_x + self.camera_x; world_y = screen_y + self.camera_y
        grid_x = int(world_x // TILE_SIZE); grid_y = int(world_y // TILE_SIZE)
        if 0 <= grid_x < self.game_map.diameter and 0 <= grid_y < self.game_map.diameter: return grid_x, grid_y
        return None, None

    def can_place_building(self, grid_x: int | None, grid_y: int | None, building_type: int | None) -> bool:
        """Checks if building placement is valid."""
        if grid_x is None or grid_y is None or building_type is None: return False
        tile = self.game_map.get_tile(grid_x, grid_y)
        if not tile or tile.terrain_type != TERRAIN_GROUND or not tile.walkable: return False
        cost = BUILDING_COSTS.get(building_type, {})
        if not all(self.resources.get(res, 0) >= amount for res, amount in cost.items()): return False
        return True

    def place_building(self, grid_x: int, grid_y: int, building_type: int) -> bool:
        """Places building, deducts cost, updates state. Returns True on success."""
        if not self.can_place_building(grid_x, grid_y, building_type): return False
        tile = self.game_map.get_tile(grid_x, grid_y)
        if not tile: return False

        cost = BUILDING_COSTS.get(building_type, {}); new_building: Building | None = None # Use base type hint
        for res, amount in cost.items(): self.resources[res] -= amount

        if building_type == BUILDING_HOUSE: new_building = House(grid_x, grid_y)
        # Add elif for other types...

        if new_building and tile.set_building(new_building):
            self.buildings.append(new_building)
            print(f"Placed {BUILDING_NAMES.get(building_type, 'Building')} at ({grid_x},{grid_y}).")
            if building_type == BUILDING_HOUSE:
                self.population_cap += HOUSE_POP_BONUS
                print(f"Pop Cap: {self.population_cap}")
            return True
        else: # Placement failed or unknown type
            for res, amount in cost.items(): self.resources[res] += amount # Refund
            if not new_building: print(f"ERROR: Unknown building type {building_type}.")
            else: print("CRITICAL ERROR: Failed tile.set_building after validation!")
            return False

    def draw(self):
        """Draws the entire game screen."""
        game_area_surface = self.screen.subsurface(pygame.Rect(0, 0, GAME_AREA_WIDTH, SCREEN_HEIGHT))
        game_area_surface.fill(DARK_BLUE)

        # 1. Map Base
        self.game_map.draw(game_area_surface, self.camera_x, self.camera_y)

        # 2. Sorted Game Objects
        # Combine lists using base types Unit and Building for sorting key check
        drawable_entities: list[Unit | Building] = self.buildings + self.workers + self.enemies
        # Sort by bottom y-coordinate
        drawable_entities.sort(key=lambda obj: obj.y + TILE_SIZE if isinstance(obj, Building) else obj.y + TILE_SIZE/2)
        for entity in drawable_entities:
            entity.draw(game_area_surface, self.camera_x, self.camera_y)

        # 3. Build Ghost
        if self.build_mode and self.build_ghost_pos:
            gx, gy = self.build_ghost_pos
            if gx is not None and gy is not None:
                scr_x = gx * TILE_SIZE - self.camera_x; scr_y = gy * TILE_SIZE - self.camera_y
                if pygame.Rect(scr_x, scr_y, TILE_SIZE, TILE_SIZE).colliderect(game_area_surface.get_rect()):
                    ghost_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                    is_valid = self.can_place_building(gx, gy, self.building_to_place_type)
                    color = (*GREEN[:3], 128) if is_valid else (*RED[:3], 128) # Use GREEN constant
                    pygame.draw.rect(ghost_surf, color, (0, 0, TILE_SIZE, TILE_SIZE))
                    pygame.draw.rect(ghost_surf, WHITE, (0, 0, TILE_SIZE, TILE_SIZE), 1)
                    game_area_surface.blit(ghost_surf, (scr_x, scr_y))

        # --- Draw UI ---
        self.ui.draw(self.screen, self.resources, self.population, self.population_cap)

        pygame.display.flip()

    @staticmethod
    def quit_game(message: str | None = None):
        """Cleans up Pygame and exits the application."""
        if message: print(message)
        print("Exiting game...")
        pygame.quit()
        sys.exit()