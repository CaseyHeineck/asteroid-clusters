import pygame
import constants as C
from circleshape import CircleShape
from logger import log_event

class Shield(CircleShape):
    def __init__(self, owner, source, radius_offset=10, max_health=C.SHIELD_MAX_HEALTH):
        super().__init__(owner.position.x, owner.position.y, owner.radius + radius_offset,
            weight=C.SHIELD_WEIGHT, bounciness=C.SHIELD_BOUNCINESS, drag=C.SHIELD_DRAG,
            rotation=0, angular_velocity=0)
        self.owner = owner
        self.source = source
        self.stat_source = source.stat_source
        self.max_health = max_health
        self.health = max_health
        self.color = C.SHIELD_COLOR
        self.color_alpha = C.SHIELD_COLOR_ALPHA
        self.line_width = C.SHIELD_LINE_WIDTH
        self.damage = owner.collision_damage
        self.hit_flash_timer = 0
        self.hit_flash_duration = 0.05

    def damaged(self, damage):
        if damage <= 0:
            return
        absorbed = min(self.health, damage)
        self.health = max(0, self.health - damage)
        self.hit_flash_timer = self.hit_flash_duration
        if absorbed > 0:
            self.owner.game.combat_stats.add_absorbed(C.PLAYER_SHIELD, absorbed)
        if self.health <= 0:
            self.owner.shield = False
            self.kill()

    def block_asteroid(self, asteroid, impact_scale=1.0):
        self.owner.apply_collision_to_asteroid(asteroid, impact_scale)

    def update(self, dt):
        self.position = self.owner.position
        if self.hit_flash_timer > 0:
            self.hit_flash_timer = max(0, self.hit_flash_timer - dt)
        if not self.owner.alive():
            self.kill()

    def draw(self, screen):
        shield_surface = pygame.Surface((self.radius * 2 + 8, self.radius * 2 + 8),
            pygame.SRCALPHA)
        center = (shield_surface.get_width() // 2, shield_surface.get_height() // 2)
        health_ratio = self.health / self.max_health if self.max_health > 0 else 0
        fill_alpha = int(self.color_alpha * health_ratio)
        ring_alpha = max(fill_alpha, 40)
        fill_color = (*self.color[:3], fill_alpha)
        ring_color = (*self.color[:3], ring_alpha)
        pygame.draw.circle(shield_surface, fill_color, center, int(self.radius))
        pygame.draw.circle(shield_surface, ring_color, center, int(self.radius),
            self.line_width)
        if self.hit_flash_timer > 0:
            flash_alpha = int(255 * (self.hit_flash_timer / self.hit_flash_duration))
            flash_color = (255, 255, 255, flash_alpha)
            pygame.draw.circle(shield_surface, flash_color, center, int(self.radius) + 1,
                self.line_width + 1)
        rect = shield_surface.get_rect(center=(self.position.x, self.position.y))
        screen.blit(shield_surface, rect)