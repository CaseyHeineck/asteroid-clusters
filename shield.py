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
        self.hit_flash_duration = 0.14

    def damaged(self, damage):
        log_event("shield_hit")
        if damage <= 0:
            return
        absorbed = min(self.health, damage)
        self.health = max(0, self.health - damage)
        self.hit_flash_timer = self.hit_flash_duration
        if absorbed > 0:
            self.owner.game.combat_stats.add_absorbed(C.PLAYER_SHIELD, absorbed)
        if self.health <= 0:
            log_event("shield_destroyed")
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
        padding = self.line_width + 6
        surf_size = int(self.radius) * 2 + padding * 2
        shield_surface = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        center = (surf_size // 2, surf_size // 2)
        health_ratio = self.health / self.max_health if self.max_health > 0 else 0
        fill_color = (*self.color[:3], self.color_alpha)
        pygame.draw.circle(shield_surface, fill_color, center, int(self.radius))
        edge_alpha = int(220 * health_ratio)
        if edge_alpha > 0:
            edge_color = (*self.color[:3], edge_alpha)
            pygame.draw.circle(shield_surface, edge_color, center,
                int(self.radius), self.line_width)
        if self.hit_flash_timer > 0:
            flash_ratio = self.hit_flash_timer / self.hit_flash_duration
            flash_alpha = int(255 * flash_ratio)
            pygame.draw.circle(shield_surface, (255, 255, 255, flash_alpha),
                center, int(self.radius) + 2, self.line_width + 2)
        rect = shield_surface.get_rect(center=(self.position.x, self.position.y))
        screen.blit(shield_surface, rect)