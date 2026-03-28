import pygame
import constants as C
from circleshape import CircleShape

class Shield(CircleShape):
    def __init__(self, player, max_health=C.SHIELD_MAX_HEALTH):
        super().__init__(player.position.x, player.position.y, C.PLAYER_RADIUS)
        self.player = player
        self.health = max_health
        self.color = C.SHIELD_COLOR
        self.color_alpha = C.SHIELD_COLOR_ALPHA
        self.line_width = C.SHIELD_LINE_WIDTH
        self.damage = C.SHIELD_DAMAGE

    def update(self, dt):
        self.position = self.player.position.copy()
        if self.health == 0:
            self.kill()    

    def draw(self, screen):
        surface_size = int(self.radius * 2 + 8)
        shield_surface = pygame.Surface((surface_size, surface_size), pygame.SRCALPHA)
        center = surface_size // 2
        pygame.draw.circle(shield_surface, (*self.color, self.color_alpha), (center, center),
                    int(self.radius), self.line_width)
        rect = shield_surface.get_rect(center=(self.position.x, self.position.y))
        screen.blit(shield_surface, rect)