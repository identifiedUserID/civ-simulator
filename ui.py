# ui.py
import pygame
from constants import *

class Slider:
    def __init__(self, x, y, w, h, min_val, max_val, initial_val, label):
        self.rect = pygame.Rect(x, y, w, h)
        self.min_val = min_val
        self.max_val = max_val
        self.val = initial_val
        self.label = label
        self.knob_radius = h // 2 + 2
        self.dragging = False
        self.font = pygame.font.SysFont(None, 20)

    def get_value(self):
        return self.val

    def set_value_from_pos(self, x_pos):
        ratio = max(0, min(1, (x_pos - self.rect.left) / self.rect.width))
        self.val = self.min_val + ratio * (self.max_val - self.min_val)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos) or \
               (abs(event.pos[0] - self._get_knob_x()) < self.knob_radius and \
                abs(event.pos[1] - self.rect.centery) < self.knob_radius) :
                 self.dragging = True
                 self.set_value_from_pos(event.pos[0])
                 return True
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.dragging:
                self.dragging = False
                return True
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.set_value_from_pos(event.pos[0])
                return True
        return False

    def _get_knob_x(self):
        ratio = (self.val - self.min_val) / (self.max_val - self.min_val)
        return self.rect.left + ratio * self.rect.width

    def draw(self, surface):
        # Draw label
        label_surf = self.font.render(f"{self.label}: {self.val:.2f}x", True, WHITE)
        surface.blit(label_surf, (self.rect.x, self.rect.y - 18))

        # Draw track
        pygame.draw.rect(surface, LIGHT_GRAY, self.rect, border_radius=5)
        pygame.draw.rect(surface, GRAY, self.rect, width=1, border_radius=5)

        # Draw knob
        knob_x = self._get_knob_x()
        pygame.draw.circle(surface, BLUE if not self.dragging else RED, (int(knob_x), self.rect.centery), self.knob_radius)


class Button:
    def __init__(self, x, y, w, h, text, icon_surf=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.icon_surf = icon_surf # Optional: a pre-rendered surface for the icon
        self.font = pygame.font.SysFont(None, 24)
        self.is_hovered = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered:
                return True # Clicked
        return False

    def draw(self, surface):
        color = LIGHT_GRAY if not self.is_hovered else WHITE
        pygame.draw.rect(surface, color, self.rect, border_radius=3)
        pygame.draw.rect(surface, BLACK, self.rect, width=1, border_radius=3)

        if self.icon_surf:
            icon_rect = self.icon_surf.get_rect(center=self.rect.center)
            surface.blit(self.icon_surf, icon_rect)
        elif self.text:
            text_surf = self.font.render(self.text, True, BLACK)
            text_rect = text_surf.get_rect(center=self.rect.center)
            surface.blit(text_surf, text_rect)

class UI:
    def __init__(self):
        self.font_resource = pygame.font.SysFont(None, 24)
        self.font_pop = pygame.font.SysFont(None, 22)
        self.sliders = {}
        self.build_buttons = {}
        self.panel_rect = pygame.Rect(GAME_AREA_WIDTH, 0, SIDE_PANEL_WIDTH, SCREEN_HEIGHT)

        # Create UI elements
        slider_y = 50
        slider_spacing = 60
        slider_width = SIDE_PANEL_WIDTH - 40
        slider_x = GAME_AREA_WIDTH + 20

        self.sliders['sim_speed'] = Slider(slider_x, slider_y, slider_width, 15, 0.1, 5.0, 1.0, "Sim Speed")
        slider_y += slider_spacing
        self.sliders['consumption'] = Slider(slider_x, slider_y, slider_width, 15, 0.1, 5.0, 1.0, "Consumption")
        slider_y += slider_spacing
        self.sliders['respawn'] = Slider(slider_x, slider_y, slider_width, 15, 0.1, 5.0, 1.0, "Respawn Rate")
        slider_y += slider_spacing
        self.sliders['monster_spawn'] = Slider(slider_x, slider_y, slider_width, 15, 0.1, 5.0, 1.0, "Monster Spawn")

        # Build Buttons
        build_y = slider_y + 80
        build_x = GAME_AREA_WIDTH + 10
        button_size = 40
        button_spacing = 10

        # Create simple icon surfaces (replace with images later)
        house_icon = pygame.Surface((button_size, button_size))
        house_icon.fill(BROWN_STONE)
        pygame.draw.polygon(house_icon, RED, [(0, button_size//2), (button_size//2, 0), (button_size, button_size//2)]) # Roof
        self.build_buttons[BUILDING_HOUSE] = Button(build_x, build_y, button_size, button_size, "", house_icon)
        # Add more buttons here...


    def handle_event(self, event):
        for slider in self.sliders.values():
            if slider.handle_event(event):
                return True # Event handled by a slider

        for building_type, button in self.build_buttons.items():
             if button.handle_event(event):
                 # Return the type of building clicked
                 return building_type # Signal build mode request

        return False # Event not handled by UI elements

    def draw(self, surface, resources, population, pop_cap):
        # Draw Panel Background
        pygame.draw.rect(surface, DARK_BLUE, self.panel_rect) # Panel background

        # Draw Resource Counts
        res_y = 10
        for name, amount in resources.items():
            text = f"{name}: {int(amount)}"
            res_surf = self.font_resource.render(text, True, WHITE)
            surface.blit(res_surf, (GAME_AREA_WIDTH + 10, res_y))
            res_y += 25

         # Draw Population
        pop_text = f"Pop: {population} / {pop_cap}"
        pop_surf = self.font_pop.render(pop_text, True, WHITE)
        surface.blit(pop_surf, (GAME_AREA_WIDTH + 10, res_y + 10))


        # Draw Sliders
        for slider in self.sliders.values():
            slider.draw(surface)

        # Draw Build Header
        build_header_surf = self.font_resource.render("Build:", True, WHITE)
        surface.blit(build_header_surf, (GAME_AREA_WIDTH + 10, self.build_buttons[BUILDING_HOUSE].rect.y - 25))


        # Draw Build Buttons
        for button in self.build_buttons.values():
            button.draw(surface)