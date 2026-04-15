import math
import pygame
from core import constants as C

class Portal:
    def __init__(self, direction, unlocked=False):
        self.direction = direction
        self.cost = C.PORTAL_ESSENCE_COST
        self.unlocked = unlocked
        self.position = self._edge_position()
        self.pulse_timer = 0.0
        self._prompt_font = None

    def _edge_position(self):
        cx, cy = C.SCREEN_WIDTH / 2, C.SCREEN_HEIGHT / 2
        if self.direction == C.NORTH:
            return pygame.Vector2(cx, 0)
        if self.direction == C.SOUTH:
            return pygame.Vector2(cx, C.SCREEN_HEIGHT)
        if self.direction == C.EAST:
            return pygame.Vector2(C.SCREEN_WIDTH, cy)
        if self.direction == C.WEST:
            return pygame.Vector2(0, cy)

    def arrival_position(self):
        offset = C.PORTAL_ARRIVAL_OFFSET
        cx, cy = C.SCREEN_WIDTH / 2, C.SCREEN_HEIGHT / 2
        if self.direction == C.NORTH:
            return pygame.Vector2(cx, offset)
        if self.direction == C.SOUTH:
            return pygame.Vector2(cx, C.SCREEN_HEIGHT - offset)
        if self.direction == C.EAST:
            return pygame.Vector2(C.SCREEN_WIDTH - offset, cy)
        if self.direction == C.WEST:
            return pygame.Vector2(offset, cy)

    def is_near(self, player_pos):
        return player_pos.distance_to(self.position) <= C.PORTAL_INTERACTION_RADIUS

    def update(self, dt):
        self.pulse_timer = (self.pulse_timer + dt) % 1.0

    def draw(self, screen):
        pulse = (math.sin(self.pulse_timer * math.pi * 2) + 1) / 2
        horizontal = self.direction in (C.NORTH, C.SOUTH)

        if self.unlocked:
            core_color = C.AQUA
            glow_color = C.CYAN
        else:
            core_color = C.BRIGHT_PURPLE
            glow_color = C.VIOLET

        pw = C.PORTAL_WIDTH if horizontal else C.PORTAL_GLOW_DEPTH
        ph = C.PORTAL_GLOW_DEPTH if horizontal else C.PORTAL_WIDTH
        surf_w, surf_h = pw + 40, ph + 40
        surf = pygame.Surface((surf_w, surf_h), pygame.SRCALPHA)
        scx, scy = surf_w // 2, surf_h // 2

        for i in range(4, 0, -1):
            expand = i * 10
            glow_alpha = int((15 + 12 * pulse) * (i / 4))
            gw = pw + expand
            gh = ph + expand
            pygame.draw.rect(surf, (*glow_color, glow_alpha),
                (scx - gw // 2, scy - gh // 2, gw, gh), border_radius=8)

        bar_alpha = int(190 + 55 * pulse)
        pygame.draw.rect(surf, (*core_color, bar_alpha),
            (scx - pw // 2, scy - ph // 2, pw, ph), border_radius=5)

        inner_pw = max(4, pw - 16) if horizontal else max(4, pw - 8)
        inner_ph = max(4, ph - 8) if horizontal else max(4, ph - 16)
        pygame.draw.rect(surf, (255, 255, 255, int(60 + 40 * pulse)),
            (scx - inner_pw // 2, scy - inner_ph // 2, inner_pw, inner_ph),
            border_radius=3)

        screen.blit(surf, surf.get_rect(center=(int(self.position.x), int(self.position.y))))

    def draw_prompt(self, screen, player_pos, can_afford):
        if not self.is_near(player_pos):
            return
        if self._prompt_font is None:
            self._prompt_font = pygame.font.Font(None, 28)

        if self.unlocked:
            text = "[ E ]  ENTER PORTAL"
            color = C.AQUA
        elif can_afford:
            text = f"[ E ]  OPEN  ({self.cost} \u25c6)"
            color = C.BRIGHT_PURPLE
        else:
            text = f"NEED {self.cost} \u25c6 TO OPEN"
            color = C.GRAY

        surf = self._prompt_font.render(text, True, color)
        px, py = int(self.position.x), int(self.position.y)
        padding = 14
        if self.direction == C.NORTH:
            pos = (px - surf.get_width() // 2, py + padding)
        elif self.direction == C.SOUTH:
            pos = (px - surf.get_width() // 2, py - surf.get_height() - padding)
        elif self.direction == C.EAST:
            pos = (px - surf.get_width() - padding, py - surf.get_height() // 2)
        else:
            pos = (px + padding, py - surf.get_height() // 2)
        screen.blit(surf, pos)
