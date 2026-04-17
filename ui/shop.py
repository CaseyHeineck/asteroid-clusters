import math
import pygame
import random
from core import constants as C
from core.element import ALL_ELEMENTS

class Shop:
    def __init__(self, wizard_element_counts=None):
        inset = C.SHOP_EDGE_INSET
        x = random.uniform(inset, C.SCREEN_WIDTH - inset)
        y = random.uniform(inset, C.SCREEN_HEIGHT - inset)
        self.position = pygame.Vector2(x, y)
        self.pulse_timer = 0.0
        self._prompt_font = None
        self.wizards = self._generate_wizards(wizard_element_counts or {})
        if wizard_element_counts is not None:
            for elem in self.wizards:
                wizard_element_counts[elem] = wizard_element_counts.get(elem, 0) + 1

    def _generate_wizards(self, global_counts):
        count = random.choices([0, 1, 2, 3, 4, 5], weights=C.WIZARD_COUNT_WEIGHTS)[0]
        max_count = max(global_counts.values(), default=0) if global_counts else 0
        base_weights = [max_count - global_counts.get(e, 0) + 1 for e in ALL_ELEMENTS]
        chosen = []
        remaining = list(ALL_ELEMENTS)
        remaining_weights = list(base_weights)
        for _ in range(min(count, len(remaining))):
            if not remaining:
                break
            elem = random.choices(remaining, weights=remaining_weights)[0]
            idx = remaining.index(elem)
            chosen.append(elem)
            remaining.pop(idx)
            remaining_weights.pop(idx)
        return chosen

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
        for i in range(4, 0, -1):
            r = size + 4 + i * 5
            alpha = int((12 + 10 * pulse) * (i / 4))
            pygame.draw.circle(surf, (*C.GOLD, alpha), (c, c), r)
        diamond = [(c, c - size),
            (c + int(size * 0.65), c),
            (c, c + size),
            (c - int(size * 0.65), c)]
        body_alpha = int(210 + 45 * pulse)
        pygame.draw.polygon(surf, (*C.GOLD, body_alpha), diamond)
        pygame.draw.polygon(surf, (*C.WHITE, int(100 + 80 * pulse)), diamond, 2)
        shine = [(c, c - size // 2),
            (c + int(size * 0.3), c),
            (c, c + size // 4),
            (c - int(size * 0.3), c)]
        pygame.draw.polygon(surf, (*C.WHITE, int(40 + 30 * pulse)), shine)
        screen.blit(surf, surf.get_rect(center=pos))

    def draw_prompt(self, screen, player_pos):
        if not self.is_near(player_pos):
            return
        if self._prompt_font is None:
            self._prompt_font = pygame.font.Font(None, 28)
        text = self._prompt_font.render("[ E ]  SORCEROUS SUNDRIES", True, C.GOLD)
        px, py = int(self.position.x), int(self.position.y)
        screen.blit(text, (px - text.get_width() // 2, py - 38))
