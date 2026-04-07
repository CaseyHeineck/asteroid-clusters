import math
import random
import pygame
import constants as C


class Shop:
    def __init__(self):
        inset = C.SHOP_EDGE_INSET
        x = random.uniform(inset, C.SCREEN_WIDTH - inset)
        y = random.uniform(inset, C.SCREEN_HEIGHT - inset)
        self.position = pygame.Vector2(x, y)
        self.pulse_timer = 0.0
        self._prompt_font = None

    def is_near(self, player_pos):
        return player_pos.distance_to(self.position) <= C.SHOP_INTERACTION_RADIUS

    def update(self, dt):
        self.pulse_timer = (self.pulse_timer + dt * 0.7) % 1.0

    def draw(self, screen):
        pulse = (math.sin(self.pulse_timer * math.pi * 2) + 1) / 2
        pos = (int(self.position.x), int(self.position.y))
        size = 16

        surf_size = (size + 24) * 2
        surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        c = surf_size // 2

        # Glow rings
        for i in range(4, 0, -1):
            r = size + 4 + i * 5
            alpha = int((12 + 10 * pulse) * (i / 4))
            pygame.draw.circle(surf, (*C.GOLD, alpha), (c, c), r)

        # Diamond body
        diamond = [
            (c, c - size),
            (c + int(size * 0.65), c),
            (c, c + size),
            (c - int(size * 0.65), c),
        ]
        body_alpha = int(210 + 45 * pulse)
        pygame.draw.polygon(surf, (*C.GOLD, body_alpha), diamond)
        pygame.draw.polygon(surf, (*C.WHITE, int(100 + 80 * pulse)), diamond, 2)

        # Inner shine
        shine = [
            (c, c - size // 2),
            (c + int(size * 0.3), c),
            (c, c + size // 4),
            (c - int(size * 0.3), c),
        ]
        pygame.draw.polygon(surf, (*C.WHITE, int(40 + 30 * pulse)), shine)

        screen.blit(surf, surf.get_rect(center=pos))

    def draw_prompt(self, screen, player_pos):
        if not self.is_near(player_pos):
            return
        if self._prompt_font is None:
            self._prompt_font = pygame.font.Font(None, 28)
        text = self._prompt_font.render("[ E ]  MECHANIC'S SHOP", True, C.GOLD)
        px, py = int(self.position.x), int(self.position.y)
        screen.blit(text, (px - text.get_width() // 2, py - 38))
