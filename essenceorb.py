import math
import pygame
import constants as C
from circleshape import CircleShape

class EssenceOrb(CircleShape):
    containers = []
    def __init__(self, x, y, value):
        super().__init__(x, y, C.ESSENCE_ORB_RADIUS, drag=C.ESSENCE_ORB_DRAG)
        self.value = value
        self.lifetime = C.ESSENCE_ORB_LIFETIME
        self.pulse_timer = 0.0

    def update(self, dt):
        self.physics_move(dt)
        self.lifetime -= dt
        self.pulse_timer = (self.pulse_timer + dt * 1.3) % 1.0
        if self.lifetime <= 0:
            super().kill()
        return 0

    def draw(self, screen):
        pulse = (math.sin(self.pulse_timer * math.pi * 2) + 1) / 2
        inner_r = max(2, int(C.ESSENCE_ORB_RADIUS * (0.55 + 0.35 * pulse)))
        glow_r = max(4, int(C.ESSENCE_ORB_RADIUS * (1.5 + 0.6 * pulse)))
        surf_size = glow_r * 2 + 4
        surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        center = surf_size // 2
        glow_alpha = int(50 + 40 * pulse)
        pygame.draw.circle(surf, (*C.ESSENCE_ORB_COLOR, glow_alpha), (center, center), glow_r)
        diamond = [
            (center, center - inner_r),
            (center + int(inner_r * 0.65), center),
            (center, center + inner_r),
            (center - int(inner_r * 0.65), center),
        ]
        pygame.draw.polygon(surf, (*C.ESSENCE_ORB_COLOR, 215), diamond)
        pygame.draw.circle(surf, (255, 255, 255, 140),
            (center - max(1, inner_r // 4), center - max(1, inner_r // 4)),
            max(1, inner_r // 3))
        screen.blit(surf, surf.get_rect(center=(int(self.position.x), int(self.position.y))))
