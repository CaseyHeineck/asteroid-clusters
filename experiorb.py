import math
import pygame
import constants as C
from circleshape import CircleShape

class ExpOrb(CircleShape):
    containers = []
    def __init__(self, x, y, value):
        super().__init__(x, y, C.EXP_ORB_RADIUS, drag=C.EXP_ORB_DRAG)
        self.value = value
        self.lifetime = C.EXP_ORB_LIFETIME
        self.pulse_timer = 0.0

    def update(self, dt):
        self.physics_move(dt)
        self.lifetime -= dt
        self.pulse_timer = (self.pulse_timer + dt) % 1.0
        if self.lifetime <= 0:
            super().kill()
        return 0

    def draw(self, screen):
        pulse = (math.sin(self.pulse_timer * math.pi * 2) + 1) / 2
        inner_r = max(2, int(C.EXP_ORB_RADIUS * (0.6 + 0.4 * pulse)))
        glow_r = max(4, int(C.EXP_ORB_RADIUS * (1.6 + 0.5 * pulse)))
        surf_size = glow_r * 2 + 4
        surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        center = surf_size // 2
        glow_alpha = int(55 + 35 * pulse)
        pygame.draw.circle(surf, (*C.EXP_ORB_COLOR, glow_alpha), (center, center), glow_r)
        pygame.draw.circle(surf, (*C.EXP_ORB_COLOR, 210), (center, center), inner_r)
        highlight_r = max(1, inner_r // 3)
        pygame.draw.circle(surf, (255, 255, 255, 150),
            (center - highlight_r, center - highlight_r), highlight_r)
        screen.blit(surf, surf.get_rect(center=(int(self.position.x), int(self.position.y))))
