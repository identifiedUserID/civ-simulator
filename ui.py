# ui.py
import pygame
from constants import *

class Slider:
    """A simple horizontal slider UI element."""
    def __init__(self, x, y, w, h, min_val, max_val, initial_val, label):
        self.rect = pygame.Rect(x, y, w, h) # The track rectangle
        self.min_val = min_val
        self.max_val = max_val
        self.val = initial_val
        self.label = label
        # Make knob slightly larger than track height for easier clicking
        self.knob_radius = h // 2 + 3
        self.dragging = False
        # Use different font sizes for label and value display
        self.font_label = pygame.font.SysFont(None, UI_SMALL_FONT_SIZE)
        self.font_value = pygame.font.SysFont(None, UI_SMALL_FONT_SIZE - 2)

    def get_value(self):
        """Returns the current value of the slider."""
        # Ensure value stays within bounds, especially if bounds change later
        return max(self.min_val, min(self.max_val, self.val))

    def set_value_from_pos(self, mouse_x):
        """Updates the slider's value based on mouse horizontal position."""
        # Calculate the ratio (0 to 1) of the click position along the slider track
        ratio = (mouse_x - self.rect.left) / self.rect.width
        # Clamp ratio between 0 and 1
        ratio = max(0, min(1, ratio))
        # Calculate the value based on the ratio and min/max values
        self.val = self.min_val + ratio * (self.max_val - self.min_val)

    def handle_event(self, event):
        """Processes mouse events for interaction with the slider."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check collision with the knob's clickable area
            knob_x = self._get_knob_x()
            knob_rect = pygame.Rect(knob_x - self.knob_radius, self.rect.centery - self.knob_radius,
                                    self.knob_radius * 2, self.knob_radius * 2)
            # Also allow clicking anywhere on the track to jump the knob
            if knob_rect.collidepoint(event.pos) or self.rect.collidepoint(event.pos):
                 self.dragging = True
                 # Update value immediately on click
                 self.set_value_from_pos(event.pos[0])
                 return True # Event handled
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.dragging:
                self.dragging = False
                return True # Event handled
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                # Update value only while dragging
                self.set_value_from_pos(event.pos[0])
                return True # Event handled
        return False # Event not handled by this slider

    def _get_knob_x(self):
        """Calculates the horizontal center position of the slider knob."""
        # Prevent division by zero if min_val equals max_val
        range_val = self.max_val - self.min_val
        if range_val == 0:
            return self.rect.left
        # Calculate the ratio of the current value within the range
        ratio = (self.get_value() - self.min_val) / range_val
        # Calculate knob's x position based on the ratio and track width
        return self.rect.left + ratio * self.rect.width

    def draw(self, surface):
        """Draws the slider label, track, and knob."""
        # Draw label above the slider
        label_surf = self.font_label.render(f"{self.label}:", True, WHITE)
        label_rect = label_surf.get_rect(left=self.rect.x, bottom=self.rect.y - 3)
        surface.blit(label_surf, label_rect)

        # Draw value next to label
        value_surf = self.font_value.render(f"{self.get_value():.1f}x", True, LIGHT_GRAY)
        value_rect = value_surf.get_rect(left=label_rect.right + 5, centery=label_rect.centery)
        surface.blit(value_surf, value_rect)

        # Draw the track
        pygame.draw.rect(surface, LIGHT_GRAY, self.rect, border_radius=5)
        pygame.draw.rect(surface, GRAY, self.rect, width=1, border_radius=5) # Outline

        # Draw the knob
        knob_x = self._get_knob_x()
        knob_color = RED if self.dragging else BLUE # Change color when dragging
        pygame.draw.circle(surface, knob_color, (int(knob_x), self.rect.centery), self.knob_radius)
        pygame.draw.circle(surface, BLACK, (int(knob_x), self.rect.centery), self.knob_radius, 1) # Outline


class Button:
    """A simple clickable button UI element, potentially with an icon."""
    def __init__(self, x, y, w, h, text="", icon_surf=None, tooltip=""):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text # Text is drawn if no icon is provided
        self.icon_surf = icon_surf # A pre-rendered pygame.Surface for the icon
        self.tooltip = tooltip # Text to display on hover
        self.font = pygame.font.SysFont(None, UI_DEFAULT_FONT_SIZE)
        self.font_tooltip = pygame.font.SysFont(None, UI_SMALL_FONT_SIZE)
        self.is_hovered = False
        self.is_active = False # Can be used for toggle buttons if needed

    def handle_event(self, event):
        """Processes mouse events for button clicks and hover state."""
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered and event.button == 1: # Left click
                # self.is_active = not self.is_active # Example for toggle
                return True # Clicked!
        # Can add MOUSEBUTTONUP logic if needed (e.g., for click release)
        return False

    def draw(self, surface):
        """Draws the button background, icon or text, and tooltip on hover."""
        # Determine background color based on hover state
        bg_color = WHITE if self.is_hovered else LIGHT_GRAY
        pygame.draw.rect(surface, bg_color, self.rect, border_radius=3)
        pygame.draw.rect(surface, BLACK, self.rect, width=1, border_radius=3) # Outline

        # Draw icon or text centered on the button
        if self.icon_surf:
            icon_rect = self.icon_surf.get_rect(center=self.rect.center)
            surface.blit(self.icon_surf, icon_rect)
        elif self.text:
            text_surf = self.font.render(self.text, True, BLACK)
            text_rect = text_surf.get_rect(center=self.rect.center)
            surface.blit(text_surf, text_rect)

        # Draw tooltip if hovered
        if self.is_hovered and self.tooltip:
            tooltip_surf = self.font_tooltip.render(self.tooltip, True, BLACK, LIGHT_GRAY) # Black text on light gray bg
            tooltip_rect = tooltip_surf.get_rect(midbottom=(self.rect.centerx, self.rect.top - 5))
            # Ensure tooltip stays on screen
            tooltip_rect.clamp_ip(surface.get_rect())
            surface.blit(tooltip_surf, tooltip_rect)


class UI:
    """Manages all UI elements like resource display, sliders, and buttons."""
    def __init__(self):
        self.panel_rect = pygame.Rect(GAME_AREA_WIDTH, 0, SIDE_PANEL_WIDTH, SCREEN_HEIGHT)
        self.font_resource = pygame.font.SysFont(None, UI_DEFAULT_FONT_SIZE)
        self.font_pop = pygame.font.SysFont(None, UI_SMALL_FONT_SIZE)
        self.font_header = pygame.font.SysFont(None, UI_DEFAULT_FONT_SIZE, bold=True)

        # --- Sliders ---
        self.sliders = {}
        slider_y = 80 # Start sliders lower down
        slider_spacing = 65 # Increased spacing
        slider_width = SIDE_PANEL_WIDTH - UI_PADDING * 3 # Add padding on both sides
        slider_x = GAME_AREA_WIDTH + UI_PADDING * 1.5

        self.sliders['sim_speed'] = Slider(slider_x, slider_y, slider_width, UI_SLIDER_HEIGHT, 0.1, 5.0, 1.0, "Sim Speed")
        slider_y += slider_spacing
        self.sliders['consumption'] = Slider(slider_x, slider_y, slider_width, UI_SLIDER_HEIGHT, 0.1, 5.0, 1.0, "Consumption")
        slider_y += slider_spacing
        self.sliders['respawn'] = Slider(slider_x, slider_y, slider_width, UI_SLIDER_HEIGHT, 0.1, 5.0, 1.0, "Respawn Rate")
        slider_y += slider_spacing
        self.sliders['monster_spawn'] = Slider(slider_x, slider_y, slider_width, UI_SLIDER_HEIGHT, 0.1, 5.0, 1.0, "Enemy Spawn")

        # --- Build Buttons ---
        self.build_buttons = {}
        self.build_button_header_y = slider_y + slider_spacing - 15 # Position header above buttons
        build_y = self.build_button_header_y + 30
        build_x = GAME_AREA_WIDTH + UI_PADDING
        button_size = UI_BUTTON_SIZE
        button_margin = 5 # Space between buttons

        # Create simple icon surface for House button
        house_icon = pygame.Surface((button_size, button_size), pygame.SRCALPHA) # Use SRCALPHA for potential transparency
        house_icon.fill((0,0,0,0)) # Transparent background
        # Draw a simple brown square base
        pygame.draw.rect(house_icon, BROWN_STONE, (button_size * 0.1, button_size * 0.4, button_size * 0.8, button_size * 0.6))
        # Draw a simple red triangle roof
        pygame.draw.polygon(house_icon, DARK_RED, [(0, button_size*0.4), (button_size/2, 0), (button_size, button_size*0.4)])
        pygame.draw.rect(house_icon, BLACK, (0,0,button_size,button_size), 1) # Outline icon

        house_cost_str = ", ".join([f"{amt} {res}" for res, amt in BUILDING_COSTS[BUILDING_HOUSE].items()])
        house_tooltip = f"Build House ({house_cost_str}) +{HOUSE_POP_BONUS} Pop Cap"
        self.build_buttons[BUILDING_HOUSE] = Button(build_x, build_y, button_size, button_size,
                                                    icon_surf=house_icon, tooltip=house_tooltip)

        # Add more buttons here...
        # next_button_x = build_x + button_size + button_margin
        # self.build_buttons[BUILDING_TYPE_2] = Button(next_button_x, build_y, ...)


    def handle_event(self, event):
        """Handles events for all UI elements. Returns data if element handled event."""
        # Check sliders first
        for slider in self.sliders.values():
            if slider.handle_event(event):
                # Return slider value change or just confirmation? For now, just confirm.
                return {'type': 'slider_change'} # Indicate UI handled it

        # Check build buttons
        for building_type, button in self.build_buttons.items():
             if button.handle_event(event):
                 # Return the type of building button clicked
                 return {'type': 'build_button_click', 'building': building_type}

        # Allow clicking anywhere on the panel background? Maybe not needed.
        # if self.panel_rect.collidepoint(event.pos):
        #     return {'type': 'panel_click'} # Generic panel interaction

        return None # Event not handled by the UI


    def draw(self, surface, resources, population, pop_cap):
        """Draws the entire UI panel."""
        # Draw Panel Background
        pygame.draw.rect(surface, DARK_BLUE, self.panel_rect)

        # --- Draw Resource Counts ---
        res_y = UI_PADDING + 5
        res_x = GAME_AREA_WIDTH + UI_PADDING
        for name, amount in resources.items():
            # Skip "Water" if you don't want it displayed, or handle specially
            # if name == 'Water': continue
            text = f"{name}: {int(amount)}"
            res_surf = self.font_resource.render(text, True, WHITE)
            surface.blit(res_surf, (res_x, res_y))
            res_y += 25 # Spacing between resource lines

         # --- Draw Population ---
        pop_text = f"Pop: {population} / {pop_cap}"
        pop_surf = self.font_pop.render(pop_text, True, WHITE)
        # Position population below resources
        surface.blit(pop_surf, (res_x, res_y + 5))

        # --- Draw Sliders ---
        for slider in self.sliders.values():
            slider.draw(surface)

        # --- Draw Build Header ---
        build_header_surf = self.font_header.render("BUILD:", True, WHITE)
        surface.blit(build_header_surf, (res_x, self.build_button_header_y))

        # --- Draw Build Buttons ---
        for button in self.build_buttons.values():
            button.draw(surface)