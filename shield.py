import pygame
import constants as C
from circleshape import CircleShape

class Shield(CircleShape):
    def __init__(self, owner, radius_offset=10, max_health=C.SHIELD_MAX_HEALTH):
        super().__init__(owner.position.x, owner.position.y, owner.radius + radius_offset)
        self.owner = owner
        self.max_health = max_health
        self.health = max_health
        self.color = C.SHIELD_COLOR
        self.color_alpha = C.SHIELD_COLOR_ALPHA
        self.line_width = C.SHIELD_LINE_WIDTH
        self.damage = C.SHIELD_DAMAGE
        self.hit_flash_timer = 0
        self.hit_flash_duration = 0.05

    def damaged(self, damage):
        self.health = max(0, self.health - damage)
        self.hit_flash_timer = self.hit_flash_duration

    def update(self, dt):
        self.position = self.owner.position.copy()
        if self.hit_flash_timer > 0:
            self.hit_flash_timer = max(0, self.hit_flash_timer - dt)
        if self.health <= 0:
            self.kill()

    def draw(self, screen):
        surface_size = int(self.radius * 2 + 12)
        shield_surface = pygame.Surface((surface_size, surface_size), pygame.SRCALPHA)
        center = surface_size // 2
        pygame.draw.circle(shield_surface, (*self.color, self.color_alpha),
                    (center, center), int(self.radius))
        health_ratio = self.health / self.max_health
        max_ring_alpha = min(255, self.color_alpha + 95)
        ring_alpha = int(self.color_alpha + ((max_ring_alpha - self.color_alpha) * health_ratio))
        pygame.draw.circle(shield_surface, (*self.color, ring_alpha), (center, center),
                    int(self.radius), self.line_width)
        rect = shield_surface.get_rect(center=(self.position.x, self.position.y))
        screen.blit(shield_surface, rect)
        if self.hit_flash_timer > 0:
            pygame.draw.circle(screen, C.WHITE, self.position, int(self.radius),
                    self.line_width + 2)