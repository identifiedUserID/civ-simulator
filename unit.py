# unit.py
import pygame # Needed for drawing
import math
from constants import * # Import constants
from tile import Tile
from building import Building, TownHall # Need TownHall specifically

# Type hinting for complex types passed from Game
BuildingList = list[Building]
ResourceDict = dict[str, int | float]

class Unit:
    """Base class for mobile entities like Workers and Enemies."""
    def __init__(self, x: int, y: int, unit_type: int, game_speed_modifier: float = 1.0):
        self.x: float = float(x * TILE_SIZE + TILE_SIZE / 2)
        self.y: float = float(y * TILE_SIZE + TILE_SIZE / 2)
        self.grid_x: int = x
        self.grid_y: int = y
        self.type = unit_type
        self.target = None
        self.target_tile: Tile | None = None
        self.state: str = 'idle'
        self.speed: float = 0.0
        self.game_speed_modifier: float = game_speed_modifier
        self.hp: int = 100
        self.max_hp: int = 100

    def update_grid_pos(self):
        self.grid_x = int(self.x // TILE_SIZE); self.grid_y = int(self.y // TILE_SIZE)

    def set_speed_modifier(self, modifier: float):
        self.game_speed_modifier = max(0.01, modifier)

    def move_towards(self, target_x_px: float, target_y_px: float, dt_simulated: float) -> bool:
        dx = target_x_px - self.x; dy = target_y_px - self.y
        dist_sq = dx*dx + dy*dy
        stop_distance = TILE_SIZE / 4
        if isinstance(self.target, (Tile, Building, Unit)): stop_distance = TILE_SIZE * 0.6
        if dist_sq < stop_distance * stop_distance: return True
        dist = math.sqrt(dist_sq)
        if dist > 0: dx /= dist; dy /= dist
        else: return True
        effective_speed_pixels = self.speed * TILE_SIZE * self.game_speed_modifier * dt_simulated
        self.x += dx * effective_speed_pixels; self.y += dy * effective_speed_pixels
        self.update_grid_pos(); return False

    def draw(self, surface: pygame.Surface, camera_x: int, camera_y: int):
        screen_x = int(self.x - camera_x); screen_y = int(self.y - camera_y)
        radius = TILE_SIZE // 3
        if not pygame.Rect(screen_x - radius, screen_y - radius, radius*2, radius*2).colliderect(surface.get_rect()): return
        color = WHITE
        if self.type == UNIT_WORKER: color = GREEN
        elif self.type == UNIT_ENEMY_BASIC: color = RED
        pygame.draw.circle(surface, color, (screen_x, screen_y), radius)
        pygame.draw.circle(surface, BLACK, (screen_x, screen_y), radius, 1)
        if self.hp < self.max_hp and self.max_hp > 0:
            hp_ratio = max(0.0, float(self.hp) / self.max_hp)
            bar_width = TILE_SIZE * 0.6; bar_height = 4
            bar_x = int(screen_x - bar_width / 2); bar_y = int(screen_y - radius - bar_height - 2)
            pygame.draw.rect(surface, DARK_RED, (bar_x, bar_y, int(bar_width), bar_height))
            pygame.draw.rect(surface, GREEN_GRASS, (bar_x, bar_y, int(bar_width * hp_ratio), bar_height))

# --- Worker Unit ---
class Worker(Unit):
    def __init__(self, x: int, y: int, game_speed_modifier: float):
        super().__init__(x, y, UNIT_WORKER, game_speed_modifier)
        self.speed = WORKER_SPEED; self.hp = WORKER_HP; self.max_hp = WORKER_HP
        self.resource_carried: int = RESOURCE_NONE; self.carry_amount: int = 0
        self.gather_timer: float = 0
        self.preferred_resource_order = [RESOURCE_FOOD, RESOURCE_WOOD, RESOURCE_STONE, RESOURCE_IRON]
        # --- Add flag to prevent error spam ---
        self._cant_find_th_logged: bool = False
        self._path_retry_timer: float = 0 # Timer to wait before retrying pathfinding

    def update(self, dt_simulated: float, game_map, buildings: BuildingList,
               resources: ResourceDict, current_population: int):
        dt_ms = dt_simulated * 1000
        retry_delay = 3000 # Wait 3 seconds (in ms) before retrying path if failed

        # Update path retry timer if active
        if self._path_retry_timer > 0:
            self._path_retry_timer -= dt_ms
            if self._path_retry_timer <= 0:
                self._path_retry_timer = 0 # Reset timer
                # Allow trying to find TH again below
            else:
                # Still waiting to retry, potentially wander slightly or just wait
                # For simplicity, just wait for now
                return # Skip rest of update while waiting

        # --- State Machine ---
        if self.state == 'idle':
            if self.carry_amount > 0: self.find_town_hall_and_return(game_map, buildings)
            else: self.find_resource_and_move(game_map, resources, current_population)

        elif self.state == 'moving_to_resource':
            # ... (moving logic remains the same as previous version) ...
            if self.target_tile and self.target_tile.resource_type != RESOURCE_NONE and self.target_tile.resource_amount > 0:
                target_cx = self.target_tile.x * TILE_SIZE + TILE_SIZE / 2
                target_cy = self.target_tile.y * TILE_SIZE + TILE_SIZE / 2
                if self.move_towards(target_cx, target_cy, dt_simulated):
                    if self.target_tile.resource_type != RESOURCE_NONE and self.target_tile.resource_amount > 0:
                        self.state = 'gathering'; self.gather_timer = 0
                    else: self.state = 'idle'; self.clear_target()
            else: self.state = 'idle'; self.clear_target()

        elif self.state == 'gathering':
            # ... (gathering logic remains the same as previous version) ...
            self.gather_timer -= dt_ms
            if self.gather_timer <= 0:
                if self.target_tile and self.target_tile.resource_amount > 0:
                    gathered, res_type = self.target_tile.gather_resource(WORKER_GATHER_RATE)
                    if gathered > 0:
                        if self.carry_amount == 0: self.resource_carried = res_type
                        if self.resource_carried == res_type: self.carry_amount += gathered
                        else: self.find_town_hall_and_return(game_map, buildings)

                    if self.state != 'moving_to_townhall':
                        if self.target_tile.resource_amount <= 0 or self.carry_amount >= WORKER_CAPACITY:
                            if self.target_tile.resource_amount <= 0:
                                game_map.mark_for_respawn(self.target_tile.x, self.target_tile.y)
                            self.find_town_hall_and_return(game_map, buildings)
                        else: self.gather_timer = WORKER_GATHER_TIME
                else:
                    if self.carry_amount > 0: self.find_town_hall_and_return(game_map, buildings)
                    else: self.state = 'idle'; self.clear_target()

        elif self.state == 'moving_to_townhall':
            # Target should be TownHall object
            if isinstance(self.target, TownHall):
                target_cx = self.target.x * TILE_SIZE + TILE_SIZE / 2
                target_cy = self.target.y * TILE_SIZE + TILE_SIZE / 2
                if self.move_towards(target_cx, target_cy, dt_simulated):
                     self.state = 'dropping_off'
                     self._cant_find_th_logged = False # Reset log flag on successful arrival
                     self._path_retry_timer = 0 # Reset retry timer
            else: # Target lost or invalid (e.g., TH destroyed)
                 # Try to find TH again, handle failure case within the find method
                 if not self.find_town_hall_and_return(game_map, buildings):
                      # If still can't find it, remain idle (find method logs error once)
                      self.state = 'idle'; self.clear_target()

        elif self.state == 'dropping_off':
            # ... (dropping off logic remains the same as previous version) ...
            if self.carry_amount > 0:
                res_name = RESOURCE_NAMES.get(self.resource_carried)
                if res_name and res_name != "None":
                     if res_name not in resources: resources[res_name] = 0
                     resources[res_name] += self.carry_amount
                self.carry_amount = 0; self.resource_carried = RESOURCE_NONE
            self._cant_find_th_logged = False # Reset log flag on successful drop-off
            self._path_retry_timer = 0 # Reset retry timer
            self.state = 'idle'; self.clear_target()

    def find_resource_and_move(self, game_map, resources: ResourceDict, current_population: int):
        # ... (logic remains the same as previous version) ...
        self.clear_target(); found_tile = None
        for res_type in self.preferred_resource_order:
             needed = True
             if res_type == RESOURCE_FOOD and resources.get('Food', 0) > current_population * 15: needed = False
             if needed:
                found_tile = game_map.find_nearest_resource(self.grid_x, self.grid_y, res_type)
                if found_tile: break
        if not found_tile:
             for res_type in [RESOURCE_WOOD, RESOURCE_FOOD, RESOURCE_STONE, RESOURCE_IRON]:
                 found_tile = game_map.find_nearest_resource(self.grid_x, self.grid_y, res_type)
                 if found_tile: break
        if found_tile:
            self.target_tile = found_tile; self.target = (found_tile.x, found_tile.y)
            self.state = 'moving_to_resource'
        else: self.state = 'idle'

    def find_town_hall_and_return(self, game_map, buildings: BuildingList) -> bool:
        """
        Finds nearest Town Hall, sets target/state. Handles failure without spamming.
        Returns True if TH found AND pathing is initiated, False otherwise.
        """
        # Only search if retry timer is not active
        if self._path_retry_timer > 0:
            return False # Still waiting to retry

        town_hall = game_map.find_nearest_building(self.grid_x, self.grid_y, BUILDING_TOWNHALL)
        if town_hall:
            self.target = town_hall
            self.target_tile = None
            self.state = 'moving_to_townhall'
            # If we successfully found it *now*, reset the logged flag
            self._cant_find_th_logged = False
            return True
        else:
            # --- Error Handling ---
            if not self._cant_find_th_logged: # Log only once
                print(f"CRITICAL: Worker at ({self.grid_x},{self.grid_y}) cannot find path to Town Hall!")
                self._cant_find_th_logged = True
            # Don't change state back to idle immediately if carrying resources.
            # Stay in current state (or moving_to_townhall if called from idle/gather)
            # Set a timer to retry pathfinding after a delay
            self._path_retry_timer = 3000 # e.g., wait 3 seconds
            print(f"Worker at ({self.grid_x},{self.grid_y}) will retry finding TH in {self._path_retry_timer/1000:.1f}s.") # Feedback
            # Ensure state is set to moving_to_townhall so it keeps trying (or stays put)
            self.state = 'moving_to_townhall'
            self.target = None # Clear specific target object, but keep state
            return False # Pathfinding failed for now

    def clear_target(self):
        """Resets target info."""
        self.target = None; self.target_tile = None

# --- Enemy Unit ---
# ... (Enemy class remains the same as previous correct version) ...
class Enemy(Unit):
    def __init__(self, x: int, y: int, game_speed_modifier: float):
        super().__init__(x, y, UNIT_ENEMY_BASIC, game_speed_modifier)
        self.speed = ENEMY_SPEED; self.hp = ENEMY_HP; self.max_hp = ENEMY_HP
        self.damage = ENEMY_DAMAGE; self.attack_rate = ENEMY_ATTACK_RATE
        self.attack_timer: float = 0
        self.target_object: Unit | Building | None = None

    def update(self, dt_simulated: float, buildings: BuildingList, workers: list['Worker']):
        dt_ms = dt_simulated * 1000
        if self.attack_timer > 0: self.attack_timer -= dt_ms

        if self.state == 'idle':
            found_target = self.find_target(workers, buildings)
            if found_target:
                self.target_object = found_target; self.target = self.target_object
                self.state = 'moving_to_target'
        elif self.state == 'moving_to_target':
             if self.target_object and self.target_object.hp > 0:
                 target_px, target_py = self.get_target_pixel_coords()
                 dx, dy = target_px - self.x, target_py - self.y
                 if dx*dx + dy*dy < (TILE_SIZE * 1.1)**2:
                     self.state = 'attacking'; self.attack_timer = 0
                 else: self.move_towards(target_px, target_py, dt_simulated)
             else: self.state = 'idle'; self.clear_target()
        elif self.state == 'attacking':
            if self.target_object and self.target_object.hp > 0:
                target_px, target_py = self.get_target_pixel_coords()
                dx, dy = target_px - self.x, target_py - self.y
                if dx*dx + dy*dy > (TILE_SIZE * 1.4)**2:
                    self.state = 'moving_to_target'
                elif self.attack_timer <= 0:
                    self.target_object.hp -= self.damage
                    if self.target_object.hp <= 0:
                        print(f"Enemy destroyed {type(self.target_object).__name__}!")
                        self.state = 'idle'; self.clear_target()
                    else: self.attack_timer = self.attack_rate
            else: self.state = 'idle'; self.clear_target()

    def find_target(self, workers: list['Worker'], buildings: BuildingList) -> Unit | Building | None:
        nearest_target = None; min_dist_sq = ENEMY_SCAN_RADIUS_SQ
        for worker in workers:
            if worker.hp > 0:
                dist_sq = (worker.x - self.x)**2 + (worker.y - self.y)**2
                if dist_sq < min_dist_sq: min_dist_sq = dist_sq; nearest_target = worker
        for building in buildings:
             if building.hp > 0:
                 b_cx = building.x * TILE_SIZE + TILE_SIZE / 2
                 b_cy = building.y * TILE_SIZE + TILE_SIZE / 2
                 dist_sq = (b_cx - self.x)**2 + (b_cy - self.y)**2
                 if dist_sq < min_dist_sq: min_dist_sq = dist_sq; nearest_target = building
        return nearest_target

    def get_target_pixel_coords(self) -> tuple[float, float]:
         if isinstance(self.target_object, Unit): return self.target_object.x, self.target_object.y
         if isinstance(self.target_object, Building):
             return (self.target_object.x * TILE_SIZE + TILE_SIZE / 2,
                     self.target_object.y * TILE_SIZE + TILE_SIZE / 2)
         return self.x, self.y

    def clear_target(self):
        self.target = None; self.target_object = None